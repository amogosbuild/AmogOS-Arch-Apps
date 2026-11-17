// Center the pinned and running applications between the launcher and status area.
if (panels().length === 0) {
    var panel = new Panel;
    panel.location = "bottom";
    panel.height = 48;
    var menu = panel.addWidget("org.kde.plasma.kickoff");
    menu.currentConfigGroup = ["General"];
    menu.writeConfig("icon", "/usr/share/pixmaps/amogos-menu.png");
    menu.writeConfig("menuLabel", "AmogOS Arch");
    menu.writeConfig("showText", true);
    panel.addWidget("org.kde.plasma.panelspacer");
    var tasks = panel.addWidget("org.kde.plasma.icontasks");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", "applications:org.kde.dolphin.desktop,applications:firefox.desktop,applications:amogosarch.appstore.desktop,applications:steam.desktop,applications:amogosarch.steam-big-picture.desktop");
    panel.addWidget("org.kde.plasma.panelspacer");
    panel.addWidget("org.kde.plasma.systemtray");
    panel.addWidget("org.kde.plasma.digitalclock");
}
var workspaces = desktopsForActivity(currentActivity());
for (var i = 0; i < workspaces.length; ++i) {
    workspaces[i].wallpaperPlugin = "org.kde.image";
    workspaces[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    workspaces[i].writeConfig("Image", "file:///usr/share/wallpapers/AmogOSArch/5.png");
}
