import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('commands',Path(__file__).resolve().parents[1]/'custom_components/tuya_ir_bridge/commands.py')
commands=importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


class CommandTests(unittest.TestCase):
    def test_tasmota_boolean_and_key_forms(self):
        self.assertEqual(commands.normalize_hvac({'power':'On','quiet':'Off','temp':24}), {'Power':True,'Quiet':False,'Temp':24})

    def test_unknown_and_duplicate_fields(self):
        for command in ({'Power':True,'power':False},{'bogus':1},{'Power':'not-a-boolean'}):
            with self.assertRaises(ValueError): commands.normalize_hvac(command)
