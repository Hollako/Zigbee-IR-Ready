"""Exercise MQTT availability payload parsing without importing Home Assistant."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


def climate_methods():
    source = Path(__file__).resolve().parents[1] / "custom_components/tuya_ir_bridge/climate.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    climate = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "IRClimate")
    wanted = {"_availability_message", "available"}
    methods = [node for node in climate.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted]
    for method in methods:
        method.decorator_list = []
    namespace = {"json": json}
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), str(source), "exec"), namespace)
    return namespace


class AvailabilityTests(unittest.TestCase):
    def test_plain_and_json_payloads(self):
        methods = climate_methods()
        entity = SimpleNamespace(
            device={"availability_topic": "zigbee/device/availability"},
            _mqtt_available=None,
            async_write_ha_state=Mock(),
        )

        methods["_availability_message"](entity, SimpleNamespace(payload="online"))
        self.assertTrue(methods["available"](entity))
        methods["_availability_message"](entity, SimpleNamespace(payload='{"state":"offline"}'))
        self.assertFalse(methods["available"](entity))
        methods["_availability_message"](entity, SimpleNamespace(payload='{"availability":"online"}'))
        self.assertTrue(methods["available"](entity))
        self.assertEqual(entity.async_write_ha_state.call_count, 3)

    def test_unknown_payload_does_not_replace_last_state(self):
        methods = climate_methods()
        entity = SimpleNamespace(
            device={"availability_topic": "zigbee/device/availability"},
            _mqtt_available=True,
            async_write_ha_state=Mock(),
        )

        methods["_availability_message"](entity, SimpleNamespace(payload='{"battery":90}'))
        self.assertTrue(entity._mqtt_available)
        entity.async_write_ha_state.assert_not_called()


if __name__ == "__main__":
    unittest.main()
