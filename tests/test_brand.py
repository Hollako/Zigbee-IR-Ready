"""Validate the HACS brand assets without optional image dependencies."""
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrandAssetTests(unittest.TestCase):
    def test_icons_are_rgba_pngs_at_required_sizes(self):
        for filename, expected_size in (("icon.png", 256), ("icon@2x.png", 512)):
            data = (ROOT / "custom_components" / "tuya_ir_bridge" / "brand" / filename).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(data[12:16], b"IHDR")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height), (expected_size, expected_size))
            self.assertEqual(data[24], 8, "Brand icons must use 8-bit channels")
            self.assertEqual(data[25], 6, "Brand icons must use RGBA color")


if __name__ == "__main__":
    unittest.main()
