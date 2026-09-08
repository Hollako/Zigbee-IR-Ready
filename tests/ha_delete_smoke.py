"""Deletion regression in HA runtime with isolated registry doubles."""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from homeassistant.core import HomeAssistant
from custom_components.tuya_ir_bridge.hub import Hub
from custom_components.tuya_ir_bridge.const import DOMAIN

async def main():
    hass=HomeAssistant('/tmp/delete-test');hub=Hub(hass,NS(entry_id='entry'))
    hub.devices=[{'id':'one','name':'TV'},{'id':'two','name':'AC'}]
    def entity(unique):return NS(device={'id':'one'},_command_lock=asyncio.Lock(),hass=hass,entity_id=unique,async_remove=AsyncMock())
    primary=entity('remote.one');companion=entity('media_player.one');switch=entity('switch.one')
    hub.entities={'remote.one':primary,'media_player.one':companion};hub.feature_entities={('one','Light'):switch}
    records={name:NS(entity_id=name,platform=platform,config_entry_id=entry,unique_id=uid) for name,platform,entry,uid in [('remote.one',DOMAIN,'entry','one'),('switch.disabled',DOMAIN,'entry','one_Turbo'),('remote.companion',DOMAIN,'entry','one_remote'),('remote.other',DOMAIN,'entry','two'),('switch.foreign','mqtt','mqtt-entry','one_Light')]}
    registry=NS(entities=records,async_remove=Mock(side_effect=lambda key:records.pop(key)))
    devices=NS(async_get_device=Mock(return_value=NS(id='virtual-one',config_entries={'entry'})),async_remove_device=Mock())
    with patch('custom_components.tuya_ir_bridge.hub.er.async_get',return_value=registry),patch('custom_components.tuya_ir_bridge.hub.er.async_entries_for_device',return_value=[]),patch('custom_components.tuya_ir_bridge.hub.dr.async_get',return_value=devices):
        with patch.object(hub.store,'async_save',side_effect=OSError('disk full')):
            try:await hub.delete('one')
            except OSError:pass
            else:raise AssertionError('Expected failure')
        assert len(hub.devices)==2;primary.async_remove.assert_not_awaited();registry.async_remove.assert_not_called()
        await primary._command_lock.acquire()
        deletion=asyncio.create_task(hub.delete('one'));await asyncio.sleep(0)
        assert not deletion.done();primary._command_lock.release()
        await deletion
        for obj in (primary,companion,switch):obj.async_remove.assert_awaited_once()
        assert set(records)=={'remote.other','switch.foreign'}
        assert hub.devices==[{'id':'two','name':'AC'}] and await hub.store.async_load()==hub.devices
        assert not hub.entities and not hub.feature_entities
        devices.async_remove_device.assert_called_once_with('virtual-one')
        try:await hub.send({'id':'one'},{})
        except ValueError:pass
        else:raise AssertionError('Deleted device allowed to transmit')
    await hass.async_stop();print('Deletion: storage failure, active command wait, companions, disabled switches and unrelated registry protection passed')
asyncio.run(main())
