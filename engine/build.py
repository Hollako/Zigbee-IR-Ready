"""Build on Linux; outputs static helpers bundled with the HACS integration.

Requires g++, nlohmann-json3-dev, and optionally g++-aarch64-linux-gnu.
The source checkout must match upstream.json. No compiler runs inside HA.
"""
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve()
arch = sys.argv[2] if len(sys.argv) > 2 else 'amd64'
revision = json.loads((root / 'engine/upstream.json').read_text())['revision']
if (source/'.git').exists():
    actual = subprocess.check_output(['git', '-c', f'safe.directory={source}', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
else:
    actual = (source/'UPSTREAM_REVISION').read_text().strip()
if actual != revision:
    raise SystemExit('Upstream revision mismatch')
work = root / '.build' / f'engine-{arch}'
work.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / 'src', work / 'src', dirs_exist_ok=True)
shutil.copytree(source / 'test', work / 'test', dirs_exist_ok=True)
cpp = work / 'src/IRsend.cpp'
text = cpp.read_text()
text = text.replace('std::vector<int> timingList;', 'std::vector<int> timingList;\nextern void bridge_record(bool, uint32_t, uint32_t, uint8_t);')
# Capture polarity, carrier and simulated elapsed time, including adjacent
# marks/spaces. Upstream SWIG timingList alone loses this information.
for old, new in [
    ('timingList.push_back(usec);', 'bridge_record(true, usec, _freq_unittest, _dutycycle); IRtimer::add(usec);'),
    ('timingList.push_back(time);', 'bridge_record(false, time, _freq_unittest, _dutycycle); IRtimer::add(time);'),
]:
    if text.count(old) != 1:
        raise SystemExit(f'Upstream capture patch no longer matches: {old}')
    text = text.replace(old, new)
cpp.write_text(text)
# Derive the general send catalogue from upstream's dispatch overloads.
dispatch = text[text.index('bool IRsend::send('):]
names = sorted(set(re.findall(r'case ([A-Z][A-Z0-9_]+):', dispatch)))
(work / 'send_names.h').write_text('static const char* send_names[] = {' + ','.join(json.dumps(n) for n in names) + '};\n')
compiler = {'amd64': 'g++', 'aarch64': 'aarch64-linux-gnu-g++'}[arch]
includes = ['-I'+str(work/'src'), '-I'+str(work/'test'), '-I'+str(work), '-I'+str(root/'engine')]
# Copy JSON headers into build-local include root for cross compilation.
shutil.copytree(root/'engine/vendor/nlohmann', work/'nlohmann', dirs_exist_ok=True)
flags = ['-std=c++17', '-O2', '-DUNIT_TEST', '-DSWIGLIB', '-D_IR_LOCALE_=en-AU', *includes]
sources = sorted((work/'src').glob('*.cpp')) + [root/'engine/main.cpp']
from concurrent.futures import ThreadPoolExecutor
def compile_one(src):
    obj = work/(src.stem+'.o')
    subprocess.run([compiler, *flags, '-c', str(src), '-o', str(obj)], check=True)
    return str(obj)
with ThreadPoolExecutor(max_workers=4) as pool:
    objects = list(pool.map(compile_one, sources))
out = root/'custom_components/tuya_ir_bridge/bin'/f'ir-engine-{arch}'
out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([compiler, '-static', '-s', *objects, '-o', str(out)], check=True)
(out.parent/'checksums.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.parent.glob('ir-engine-*'))},indent=2)+'\n')
print(out)
