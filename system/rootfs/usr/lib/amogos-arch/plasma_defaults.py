# Apply lightweight Plasma defaults once per account without changing the chosen theme.
from subprocess import TimeoutExpired

DEFAULTS = (
    ("baloofilerc", "Basic Settings", "Indexing-Enabled", "false"),
    ("kwinrc", "Plugins", "blurEnabled", "false"),
    ("kwinrc", "Plugins", "wobblywindowsEnabled", "false"),
    ("kwinrc", "Plugins", "magiclampEnabled", "false"),
    ("ksmserverrc", "General", "loginMode", "emptySession"),
)


def apply_plasma_defaults(config, run):
    marker = config / "amogos-arch/plasma-performance-v1"
    if marker.exists():
        return True
    for filename, group, key, value in DEFAULTS:
        try:
            if not run("kwriteconfig6", "--file", str(config / filename),
                       "--group", group, "--key", key, value):
                return False
        except (OSError, TimeoutExpired):
            return False
    try:
        run("balooctl6", "disable")
    except (OSError, TimeoutExpired):
        pass
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    return True
