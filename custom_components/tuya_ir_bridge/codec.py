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


def tuya_to_raw(value: str) -> list[int]:
    """Decode bounded FastLZ level-1 learned timings, including back references."""
    if not isinstance(value, str) or not 1 <= len(value) <= 16000:
        raise ValueError("Invalid learned code length")
    try:
        data = base64.b64decode(value, validate=True)
        output = bytearray()
        pos = 0
        while pos < len(data):
            control = data[pos]
            pos += 1
            if control < 32:
                length = control + 1
                if pos + length > len(data):
                    raise ValueError("Truncated literal")
                output.extend(data[pos:pos + length])
                pos += length
            else:
                length = (control >> 5) + 2
                if length == 9:
                    length += data[pos]
                    pos += 1
                distance = ((control & 31) << 8) + data[pos] + 1
                pos += 1
                if distance > len(output):
                    raise ValueError("Invalid reference")
                for _ in range(length):
                    output.append(output[-distance])
            if len(output) > 8192:
                raise ValueError("Learned code exceeds 4096 timings")
        if not output or len(output) % 2:
            raise ValueError("Incomplete timings")
        raw = [v[0] for v in struct.iter_unpack("<H", output)]
        if any(v == 0 for v in raw):
            raise ValueError("Zero timing")
        return raw
    except (IndexError, TypeError, ValueError) as err:
        raise ValueError(f"Invalid learned Tuya code: {err}") from err
