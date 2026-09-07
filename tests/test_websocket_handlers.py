"""Exercise actual handler bodies without installing Home Assistant.

Imports/decorators are omitted; this covers handler logic, not HA registration.
The connection double deliberately exposes only HA's user/send methods.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock


class Unauthorized(Exception):
    pass


def handlers():
    source = Path(__file__).resolve().parents[1] / 'custom_components/tuya_ir_bridge/websocket_api.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    tree.body = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)]
    for node in tree.body:
        node.decorator_list = []
    namespace = {'DOMAIN': 'tuya_ir_bridge', 'Unauthorized': Unauthorized}
    exec(compile(tree, str(source), 'exec'), namespace)
    return namespace


class WebsocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_list_and_create(self):
        api = handlers()
        device = {'name': 'Bedroom'}
        hub = SimpleNamespace(devices=[device], create=AsyncMock(return_value=device))
        hass = SimpleNamespace(data={'tuya_ir_bridge': hub})
        connection = SimpleNamespace(user=SimpleNamespace(is_admin=True), send_result=Mock(), send_error=Mock())
        await api['list_devices'](hass, connection, {'id': 1})
        connection.send_result.assert_called_once_with(1, [device])
        await api['create_device'](hass, connection, {'id': 2, 'device': device})
        hub.create.assert_awaited_once_with(device)
        connection.send_result.assert_called_with(2, device)

    async def test_non_admin_rejected_before_access(self):
        api = handlers()
        for user in (None, SimpleNamespace(is_admin=False)):
            for name in ('list_devices', 'create_device', 'catalogue'):
                with self.assertRaises(Unauthorized):
                    await api[name](SimpleNamespace(data={}), SimpleNamespace(user=user), {'id': 1})

    async def test_not_loaded_and_invalid_device(self):
        api = handlers()
        connection = SimpleNamespace(user=SimpleNamespace(is_admin=True), send_error=Mock())
        await api['list_devices'](SimpleNamespace(data={}), connection, {'id': 1})
        self.assertEqual(connection.send_error.call_args.args[1], 'not_loaded')
        hub = SimpleNamespace(create=AsyncMock(side_effect=ValueError('Invalid protocol')))
        await api['create_device'](SimpleNamespace(data={'tuya_ir_bridge': hub}), connection, {'id': 2, 'device': {}})
        connection.send_error.assert_called_with(2, 'invalid_device', 'Invalid protocol')
