# Copy the preinstalled app launchers to each desktop without replacing user files.
from pathlib import Path
import shutil
import subprocess

APPLICATIONS = (
    'amogosarch.appstore.desktop',
    'amogos.music.desktop',
    'amogos.notes.desktop',
)


def seed_desktop_shortcuts(should_trust):
    desktop = Path.home() / 'Desktop'
    if shutil.which('xdg-user-dir'):
        destination = subprocess.run(
            ['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True, check=False,
        ).stdout.strip()
        if destination and Path(destination).is_absolute() and Path(destination) != Path.home():
            desktop = Path(destination)
    applications = Path('/usr/share/applications')
    desktop.mkdir(parents=True, exist_ok=True)
    for filename in APPLICATIONS:
        source = applications / filename
        target = desktop / filename
        if not source.is_file() or target.exists() or target.is_symlink():
            continue
        try:
            with source.open('rb') as original, target.open('xb') as shortcut:
                shutil.copyfileobj(original, shortcut)
            target.chmod(0o755)
            if should_trust and shutil.which('gio'):
                subprocess.run(
                    ['gio', 'set', str(target), 'metadata::trusted', 'true'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                    timeout=5,
                )
        except (OSError, subprocess.TimeoutExpired):
            continue
