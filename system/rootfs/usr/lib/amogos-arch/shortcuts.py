# Install and trust desktop shortcuts whose contents match the packaged launchers.
from pathlib import Path
import shutil
import subprocess

APPLICATIONS = (
    'amogosarch.appstore.desktop',
    'amogos.music.desktop',
    'amogos.notes.desktop',
    'amogosarch.installer.desktop',
    'steam.desktop',
    'FREE ROBUX.desktop',
    'amogosarch.steam-big-picture.desktop',
)


def desktop_folder():
    home = Path.home()
    if shutil.which('xdg-user-dir'):
        value = subprocess.run(
            ['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True, check=False,
        ).stdout.strip()
        if value and Path(value).is_absolute() and Path(value) != home:
            return Path(value)
    return home / 'Desktop'


def seed_desktop_shortcuts(trust_attribute):
    desktop = desktop_folder()
    desktop.mkdir(parents=True, exist_ok=True)
    for filename in APPLICATIONS:
        bundled = Path('/usr/share/applications') / filename
        if not bundled.is_file():
            continue
        skeleton = Path('/etc/skel/Desktop') / filename
        source = skeleton if skeleton.is_file() else bundled
        target = desktop / filename
        if target.is_symlink():
            continue
        try:
            content = source.read_bytes()
            if not target.exists():
                with target.open('xb') as shortcut:
                    shortcut.write(content)
            if not target.is_file() or target.read_bytes() not in (content, bundled.read_bytes()):
                continue
            target.chmod(0o755)
            if trust_attribute and shutil.which('gio'):
                subprocess.run(
                    ['gio', 'set', str(target), trust_attribute, 'true'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                    timeout=5,
                )
        except (OSError, subprocess.TimeoutExpired):
            continue
