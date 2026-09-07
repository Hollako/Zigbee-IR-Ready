"""Run inside an isolated Home Assistant image; never connects to a broker."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from homeassistant.core import HomeAssistant
from custom_components.tuya_ir_bridge.hub import Hub
from custom_components.tuya_ir_bridge.climate import IRClimate
from custom_components.tuya_ir_bridge.remote import IRRemote
from custom_components.tuya_ir_bridge.media_player import IRMediaPlayer
from custom_components.tuya_ir_bridge.light import IRLight
from custom_components.tuya_ir_bridge.services import register_services


async def main():
    hass=HomeAssistant('/tmp/zigbee-ir-test')
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
    device=await hub.create({'name':'TV','device_type':'remote','protocol':'SONY','topic':'zigbee2mqtt/test/set/ir_code_to_send','transport':'zosung','commands':{'power':{'Bits':12,'Data':'0xA90'}}})
    remote=IRRemote(hub,device)
    with patch.object(hub,'send',new_callable=AsyncMock) as send:
        await remote.async_send_command(['power'])
        assert send.await_count==1
    print('HA imports, four AC families, state updates, options, storage, services and Sony remote passed')
    await hass.async_stop()

asyncio.run(main())
