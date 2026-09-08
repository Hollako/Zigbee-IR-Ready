"""Exercise feature state, learned IR and MQTT session cleanup inside HA."""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from homeassistant.core import HomeAssistant, get_hassjob_callable_job_type, HassJobType
from homeassistant.helpers import device_registry as dr
from homeassistant.components.climate import ClimateEntityFeature
from custom_components.tuya_ir_bridge.hub import Hub, validate_device
from custom_components.tuya_ir_bridge.climate import IRClimate
from custom_components.tuya_ir_bridge.switch import IRFeatureSwitch
from custom_components.tuya_ir_bridge.media_player import IRMediaPlayer
from custom_components.tuya_ir_bridge.remote import IRRemote
from custom_components.tuya_ir_bridge.codec import raw_to_tuya

async def main():
    hass=HomeAssistant('/tmp/zigbee-feature-test');dr.async_setup(hass);await dr.async_load(hass)
    hub=Hub(hass,SimpleNamespace());await hub.load()
    added=[]
    for kind in ('climate','remote','media_player','light','switch'):hub.adders[kind]=added.append
    config={'name':'AC','device_type':'climate','protocol':'ELECTRA_AC','topic':'Zigbee/Test/set/ir_code_to_send','transport':'base64','hvac_modes':['off','cool'],'fan_modes':['auto','high'],'swing_modes':['off','vertical'],'feature_switches':['Light','SwingV'],'hvac_options':{'Light':False}}
    device=await hub.create(config);ac=IRClimate(hub,device);ac.async_write_ha_state=Mock();hub.entities['climate.test']=ac
    toggle=IRFeatureSwitch(hub,device,'Light')
    assert toggle.assumed_state is False
    assert ac.hvac_modes==['off','cool'] and ac.fan_modes==['auto','high']
    assert ac.supported_features & ClimateEntityFeature.SWING_MODE
    with patch.object(hub,'send',new_callable=AsyncMock):
        await ac.async_set_hvac_mode('cool')
        await toggle.async_turn_on();assert toggle.is_on is True
        await ac.async_set_temperature(temperature=25);assert ac._previous['Light'] is True
        await toggle.async_turn_off();assert toggle.is_on is False
        await ac.async_set_swing_mode('vertical');assert ac.swing_mode=='vertical'
        await ac.async_set_temperature(temperature=26);assert ac._previous['SwingV']=='Auto'
    await hub.update(device['id'],{**config,'feature_switches':[],'fan_modes':[]})
    assert not toggle.available and not ac.supported_features & ClimateEntityFeature.FAN_MODE
    for invalid in ({'hvac_modes':['off']},{'fan_modes':['nope']},{'feature_switches':['Power']}):
        try:validate_device({**config,**invalid},hub.catalogue)
        except ValueError:pass
        else:raise AssertionError('Invalid capabilities accepted')
    code=raw_to_tuya([9000,4500,560,1690,560])
    media=await hub.create({'name':'TV','device_type':'media_player','protocol':'NEC','topic':config['topic'],'transport':'base64','commands':{key:{'Learned':code} for key in ('turn_on','turn_off','volume_up','volume_down','source:HDMI 1')}})
    mp=IRMediaPlayer(hub,media);mp.async_write_ha_state=Mock();hub.entities['media_player.test']=mp
    remote=IRRemote(hub,media);assert remote.unique_id!=mp.unique_id
    assert mp.source_list==['HDMI 1']
    with patch.object(hub,'send',new_callable=AsyncMock) as send:
        await mp.async_select_source('HDMI 1');await remote.send_command('power_on');assert send.await_count==2
    callback=None;unsub=Mock()
    async def subscribe(hass,topic,handler,**kwargs):
        nonlocal callback
        assert get_hassjob_callable_job_type(handler) is HassJobType.Callback
        callback=handler;return unsub
    with patch('custom_components.tuya_ir_bridge.learning.mqtt.async_subscribe',side_effect=subscribe),patch('custom_components.tuya_ir_bridge.learning.mqtt.async_publish',new_callable=AsyncMock) as publish:
        session=await hub.learning.start(config['topic']);await asyncio.sleep(0)
        publish.assert_awaited_once_with(hass,'Zigbee/Test/set',json.dumps({'learn_ir_code':'ON'}),qos=0,retain=False)
        callback(SimpleNamespace(retain=True,payload=json.dumps({'learned_ir_code':code})))
        assert hub.learning.status(session['session'])['status']=='waiting'
        callback(SimpleNamespace(retain=False,payload=json.dumps({'learned_ir_code':code})))
        await hub.learning.sessions[session['session']]['task']
        assert hub.learning.status(session['session'])['code']==code;unsub.assert_called_once()
        other=await hub.learning.start(config['topic']);await asyncio.sleep(0)
        await hub.learning.cancel(other['session']);assert hub.learning.status(other['session'])['status']=='cancelled'
        assert unsub.call_count==2
    await hub.learning.close();await hass.async_stop()
    print('Feature switches, selected capabilities, swing persistence, learned sends, media companions and learning cleanup passed')
asyncio.run(main())
