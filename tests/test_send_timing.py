"""Verify MQTT sends return promptly while preserving per-blaster spacing."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock


def send_method():
    source = Path(__file__).resolve().parents[1] / "custom_components/tuya_ir_bridge/hub.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    hub = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Hub")
    method = next(node for node in hub.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "send")
    sleep = AsyncMock()
    async_api = SimpleNamespace(
        Lock=asyncio.Lock,
        get_running_loop=asyncio.get_running_loop,
        sleep=sleep,
    )
    mqtt = SimpleNamespace(async_publish=AsyncMock())
    namespace = {
        "asyncio": async_api,
        "mqtt": mqtt,
        "prepare_signal": lambda signal, transport: ("payload", signal["duration"]),
    }
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    exec(compile(module, str(source), "exec"), namespace)
    return namespace["send"], sleep, mqtt.async_publish


class SendTimingTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_send_is_immediate_and_second_same_topic_waits(self):
        send, sleep, publish = send_method()
        sender = SimpleNamespace(
            deleted=set(),
            tx_locks={},
            tx_ready={},
            learning=SimpleNamespace(sessions={}),
            hass=object(),
        )
        device = {"id": "one", "topic": "zigbee/one", "transport": "base64", "mqtt_delay": 0}

        await send(sender, device, {"duration": 0.1})
        sleep.assert_not_awaited()

        await send(sender, device, {"duration": 0.1})
        self.assertEqual(sleep.await_count, 1)
        self.assertGreater(sleep.await_args.args[0], 0.45)
        self.assertEqual(publish.await_count, 2)

    async def test_different_blasters_do_not_share_cooldown(self):
        send, sleep, publish = send_method()
        sender = SimpleNamespace(
            deleted=set(),
            tx_locks={},
            tx_ready={},
            learning=SimpleNamespace(sessions={}),
            hass=object(),
        )

        await send(sender, {"id": "one", "topic": "zigbee/one"}, {"duration": 0.1})
        await send(sender, {"id": "two", "topic": "zigbee/two"}, {"duration": 0.1})

        sleep.assert_not_awaited()
        self.assertEqual(publish.await_count, 2)


if __name__ == "__main__":
    unittest.main()
