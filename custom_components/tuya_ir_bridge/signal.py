"""Preserve native polarity and carrier through the Tuya transport."""
import json
from .codec import raw_to_tuya


def prepare_signal(result, transport="zosung"):
    pulses = result.get("pulses")
    if not isinstance(pulses, list) or not pulses:
        raise ValueError("No IR signal generated")
    duration = sum(abs(p[0]) for p in pulses) / 1_000_000
    if duration > 30:
        raise ValueError("IR signal exceeds 30 seconds")
    while pulses and pulses[-1][0] < 0:
        pulses = pulses[:-1]
    if not pulses or pulses[0][0] <= 0:
        raise ValueError("Signal starts with a space; Tuya cannot represent it")
    carriers = {p[1] for p in pulses if p[0] > 0}
    if len(carriers) != 1:
        raise ValueError("Signal changes carrier frequency; Tuya cannot represent it")
    frequency = carriers.pop()
    if frequency <= 30000 or frequency > 60000:
        raise ValueError(f"Unsupported blaster carrier: {frequency} Hz")
    raw = []
    for index, pulse in enumerate(pulses):
        value = pulse[0]
        if (value > 0) != (index % 2 == 0):
            raise ValueError("IR engine returned non-alternating timings")
        if abs(value) > 65535:
            raise ValueError("Internal duration exceeds 65535 us; Tuya cannot encode it without altering the waveform")
        raw.append(abs(value))
    encoded = raw_to_tuya(raw)
    if transport == "base64":
        if frequency != 38000:
            raise ValueError(f"Protocol needs {frequency} Hz. Select carrier-aware Zosung transport")
        payload = encoded
    elif transport == "zosung":
        message = json.dumps({"key_num": 1, "delay": 300, "key1": {"num": 1, "freq": frequency, "type": 1, "key_code": encoded}})
        # Z2M JSON-parses values on /set/ir_code_to_send. Encode a JSON string
        # so the converter receives the full message as text, not an object
        # that some converter versions turn into "[object Object]".
        payload = json.dumps(message)
    else:
        raise ValueError("Unknown transport")
    return payload, duration
