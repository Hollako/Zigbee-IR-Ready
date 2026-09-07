"""Fetch upstream revision metadata for maintainer review, never execute code."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

url = "https://api.github.com/repos/crankyoldgit/IRremoteESP8266/commits?path=src/ir_Electra.cpp&per_page=1"
request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Zigbee-IR-Ready"})
with urlopen(request, timeout=30) as response:
    commits = json.loads(response.read(1_000_000))
report = {"source": url, "electra_latest_commit": commits[0]["sha"],
          "review_required": True,
          "note": "Compare changes, port deliberately, and validate wire vectors before releasing."}
Path("upstream-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
