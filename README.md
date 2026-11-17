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
Pacman software installation includes pending system upgrades.

The installer includes Plasma for offline setup. It can download GNOME or LXQt
during installation. First boot opens onboarding in a temporary Plasma session.
After creating the account, onboarding removes the temporary account and opens
the chosen desktop or sign-in screen according to the auto-login setting.

The Plymouth assets and wallpapers are packaged with the desktop integration.
See [artwork credits and permissions](ARTWORK-LICENSE.md).
The numbered wallpaper mapping is in
system/rootfs/usr/share/wallpapers/AmogOSArch/ORIGINALS.

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
    python3 -m unittest discover -s amogos-store/backend/tests
    python3 -m unittest discover -s amogos-installer/backend/tests

The store and live installer are Arch ports of the corresponding AmogOS
applications. The restored packaging and original third-party notices are
kept with each component.
