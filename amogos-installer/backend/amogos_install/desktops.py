# KDE is supplied offline, and the alternative desktops are installed with a full Pacman upgrade.
from .runtime import InstallError
from .storage import online

DESKTOPS={
    'plasma': [],
    'gnome': [
        'gnome-shell','gnome-session','gdm','nautilus','gnome-control-center','gnome-terminal',
        'gnome-keyring','xdg-desktop-portal-gnome',
        'chaotic-aur/gnome-shell-extension-dash-to-dock',
    ],
    'lxqt': [
        'lxqt-session','lxqt-panel','lxqt-config','lxqt-globalkeys','lxqt-notificationd',
        'lxqt-policykit','lxqt-powermanagement','lxqt-qtplugin','lxqt-themes',
        'pcmanfm-qt','qterminal','openbox','plank','picom','xdg-desktop-portal-lxqt',
    ],
}
LABELS={'plasma':'KDE Plasma','gnome':'GNOME','lxqt':'LXQt'}


def selection(request):
    desktop=request.get('desktop','plasma')
    if not isinstance(desktop,str) or desktop not in DESKTOPS:
        raise InstallError('Choose KDE Plasma, GNOME or LXQt.')
    return desktop


def check_network(desktop, upgrade):
    if (desktop!='plasma' or upgrade) and not online():
        raise InstallError('Connect to the internet for desktop downloads or online updates. KDE Plasma is available offline.')
