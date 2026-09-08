"""Run without Home Assistant: python -m unittest discover -s tests."""
import base64
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/tuya_ir_bridge"

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

codec, protocols = load("codec"), load("protocols")

class EncodingTests(unittest.TestCase):
    def test_learned_back_reference_and_limits(self):
        # Literal 560us followed by an overlapping two-byte-distance reference.
        encoded=base64.b64encode(bytes.fromhex('0130024001')).decode()
        self.assertEqual(codec.tuya_to_raw(encoded),[560,560,560])
        raw=[9000,4500,560,1690]*25
        self.assertEqual(codec.tuya_to_raw(codec.raw_to_tuya(raw)),raw)
        for value in ('!!!','',base64.b64encode(bytes.fromhex('4001')).decode(),base64.b64encode(bytes.fromhex('0130')).decode()):
            with self.assertRaises(ValueError): codec.tuya_to_raw(value)
    def test_fixed_payload(self):
        # Four uint16 LE values with a single 8-byte literal run.
        self.assertEqual(base64.b64decode(codec.raw_to_tuya([9000, 4500, 560, 1690])),
                         bytes.fromhex("072823941130029a06"))

    def test_chunk_boundaries(self):
        for count in (1, 15, 16, 17, 32, 33, 4096):
            raw = [65535] * count
            stream = base64.b64decode(codec.raw_to_tuya(raw))
            decoded = bytearray()
            pos = 0
            while pos < len(stream):
                size = stream[pos] + 1
                self.assertLessEqual(size, 32)
                decoded.extend(stream[pos + 1:pos + 1 + size])
                pos += 1 + size
            self.assertEqual(list(struct.unpack(f"<{count}H", decoded)), raw)

    def test_invalid_timings(self):
        for raw in ([], [0], [-1], [65536], [1.5], [True], [1] * 4097):
            with self.assertRaises(ValueError):
                codec.raw_to_tuya(raw)

    def test_hex(self):
        self.assertEqual(codec.raw_hex_to_tuya("2823941130029a06"), codec.raw_to_tuya([9000,4500,560,1690]))

    def test_nec_wire_bytes(self):
        raw = protocols.encode_command("nec", 0x10, 0x20)
        bits = [int(raw[i] > 1000) for i in range(3, len(raw)-1, 2)]
        decoded = [sum(bits[i+j] << j for j in range(8)) for i in range(0,32,8)]
        self.assertEqual(decoded, [0x10,0xef,0x20,0xdf])
        self.assertEqual(len(raw), 67)

    def test_electra_vector(self):
        # Independent expected layout: cool/24/auto, both swings off.
        self.assertEqual(protocols.electra_state("cool", 24, "auto").hex(),
                         "c387e000a00020000020000812")
        self.assertEqual(len(protocols.encode_electra("cool",24,"auto")), 211)

    def test_invalid_protocol(self):
        with self.assertRaises(ValueError):
            protocols.encode_command("rc6", 0, 1)

if __name__ == "__main__":
    unittest.main()
