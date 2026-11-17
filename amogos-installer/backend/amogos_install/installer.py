# Installation applies a reviewed plan only in live media and confines configuration to the mounted target.
import pathlib
import os
import re
import shutil
import tempfile
from .desktops import DESKTOPS, check_network
from .kernels import prepare_kernels
from .planner import MIB, fingerprint
from .runtime import InstallError, Runner, log_directory, private_mounts, require_live
from .storage import disk_by_path, read_table, shrink_limit
from .bootloaders import Bootloader

def validate_settings(request):
    locale = request.get("locale")
    if not isinstance(locale, str) or not re.fullmatch(r"[a-z]{2}_[A-Z]{2}\.UTF-8", locale):
        raise InstallError("Select a supported system language.")
    available = pathlib.Path("/etc/locale.gen").read_text().splitlines()
    if not any(line.lstrip("# ").split() == [locale, "UTF-8"] for line in available):
        raise InstallError("This system language is unavailable.")
    timezone = request.get("timezone")
    zones = pathlib.Path("/usr/share/zoneinfo")
    if not isinstance(timezone, str) or not (zones / timezone).resolve().is_relative_to(zones) or not (zones / timezone).is_file():
        raise InstallError("Select an available time zone.")
    keyboard = request.get("keyboard")
    if not isinstance(keyboard, str) or not re.fullmatch(r"[a-z]{2}", keyboard) or not pathlib.Path("/usr/share/X11/xkb/symbols", keyboard).is_file():
        raise InstallError("Select an available keyboard layout.")


class Installer:
    def __init__(self, plan, request, reporter):
        self.plan, self.request, self.report = plan, request, reporter
        self.runner = Runner()
        self.mounts = []
        self.target = None

    def run(self):
        medium = require_live(self.runner)
        validate_settings(self.request)
        check_network(self.plan["desktop"], self.plan["upgrade"])
        if self.request.get("confirmation") != self.plan.get("confirmation", self.plan["disk"].split("/")[-1]):
            raise InstallError("The drive confirmation does not match the reviewed plan.")
        disk = disk_by_path(self.runner, self.plan["disk"], inspect=False)
        if fingerprint(disk) != self.plan["fingerprint"]:
            raise InstallError("The drive layout changed after review. Scan the drives and review a new plan.")
        self._validate_boot_targets()
        for step in self.plan["steps"]:
            if step["action"] == "shrink":
                partition = next(p for p in disk["partitions"] if p["path"] == step["path"])
                minimum, reason = shrink_limit(self.runner, partition)
                if reason or minimum is None or minimum > step["size"]:
                    raise InstallError("The filesystem is no longer eligible for the reviewed resize.")
        secure = next(pathlib.Path("/sys/firmware/efi/efivars").glob("SecureBoot-*"), None)
        if secure and len(secure.read_bytes()) > 4 and secure.read_bytes()[4] == 1:
            raise InstallError("This development image does not include a signed Secure Boot chain.")
        folder = log_directory()
        self.runner.log = (folder / "installation.log").open("w", buffering=1)
        (folder / "partition-table.before").write_text(self.runner.run(["sfdisk", "--dump", disk["path"]], check=False).stdout)
        self.report.emit("prepare", .02, "Checking the live system and reviewed layout")
        try:
            private_mounts(self.runner)
            self.target = pathlib.Path(tempfile.mkdtemp(prefix="amogos-target-", dir="/run"))
            self._partitions(disk)
            self._mount(self.plan["root"], self.target)
            self._copy(medium)
            self._validate_boot_targets()
            if self.plan["esp"]:
                (self.target / "boot/efi").mkdir(parents=True, exist_ok=True)
                self._mount(self.plan["esp"], self.target / "boot/efi")
            self._runtime()
            self._configure()
            self._packages()
            self._boot(medium)
            self.report.emit("finish", .98, "Syncing your new system to disk")
            self.runner.run(["sync"], timeout=180)
        finally:
            self.runner.log.flush()
            if self.target and (self.target / "etc/os-release").exists():
                try:
                    shutil.copytree(folder, self.target / "var/log/amogos-arch-installer" / folder.name, dirs_exist_ok=True)
                except OSError:
                    pass
            for path in reversed(self.mounts):
                self.runner.run(["umount", "-R", str(path)], check=False, timeout=90)
            if self.target:
                try:
                    self.target.rmdir()
                except OSError:
                    pass
            self.runner.log.close()
        self.report.emit("complete", 1, "AmogOS 2 Pro (Arch) is installed. Welcome home.", done=True)

    def _validate_boot_targets(self):
        for item in self.plan.get("bootTargets", []):
            selected = disk_by_path(self.runner, item["path"], inspect=False)
            if fingerprint(selected) != item["fingerprint"]:
                raise InstallError("The custom boot disk changed after review. Review a new installation plan.")

    def _partitions(self, disk):
        r = self.runner
        self.report.emit("partition", .07, "Preparing the partitions you reviewed")
        for step in self.plan["steps"]:
            action = step["action"]
            if action == "label":
                r.run(["wipefs", "--all", "--force", self.plan["disk"]])
                r.run(["parted", "--script", self.plan["disk"], "mklabel", "gpt"])
            elif action == "shrink":
                size = step["size"] - MIB
                if step["fs"] == "ntfs":
                    r.run(["ntfsresize", "--no-action", "--size", str(size), step["path"]], timeout=900)
                    r.run(["ntfsresize", "--size", str(size), step["path"]], input="y\n", timeout=1800)
                    self.report.emit("partition", .1, "Windows will check its resized filesystem at the next boot. Let that check complete.", warning=True)
                elif step["fs"] == "ext4":
                    r.run(["e2fsck", "-f", "-p", step["path"]], allowed=(0, 1), timeout=1800)
                    r.run(["resize2fs", step["path"], f"{size // 1024}K"], timeout=1800)
                else:
                    raise InstallError("This filesystem cannot be resized by the installer.")
                r.run(["sfdisk", "--lock=yes", "--wipe", "never", "--wipe-partitions", "never", "-N", str(step["number"]), self.plan["disk"]], input=f"size={step['size'] // disk['sectorSize']}\n")
            elif action == "create":
                args = ["parted", "--script", "--align", "optimal", self.plan["disk"], "unit", "B", "mkpart", "AmogOS-" + step["role"] if self.plan["table"] == "gpt" else "primary"]
                if step["fs"]:
                    args.append(step["fs"])
                r.run(args + [str(step["start"]) + "B", str(step["start"] + step["size"] - 1) + "B"])
                table = read_table(r, self.plan["disk"])
                created = next((p for p in table.get("partitions", []) if p["start"] * table.get("sectorsize", 512) == step["start"]), None)
                if not created or created["node"] != self._path(step["number"]):
                    raise InstallError("The created partition does not match the reviewed partition plan.")
                if step["role"] in ("esp", "bios"):
                    r.run(["parted", "--script", self.plan["disk"], "set", str(step["number"]), "esp" if step["role"] == "esp" else "bios_grub", "on"])
            elif action == "format":
                r.run(["partprobe", self.plan["disk"]])
                r.run(["udevadm", "settle"], timeout=60)
                if step["fs"] == "ext4":
                    r.run(["mkfs.ext4", "-F", "-L", "AmogOS", step["path"]], timeout=600)
                else:
                    r.run(["mkfs.fat", "-F", "32", "-n", "AMOGOS_EFI", step["path"]])
        r.run(["partprobe", self.plan["disk"]])
        r.run(["udevadm", "settle"], timeout=60)

    def _path(self, number):
        disk = self.plan["disk"]
        return f"{disk}{'p' if disk[-1].isdigit() else ''}{number}"

    def _mount(self, source, target, options=None):
        target = pathlib.Path(target)
        target.mkdir(parents=True, exist_ok=True)
        self.runner.run(["mount", *([] if options is None else ["-o", options]), str(source), str(target)])
        self.mounts.append(target)

    def _copy(self, medium):
        self.report.emit("copy", .17, "Unpacking your AmogOS 2 Pro (Arch) system")
        def progress(line):
            percent = re.search(r"(\d+)%", line)
            if percent:
                self.report.emit("copy", .17 + .45 * int(percent.group(1)) / 100, "Copying AmogOS 2 Pro (Arch)")
        self.runner.stream(["nice", "-n", "10", "unsquashfs", "-force", "-processors", "1", "-data-queue", "8", "-frag-queue", "8", "-percentage", "-d", str(self.target), str(medium / "amogos/x86_64/airootfs.sfs")], progress)
        descriptor=os.open(self.target,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            os.fchown(descriptor,0,0)
            os.fchmod(descriptor,0o755)
        finally:
            os.close(descriptor)
        self.report.emit("copy", .63, "Your system files are in place")

    def _runtime(self):
        for name in ("dev", "proc", "sys"):
            destination = self.target / name
            destination.mkdir(exist_ok=True)
            self.runner.run(["mount", "--rbind", "/" + name, str(destination)])
            self.runner.run(["mount", "--make-rslave", str(destination)])
            self.mounts.append(destination)
        (self.target / "run").mkdir(exist_ok=True)
        self.runner.run(["mount", "-t", "tmpfs", "-o", "mode=755,nosuid,nodev", "tmpfs", str(self.target / "run")])
        self.mounts.append(self.target / "run")
        (self.target / "run/amogos-install-target").touch()
        resolver = self.target / "etc/resolv.conf"
        if resolver.is_symlink():
            resolver.unlink()
        resolver.write_text(pathlib.Path("/etc/resolv.conf").read_text())

    def chroot(self, args, **kwargs):
        return self.runner.run(["chroot", str(self.target), *args], **kwargs)

    def write(self, name, text):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def _uuid(self, device):
        value = self.runner.run(["blkid", "-s", "UUID", "-o", "value", device]).stdout.strip()
        if not re.fullmatch(r"[A-Za-z0-9-]+", value):
            raise InstallError("The installed filesystem has no valid UUID.")
        return value

    def _configure(self):
        self.report.emit("configure", .66, "Making AmogOS 2 Pro (Arch) yours")
        for name in (
            "etc/systemd/system/multi-user.target.wants/amogos-arch-live.service",
            "etc/sddm.conf.d/20-amogos-live.conf",
            "etc/mkinitcpio.conf.d/archiso.conf",
            "etc/pacman.d/hooks/00-amogos-archiso-only.hook",
            "etc/skel/Desktop/amogosarch.installer.desktop",
        ):
            (self.target / name).unlink(missing_ok=True)
        self.write("etc/hostname", "amogos-arch\n")
        self.write("etc/locale.conf", "LANG=" + self.request["locale"] + "\n")
        locale_file=self.target / "etc/locale.gen"
        locale = self.request["locale"] + " UTF-8"
        contents=locale_file.read_text().splitlines()
        locale_file.write_text("\n".join(locale if line.lstrip("# ") == locale else line for line in contents) + "\n")
        self.chroot(["locale-gen"],timeout=300)
        localtime=self.target/"etc/localtime"
        localtime.unlink(missing_ok=True)
        localtime.symlink_to("/usr/share/zoneinfo/" + self.request["timezone"])
        self.write("etc/X11/xorg.conf.d/00-keyboard.conf", '# Keyboard layout chosen in the installer.\nSection "InputClass"\n    Identifier "system-keyboard"\n    MatchIsKeyboard "on"\n    Option "XkbLayout" "'+self.request["keyboard"]+'"\nEndSection\n')
        self.write("etc/vconsole.conf", "KEYMAP=" + ("uk" if self.request["keyboard"] == "gb" else self.request["keyboard"]) + "\n")
        fstab = "UUID=" + self._uuid(self.plan["root"]) + " / ext4 defaults,errors=remount-ro 0 1\n"
        if self.plan["esp"]:
            fstab += "UUID=" + self._uuid(self.plan["esp"]) + " /boot/efi vfat umask=0077 0 2\n"
        self.write("etc/fstab",fstab)
        machine=self.target/"etc/machine-id"
        machine.unlink(missing_ok=True)
        machine.touch()
        self.chroot(["passwd","--lock","root"])
        self.chroot(["pacman-key","--init"],timeout=300)
        self.chroot(["pacman-key","--populate","archlinux","chaotic","amogos-arch"],timeout=300)
        self.chroot(["/usr/lib/amogos-arch-onboarding/prepare", self.plan["desktop"]],timeout=120)

    def _packages(self):
        desktop_packages=DESKTOPS[self.plan["desktop"]]
        if self.plan["upgrade"] or desktop_packages:
            self.report.emit("packages",.72,"Updating Arch packages from the network")
            self.runner.stream(["chroot",str(self.target),"pacman","-Syu","--noconfirm","--needed",*desktop_packages],lambda line: self.report.emit("packages",.77,line))
        self.chroot(["pacman","-Dk"],timeout=180)
        self.report.emit("drivers",.83,"Zen kernel and included firmware are ready")

    def _boot(self, medium):
        self.report.emit("bootloader", .88, "Creating your boot menu")
        prepare_kernels(self.runner, self.target, medium)
        if self.plan.get("bootTargets") and not self.plan["esp"]:
            self._validate_boot_targets()
        Bootloader(self.runner, self.target, self.plan, self.report).install()
        self.report.emit("bootloader", .96, "Your boot setup is ready")
        self.chroot(["pacman","-R","--noconfirm","amogos-arch-installer"],timeout=120)
        (self.target / "etc/resolv.conf").unlink(missing_ok=True)
        (self.target / "etc/resolv.conf").symlink_to("/run/NetworkManager/resolv.conf")
