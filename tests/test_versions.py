"""Keep every browser asset on the integration release cache key."""
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/tuya_ir_bridge"


class VersionTests(unittest.TestCase):
    def test_frontend_assets_match_manifest_version(self):
        version = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]
        manager = (COMPONENT / "www/manager.js").read_text(encoding="utf-8")
        card = (COMPONENT / "www/remote_card.js").read_text(encoding="utf-8")

        for asset in ("remote_card.js", "panel.js", "editor.js"):
            self.assertIn(f"./{asset}?v={version}", manager)
        self.assertEqual(re.search(r'const CARD_VERSION = "([^"]+)";', card).group(1), version)


if __name__ == "__main__":
    unittest.main()
