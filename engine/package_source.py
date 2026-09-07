"""Package exact corresponding upstream source alongside the build adapter."""
import gzip
import io
import json
from pathlib import Path
import tarfile

root=Path(__file__).resolve().parents[1]
source=root/'.build/IRremoteESP8266'
revision=json.loads((root/'engine/upstream.json').read_text())['revision']
target=root/'engine/vendor/IRremoteESP8266-source.tar.gz'
with target.open('wb') as stream, gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as zipped, tarfile.open(fileobj=zipped,mode='w') as archive:
    files=sorted((source/'src').rglob('*'))+[source/'test/IRsend_test.h',source/'LICENSE.txt']
    for path in files:
        if not path.is_file(): continue
        data=path.read_bytes()
        info=tarfile.TarInfo('IRremoteESP8266/'+path.relative_to(source).as_posix())
        info.size=len(data); info.mode=0o644
        archive.addfile(info,io.BytesIO(data))
    data=revision.encode()
    info=tarfile.TarInfo('IRremoteESP8266/UPSTREAM_REVISION'); info.size=len(data)
    archive.addfile(info,io.BytesIO(data))
print(target)
