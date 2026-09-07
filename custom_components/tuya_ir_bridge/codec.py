"""Tuya/Zosung FastLZ literal-stream encoding. No third-party dependency."""
import base64
import struct
from collections.abc import Sequence


def raw_to_tuya(raw: Sequence[int]) -> str:
    """Encode alternating mark/space durations in microseconds, mark first.

    Unsigned uint16 little-endian samples are wrapped in FastLZ level-1
    literal blocks (max 32 bytes). This is valid, but intentionally does not
    use back references. Base64 of uint16 bytes alone is NOT Tuya encoding.
    Carrier frequency is not represented in this payload.
    """
    if not raw or len(raw) > 4096:
        raise ValueError("Expected 1..4096 durations")
    if any(type(value) is not int or not 1 <= value <= 65535 for value in raw):
        raise ValueError("Durations must be integer microseconds in 1..65535")
    packed = struct.pack(f"<{len(raw)}H", *raw)
    framed = bytearray()
    for offset in range(0, len(packed), 32):
        chunk = packed[offset:offset + 32]
        framed.append(len(chunk) - 1)
        framed.extend(chunk)
    return base64.b64encode(framed).decode("ascii")


def raw_hex_to_tuya(value: str) -> str:
    """Convert a hex dump of uint16-LE durations; not a protocol command hex."""
    data = bytes.fromhex(value)
    if len(data) % 2:
        raise ValueError("Hex timing data must contain complete uint16 values")
    return raw_to_tuya([item[0] for item in struct.iter_unpack("<H", data)])
