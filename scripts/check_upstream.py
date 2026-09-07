"""Fetch upstream revision metadata for maintainer review, never execute code."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
pinned = json.loads((root / "engine/upstream.json").read_text())["revision"]
url = "https://api.github.com/repos/crankyoldgit/IRremoteESP8266/commits/master"
request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Zigbee-IR-Ready"})
with urlopen(request, timeout=30) as response:
    commit = json.loads(response.read(1_000_000))
report = {"source": url, "pinned_revision": pinned, "latest_revision": commit["sha"],
          "review_required": commit["sha"] != pinned,
          "note": "Review upstream changes, update corresponding source, rebuild both architectures, and validate before releasing."}
Path("upstream-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
