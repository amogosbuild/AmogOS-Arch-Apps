# AmogOS Arch Apps

Linux applications and desktop setup for **AmogOS 2 Pro (Arch)**.

| Component | Application ID | Package |
| --- | --- | --- |
| App Store | amogosarch.appstore | amogos-arch-store |
| Live installer | amogosarch.installer | amogos-arch-installer |
| First-boot setup | amogosarch.onboarding | amogos-arch-onboarding |
| Desktop integration | | amogos-arch-system |

The store uses Pacman for Arch, AmogOS and Chaotic-AUR packages. It supports
Flathub and AppImageHub and keeps their updates separate. Settings enables
direct AUR recipes for the current user. The store displays the PKGBUILD and
checks the reviewed Git commit before makepkg runs as the desktop user.
Pacman software installation includes pending system upgrades. Installed Pacman
and AUR packages offer Uninstall or Full uninstall (-Rns). The review lists
every package Pacman will remove, including unused dependencies. Full uninstall
removes package-owned configuration without creating .pacsave backups and keeps
files in the user's home folder. Shared dependencies and explicitly installed
packages follow Pacman's normal removal rules. The helper checks protected
system packages and revalidates the removal list before running a queued job.

The installer includes Plasma for offline setup. It can download GNOME or LXQt
during installation. First boot opens onboarding in a temporary Plasma session.
After creating the account, onboarding removes the temporary account and opens
the chosen desktop or sign-in screen according to the auto-login setting.

The Plymouth assets and wallpapers are packaged with the desktop integration.
See [artwork credits and permissions](ARTWORK-LICENSE.md).
The numbered wallpaper mapping is in
system/rootfs/usr/share/wallpapers/AmogOSArch/ORIGINALS.

## Plasma memory defaults

The desktop package disables Baloo file indexing, blur, wobbly windows and
Magic Lamp by default, and starts an empty session instead of reopening apps.
Compositing, the AmogOS theme, wallpaper changes, accessibility, audio,
networking and power management remain available.

The same defaults are installed in /etc/xdg and /etc/skel/.config. Existing
Plasma accounts receive a one-time migration on their next sign-in without
changing their color scheme. Later choices to enable indexing or effects are
preserved. Compressed swap uses zstd with a logical size of half of RAM,
capped at 4 GiB, and allocates memory as needed. A local configuration in
/etc/systemd/zram-generator.conf.d can override the vendor defaults.

After upgrading amogos-arch-system to 2.0.0-8, reboot once to activate
compressed swap and the account migration. Idle RAM varies with hardware
and open applications.

## Build the packages

Use Flutter 3.47.6 on an x86_64 Linux host with clang, cmake, ninja, pkgconf and
GTK 3 development libraries. Build each Flutter bundle in amogos-store,
amogos-installer, and onboarding with the corresponding pubspec lock.

    flutter pub get
    flutter build linux --release --no-pub

On Arch, run ./scripts/package.sh as a regular user to package the resulting
bundles. The signed [binary archive](https://amogosbuild.github.io/amogos-arch/)
serves the packages for the
[ArchISO builder](https://github.com/amogosbuild/AmogOS-2.x-Builder/tree/main/amogos-arch).

## Validate the sources

    python3 scripts/check-source.py
    python3 -m unittest discover -s system/tests
    python3 -m unittest discover -s amogos-store/backend/tests
    python3 -m unittest discover -s amogos-installer/backend/tests

The store and live installer are Arch ports of the corresponding AmogOS
applications. The restored packaging and original third-party notices are
kept with each component.
