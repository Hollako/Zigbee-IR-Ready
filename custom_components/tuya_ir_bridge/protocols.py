"""Dynamic encoders. Electra layout follows IRremoteESP8266 (see NOTICE).

Python port, 2026-09-07. Copyright 2018-2021 David Conran (Electra).
SPDX-License-Identifier: LGPL-2.1-or-later
"""


def pulse_distance(data: bytes, header=(9000, 4500), mark=560,
                   one=1690, zero=560) -> list[int]:
    """Send bytes least-significant bit first and finish with a mark.

    The final idle gap is handled by the transport, not truncated to uint16.
    """
    result = list(header)
    for byte in data:
        for bit in range(8):
            result.extend((mark, one if byte & (1 << bit) else zero))
    result.append(mark)
    return result


def encode_command(protocol: str, address: int, command: int) -> list[int]:
    """Generate standard 8-bit NEC or Samsung32 address/command frames."""
    if type(address) is not int or type(command) is not int:
        raise ValueError("Address and command must be integers")
    if not 0 <= address <= 255 or not 0 <= command <= 255:
        raise ValueError("Address and command must be 0..255")
    if protocol == "nec":
        return pulse_distance(bytes((address, address ^ 255, command, command ^ 255)))
    if protocol == "samsung":
        return pulse_distance(bytes((address, address, command, command ^ 255)),
                              header=(4500, 4500))
    raise ValueError(f"Unsupported command protocol: {protocol}")


def electra_state(mode: str, temperature: int, fan: str) -> bytes:
    """Build the 13-byte Electra AC state including its additive checksum."""
    modes = {"off": 0, "auto": 0, "cool": 1, "dry": 2, "heat": 4, "fan_only": 6}
    fans = {"auto": 5, "low": 3, "medium": 2, "high": 1}
    if mode not in modes or fan not in fans:
        raise ValueError("Unsupported Electra mode or fan")
    if type(temperature) is not int or not 16 <= temperature <= 32:
        raise ValueError("Electra temperature must be an integer from 16 to 32")
    data = bytearray(13)
    data[0] = 0xC3
    data[1] = ((temperature - 8) << 3) | 7
    data[2] = 7 << 5
    data[4] = fans[fan] << 5
    data[6] = modes[mode] << 5
    data[9] = 0 if mode == "off" else 0x20
    data[11] = 0x08
    data[12] = sum(data[:12]) & 255
    return bytes(data)


def encode_electra(mode: str, temperature: int, fan: str) -> list[int]:
    return pulse_distance(electra_state(mode, temperature, fan),
                          header=(9166, 4470), mark=646, one=1647, zero=547)
