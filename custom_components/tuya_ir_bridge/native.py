"""Local static IRremoteESP8266 helper bundled by HACS; no runtime downloads."""
import asyncio
import hashlib
import json
from pathlib import Path
import platform
import sys


class NativeEngine:
    def __init__(self):
        arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "aarch64", "arm64": "aarch64"}.get(platform.machine().lower())
        if sys.platform != "linux" or arch is None:
            raise ValueError("The bundled IR engine requires 64-bit Linux (amd64 or aarch64)")
        self.path = Path(__file__).parent / "bin" / f"ir-engine-{arch}"
        self.limit = asyncio.Semaphore(2)

    def prepare(self):
        """Verify artifact and restore executable mode after HACS extraction."""
        checksums = json.loads((self.path.parent / "checksums.json").read_text())
        if hashlib.sha256(self.path.read_bytes()).hexdigest() != checksums[self.path.name]:
            raise ValueError("IR engine checksum mismatch; reinstall the integration")
        self.path.chmod(self.path.stat().st_mode | 0o100)

    async def request(self, message):
        request = json.dumps(message, allow_nan=False).encode() + b"\n"
        if len(request) > 65536:
            raise ValueError("IR request exceeds 64 KiB")
        async with self.limit:
            process = await asyncio.create_subprocess_exec(str(self.path), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                async with asyncio.timeout(15):
                    stdout, stderr = await process.communicate(request)
            except BaseException:
                if process.returncode is None:
                    process.kill()
                await process.wait()
                raise
        if not stdout or len(stdout) > 2_000_000:
            raise ValueError("IR engine returned an invalid response")
        result = json.loads(stdout)
        if process.returncode or "error" in result:
            raise ValueError(result.get("error", "IR engine failed"))
        return result
