"""Short-lived, cancellable Zigbee2MQTT learning sessions."""
import asyncio
import json
import logging
from uuid import uuid4
from homeassistant.components import mqtt
from homeassistant.core import callback
from .codec import tuya_to_raw

_LOGGER = logging.getLogger(__name__)


class LearningManager:
    def __init__(self, hub):
        self.hub = hub
        self.sessions = {}

    async def start(self, topic):
        suffix = "/set/ir_code_to_send"
        if not isinstance(topic, str) or not topic.endswith(suffix) or len(topic) > 512 or any(c in topic for c in ("+", "#", "\x00")):
            raise ValueError("Use the full blaster command topic")
        base = topic[:-len(suffix)]
        if not base:
            raise ValueError("Missing blaster topic")
        if topic in self.hub.tx_locks and self.hub.tx_locks[topic].locked():
            raise ValueError("The blaster is sending. Wait for it to finish before learning")
        if any(s["topic"] == topic and s["status"] == "waiting" for s in self.sessions.values()):
            raise ValueError("This blaster is already learning")
        # Bound retained results as well as active sessions.
        for key in list(self.sessions):
            if self.sessions[key]["status"] != "waiting":
                del self.sessions[key]
        if len(self.sessions) >= 8:
            raise ValueError("Too many active learning sessions")
        token = uuid4().hex
        session = {"topic": topic, "status": "waiting"}
        self.sessions[token] = session
        future = asyncio.get_running_loop().create_future()

        @callback
        def received(message):
            if message.retain or future.done():
                return
            try:
                value = json.loads(message.payload).get("learned_ir_code")
                if not value:
                    return
                tuya_to_raw(value)
            except (ValueError, TypeError, AttributeError):
                return
            future.set_result(value)

        async def run():
            unsubscribe = None
            try:
                unsubscribe = await mqtt.async_subscribe(self.hub.hass, base, received, qos=0)
                await mqtt.async_publish(self.hub.hass, base + "/set", json.dumps({"learn_ir_code": "ON"}), qos=0, retain=False)
                session["code"] = await asyncio.wait_for(future, 30)
                session["status"] = "learned"
            except TimeoutError:
                session["status"] = "timeout"
            except asyncio.CancelledError:
                session["status"] = "cancelled"
                raise
            except Exception as err:
                _LOGGER.exception("IR learning failed for %s", base)
                session.update(status="error", error=str(err))
            finally:
                if unsubscribe:
                    unsubscribe()
                # Z2M's learn action starts a timed hardware window; OFF is
                # not sent because some converter versions treat it as start.

        session["task"] = self.hub.hass.async_create_task(run())
        return {"session": token}

    def status(self, token):
        if token not in self.sessions:
            raise ValueError("Learning session expired")
        return {k: v for k, v in self.sessions[token].items() if k not in ("task", "topic")}

    async def cancel(self, token):
        session = self.sessions.get(token)
        if session and not session["task"].done():
            session["task"].cancel()
            await asyncio.gather(session["task"], return_exceptions=True)
            session["status"] = "cancelled"

    async def close(self):
        for token in list(self.sessions):
            await self.cancel(token)
