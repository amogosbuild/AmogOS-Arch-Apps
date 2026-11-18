# Apply native AmogOS window frames while preserving bindings and later theme choices.
import pathlib
import xml.etree.ElementTree as ET

NS = 'http://openbox.org/3.4/rc'
ET.register_namespace('', NS)
STOCK = {'Clearlooks', 'Default', 'Onyx', 'Onyx-Citrus', 'Adwaita', 'Artwiz-boxed',
         'Bear2', 'Clearlooks-3.4', 'Clearlooks-Olive', 'Mikachu', 'Natura', 'Orang', 'Syscrash'}


def element(parent, name):
    child = parent.find(f'{{{NS}}}{name}')
    return child if child is not None else ET.SubElement(parent, f'{{{NS}}}{name}')


def apply_openbox_theme(config, dark, defaults=pathlib.Path('/usr/share/amogos-arch/lxqt/openbox-rc.xml')):
    path = config / 'openbox/rc.xml'
    marker = config / 'amogos-arch/openbox-decoration-v1'
    try:
        tree = ET.parse(path if path.exists() else defaults,
                        parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
        root = tree.getroot()
        if root.tag != f'{{{NS}}}openbox_config':
            return False
        theme = element(root, 'theme')
        name = element(theme, 'name')
        current = name.text or 'Clearlooks'
        owned = current in ('AmogOS-Arch-Dark', 'AmogOS-Arch-Light')
        if not owned and (marker.exists() or current not in STOCK):
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()
            return True
        chosen = 'AmogOS-Arch-Dark' if dark else 'AmogOS-Arch-Light'
        if name.text != chosen or not marker.exists():
            name.text = chosen
            if not marker.exists():
                element(theme, 'titleLayout').text = 'NLIMC'
                element(theme, 'animateIconify').text = 'no'
                for place in ('ActiveWindow', 'InactiveWindow', 'MenuHeader', 'MenuItem', 'OnScreenDisplay'):
                    font = theme.find(f'{{{NS}}}font[@place="{place}"]')
                    if font is None:
                        font = ET.SubElement(theme, f'{{{NS}}}font', place=place)
                    for key, value in {'name': 'Noto Sans', 'size': '11' if 'Window' in place else '10',
                                       'weight': 'bold' if place == 'ActiveWindow' else 'normal', 'slant': 'normal'}.items():
                        element(font, key).text = value
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + '.amogos-new')
            tree.write(temporary, encoding='UTF-8', xml_declaration=True)
            temporary.replace(path)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        return True
    except (OSError, ET.ParseError):
        return False
