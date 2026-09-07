"""Compare shipped executables; ARM64 requires native host or binfmt emulation."""
import hashlib
import json
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
folder=root/'custom_components/tuya_ir_bridge/bin'
checksums=json.loads((folder/'checksums.json').read_text())
requests=[{'op':'catalogue'}]
for name in ('DAIKIN','GREE','MITSUBISHI_AC','ELECTRA_AC'):
    requests.append({'op':'hvac','state':{'Protocol':name,'Power':True,'Mode':'Cool','Temp':24,'FanSpeed':'Auto'}})
for name,bits,data in [('NEC',32,'0x20DF10EF'),('SONY',12,'0xA90'),('RC5',12,'0xC86'),('RC6',20,'0x1000C')]:
    requests.append({'op':'send','command':{'Protocol':name,'Bits':bits,'Data':data}})
outputs=[]
for arch in ('amd64','aarch64'):
    path=folder/f'ir-engine-{arch}'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==checksums[path.name]
    path.chmod(path.stat().st_mode|0o100)
    results=[]
    for request in requests:
        result=subprocess.run([str(path)],input=json.dumps(request),text=True,capture_output=True,timeout=15,check=True)
        results.append(json.loads(result.stdout))
    outputs.append(results)
assert outputs[0]==outputs[1], 'Architecture output mismatch'
print('amd64 and aarch64 checksums, catalogues, four HVAC and four IRsend vectors match')
