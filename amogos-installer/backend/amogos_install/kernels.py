# Restore the packaged Zen kernel and regenerate initramfs for disk boot.
import shutil

MKINITCPIO_CONFIG = (
    'HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block plymouth filesystems fsck)\n'
    'COMPRESSION="zstd"\n'
    'COMPRESSION_OPTIONS=(-T1 -3)\n'
)


def prepare_kernels(runner, target):
    kernel = target / 'boot/vmlinuz-linux-zen'
    if not kernel.is_file():
        packaged = [
            pkgbase.with_name('vmlinuz')
            for pkgbase in (target / 'usr/lib/modules').glob('*/pkgbase')
            if pkgbase.read_text().strip() == 'linux-zen'
            and pkgbase.with_name('vmlinuz').is_file()
        ]
        if len(packaged) != 1:
            raise RuntimeError('The installed Arch filesystem must contain one Linux Zen kernel.')
        kernel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packaged[0], kernel)
        kernel.chmod(0o644)
    conf = target / 'etc/mkinitcpio.conf.d/10-amogos.conf'
    conf.write_text(MKINITCPIO_CONFIG)
    runner.run(['chroot', str(target), 'mkinitcpio', '-p', 'linux-zen'], timeout=1800)
