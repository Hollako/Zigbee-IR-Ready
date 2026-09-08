"""Run inside an isolated Home Assistant image; never connects to a broker."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from custom_components.tuya_ir_bridge.hub import Hub
from custom_components.tuya_ir_bridge.climate import IRClimate
from custom_components.tuya_ir_bridge.remote import IRRemote
from custom_components.tuya_ir_bridge.media_player import IRMediaPlayer
from custom_components.tuya_ir_bridge.light import IRLight
from custom_components.tuya_ir_bridge.services import register_services


async def main():
    hass=HomeAssistant('/tmp/zigbee-ir-test')
    dr.async_setup(hass)
    await dr.async_load(hass)
    hub=Hub(hass,SimpleNamespace())
    await hub.load()
    hass.data['tuya_ir_bridge']=hub
    register_services(hass)
    added=[]
    for kind in ('climate','remote','media_player','light'): hub.adders[kind]=added.append
    for protocol in ('DAIKIN','GREE','MITSUBISHI_AC','ELECTRA_AC'):
        device=await hub.create({'name':protocol,'device_type':'climate','protocol':protocol,'topic':'zigbee2mqtt/test/set/ir_code_to_send','transport':'zosung'})
        entity=IRClimate(hub,device)
        entity.async_write_ha_state=lambda:None
        with patch.object(hub,'send',new_callable=AsyncMock) as send:
            await entity.async_set_hvac_mode('cool')
            await entity.async_set_temperature(temperature=25)
            await entity.async_irhvac({'SwingV':'Auto','Power':True})
            assert send.await_count==3
            assert entity.target_temperature==25
    hub.entities['climate.test']=entity
    with patch.object(hub,'send',new_callable=AsyncMock) as send:
        edited=await hub.update(device['id'],{**{k:v for k,v in device.items() if k!='id'},'max_temp':24,'hvac_options':{'SwingV':'Auto'}})
        assert entity.unique_id==device['id'] and entity.max_temp==24
        assert entity.target_temperature==24 and entity._previous is None
        send.assert_not_awaited()
    device=await hub.create({'name':'TV','device_type':'remote','protocol':'SONY','topic':'zigbee2mqtt/test/set/ir_code_to_send','transport':'zosung','commands':{'power':{'Bits':12,'Data':'0xA90'}}})
    remote=IRRemote(hub,device)
    with patch.object(hub,'send',new_callable=AsyncMock) as send:
        await remote.async_send_command(['power'])
        assert send.await_count==1
    # Editing updates the same live entity and stored ID, without sending IR.
    hub.entities['remote.test']=remote
    before_count=len(hub.devices)
    changed={key:value for key,value in device.items() if key!='id'}
    changed.update(name='Updated TV',topic='zigbee2mqtt/new/set/ir_code_to_send',protocol='NEC',commands={'power':{'Bits':32,'Data':'0x20DF10EF'}})
    remote.async_write_ha_state=Mock()
    with patch.object(hub,'send',new_callable=AsyncMock) as send:
        updated=await hub.update(device['id'],changed)
        assert updated['id']==device['id'] and len(hub.devices)==before_count
        assert remote.unique_id==device['id'] and remote.device['topic']==changed['topic']
        send.assert_not_awaited()
        await remote.send_command('power')
        assert send.call_args.args[0]['topic']==changed['topic']
    stored=await hub.store.async_load()
    assert next(d for d in stored if d['id']==device['id'])['name']=='Updated TV'
    with patch.object(hub.store,'async_save',side_effect=OSError('disk full')):
        try: await hub.update(device['id'],{**changed,'name':'Must not persist'})
        except OSError: pass
        else: raise AssertionError('Expected save failure')
    assert remote.device['name']=='Updated TV'
    for device_id,data in [('missing',changed),(device['id'],{**changed,'device_type':'light'})]:
        try: await hub.update(device_id,data)
        except ValueError: pass
        else: raise AssertionError('Expected invalid edit rejection')
    print('HA imports, four AC families, state updates, options, storage, services and Sony remote passed')
    await hass.async_stop()

asyncio.run(main())
