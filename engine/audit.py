"""Exercise catalogue entries without transmitting; write a reviewable report."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_native_engine import request, signal

catalogue=request({'op':'catalogue'})
report={'climate':{},'send':{}}
for name in catalogue['climate']:
    try:
        output=request({'op':'hvac','state':{'Protocol':name,'Power':True,'Mode':'Cool','Temp':24,'FanSpeed':'Auto'}})
        signal.prepare_signal(output)
        report['climate'][name]='encoded and transport-validated'
    except Exception as error:
        report['climate'][name]=str(error)
for item in catalogue['send']:
    try:
        bits=item['bits']
        data='00'*((bits+7)//8) if item['state'] else '0'
        output=request({'op':'send','command':{'Protocol':item['name'],'Bits':bits,'Data':data}})
        signal.prepare_signal(output)
        report['send'][item['name']]='encoded and transport-validated'
    except Exception as error:
        report['send'][item['name']]=str(error)
target=Path(__file__).resolve().parents[1]/'engine/catalogue-audit.json'
target.write_text(json.dumps(report,indent=2)+'\n')
for group,items in report.items():
    good=sum(v=='encoded and transport-validated' for v in items.values())
    print(f'{group}: {good}/{len(items)} default vectors fit the transport')
    for key,value in items.items():
        if value!='encoded and transport-validated': print(f'  {key}: {value}')
