# Verify frame migration preserves bindings, later customizations and invalid user files.
import pathlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'rootfs/usr/lib/amogos-arch'))
from openbox_defaults import apply_openbox_theme, NS
DEFAULTS = pathlib.Path(__file__).resolve().parents[1] / 'rootfs/usr/share/amogos-arch/lxqt/openbox-rc.xml'
Q = {'o': NS}


class OpenboxDefaultsTest(unittest.TestCase):
    def test_new_profile_has_bindings_and_light_variant(self):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory)
            self.assertTrue(apply_openbox_theme(config, False, DEFAULTS))
            root = ET.parse(config / 'openbox/rc.xml').getroot()
            self.assertEqual(root.findtext('o:theme/o:name', namespaces=Q), 'AmogOS-Arch-Light')
            self.assertGreater(len(root.findall('o:keyboard/o:keybind', Q)), 10)
            self.assertTrue(root.findall('o:mouse/o:context', Q))

    def test_migration_keeps_bindings_and_later_font_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory)
            path = config / 'openbox/rc.xml'
            path.parent.mkdir()
            path.write_text(f'<openbox_config xmlns="{NS}"><theme><name>Clearlooks</name></theme>'
                            '<keyboard><keybind key="W-e"><action name="Execute"><command>my-files</command>'
                            '</action></keybind></keyboard></openbox_config>')
            self.assertTrue(apply_openbox_theme(config, True, DEFAULTS))
            tree = ET.parse(path)
            self.assertEqual(tree.findtext('.//o:command', namespaces=Q), 'my-files')
            tree.find('o:theme/o:font[@place="ActiveWindow"]/o:size', Q).text = '16'
            tree.write(path)
            self.assertTrue(apply_openbox_theme(config, False, DEFAULTS))
            tree = ET.parse(path)
            self.assertEqual(tree.findtext('o:theme/o:font[@place="ActiveWindow"]/o:size', namespaces=Q), '16')
            self.assertEqual(tree.findtext('o:theme/o:name', namespaces=Q), 'AmogOS-Arch-Light')

    def test_custom_theme_and_later_stock_choice_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory)
            path = config / 'openbox/rc.xml'
            path.parent.mkdir()
            original = f'<openbox_config xmlns="{NS}"><theme><name>Personal</name></theme></openbox_config>'
            path.write_text(original)
            self.assertTrue(apply_openbox_theme(config, True, DEFAULTS))
            self.assertEqual(path.read_text(), original)
            path.write_text(original.replace('Personal', 'Clearlooks'))
            self.assertTrue(apply_openbox_theme(config, True, DEFAULTS))
            self.assertEqual(ET.parse(path).findtext('o:theme/o:name', namespaces=Q), 'Clearlooks')

    def test_invalid_xml_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory)
            path = config / 'openbox/rc.xml'
            path.parent.mkdir()
            path.write_text('<unfinished')
            self.assertFalse(apply_openbox_theme(config, True, DEFAULTS))
            self.assertEqual(path.read_text(), '<unfinished')
            self.assertFalse((config / 'amogos-arch/openbox-decoration-v1').exists())


if __name__ == '__main__':
    unittest.main()
