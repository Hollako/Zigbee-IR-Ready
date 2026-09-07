# Zigbee IR Ready

Experimental HACS custom integration connecting Tuya/Zosung Zigbee IR blasters
through Zigbee2MQTT to native Home Assistant entities. Domain: `tuya_ir_bridge`.

**0.1.1 is a developer scaffold, not universal hardware support.** It generates
timings dynamically, but has not been tested in a running Home Assistant instance
or against physical blasters. Do not assume every Tuya device uses this format.

## Current scope

| Feature | Status |
| --- | --- |
| Raw microseconds → Tuya Base64 | Implemented; literal FastLZ framing |
| Electra AC temperature, mode, fan | Python port; experimental |
| NEC 8-bit address / Samsung32 | Dynamic command encoding |
| Climate, Remote, Media Player, Light | Native platform scaffold |
| Sidebar device creation | Persistent devices; reused Tasmota IR Ready CSS/layout |
| Blaster selection | Explicit MQTT command topic |
| Gree, Mitsubishi, Daikin | Pending individual protocol/model ports |
| Sony, RC5, RC6 | Pending; carrier and toggle/repeat handling needed |
| Blaster discovery / editing / deletion | Pending |
| Upstream maintenance | Weekly revision metadata fetch in GitHub Actions |
| Automatic runtime definition updates | Pending validated schema; no downloaded code execution |

The panel retains the original project's no-build vanilla Web Component approach,
top toolbar, grouped sidebar, theme-aware fields and status bar. It is a focused
creation scaffold, not a full copy of the Tasmota editor's features. Lit conversion
can follow once the backend contract is stable.

## Install

Updating from 0.1.0: update the integration files, restart Home Assistant, then
reload the panel page. Version 0.1.1 fixes the administrator check that caused
"Unknown error" when listing or creating devices. Climate still offers Electra
only; select Remote, Media Player or Light to see NEC and Samsung32.

1. Configure MQTT and Zigbee2MQTT and confirm the blaster exposes `ir_code_to_send`.
2. Once published, add this repository in HACS as a custom **Integration** repository;
   alternatively copy `custom_components/tuya_ir_bridge` into HA's `custom_components`.
3. Restart Home Assistant. Add **Zigbee IR Ready** under Settings → Devices & services.
4. Open **Zigbee IR Ready** in the sidebar as an administrator. Enter a name, type,
   protocol and full topic, e.g. `zigbee2mqtt/Living Room IR/set/ir_code_to_send`.
5. For NEC/Samsung devices provide the address and named command IDs from model
   documentation. Media/Light require `turn_on` and `turn_off`. A remote can use
   arbitrary names with `remote.send_command`.

A protocol describes the signal format; it cannot infer a TV model's command IDs.
No learned waveform files are needed, but model/address/command information is.
Power-toggle-only remotes cannot provide reliable discrete on/off behavior.

## Project structure

```text
custom_components/tuya_ir_bridge/
  manifest.json        HACS/HA integration metadata
  __init__.py          MQTT dependency, platform lifecycle, sidebar registration
  config_flow.py       Single bridge setup
  const.py             Domain/platform constants
  hub.py               Storage, validation, per-blaster send serialization
  websocket_api.py     Admin-only list/create API
  entity.py            Stable unique IDs and device registry metadata
  climate.py           Electra climate platform
  media_player.py      IR media power platform
  remote.py            Named protocol commands
  light.py             On/off light platform
  protocols.py         Dynamic bitstream/timing engines
  codec.py             uint16-LE → FastLZ literals → Base64
  strings.json
  translations/en.json
  www/panel.js         Tasmota-derived panel styling
  www/manager.js       Device creation Web Component
tests/test_encoders.py
scripts/check_upstream.py
.github/workflows/{validate,upstream}.yml
hacs.json
README.md
info.md
LICENSE
NOTICE
```

## Payload encoding

`codec.raw_to_tuya([9000, 4500, 560, 1690])` accepts positive integer microsecond
durations, alternating mark/space, beginning with a mark. It packs unsigned 16-bit
little-endian samples, prepends each group of up to 32 bytes with its length minus
one, then Base64-encodes the resulting valid FastLZ level-1 literal stream.
This trades compression efficiency for a small dependency-free encoder.

Hex input via `raw_hex_to_tuya` means a hex dump of **uint16 little-endian timings**,
not a NEC command number or arbitrary hex IR code. Durations above 65535 are rejected;
splitting them naively would change mark/space polarity. Final idle gaps are omitted
from single-frame engines and the transport applies conservative pacing.

Publish the resulting Base64 string directly to the property topic:

```python
from homeassistant.components import mqtt
await mqtt.async_publish(
    hass,
    "zigbee2mqtt/Living Room IR/set/ir_code_to_send",
    raw_to_tuya(timings),
    qos=0,
    retain=False,
)
```

The equivalent root `/set` topic requires a JSON object containing `ir_code_to_send`.
The Base64 envelope itself contains no carrier frequency. This initial transport
targets the usual 38 kHz path; Sony/RC5/RC6 need explicit carrier-aware transport
support and hardware verification. MQTT publishing does not confirm IR delivery.
All entity state is optimistic and is not restored after restart in this scaffold.

Entity objects are added through `async_add_entities`; stable `unique_id` and
`DeviceInfo.identifiers` let HA populate its registries. Writing registry records
alone would not create functional entities. Virtual device configuration survives
restarts using HA Storage. Concurrent transmissions sharing a topic are serialized.

## Upstream strategy

IRremoteESP8266 is a C++ implementation, not a directly importable Python database.
Port each supported variant, retain its license/attribution and compare generated
state bytes and timings against upstream vectors before enabling it in the UI.
The weekly workflow fetches the latest Electra source revision as a review artifact;
it does **not** claim to synchronize executable encoders. A future declarative
schema needs versioning, bounds, source pinning, rollback and last-known-good caching.
New algorithms should ship through reviewed integration releases.

## Validation and publishing

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components
node --check custom_components/tuya_ir_bridge/www/manager.js
node --test tests/panel.test.cjs
```

These check wire layout/codec boundaries and syntax, not HA lifecycle, browser
rendering or physical delivery. Before a release: exercise setup/unload/reload,
admin restrictions, persistence and entity services inside HA; compare captured
waveforms for each supported model; run hassfest and HACS validation. Brand assets,
release packaging and HACS default-store submission remain release work.

Public repository: `Hollako/Zigbee-IR-Ready`. This initial source snapshot is an
experimental scaffold; it is not a hardware-validated stable release.

## Sources

- [Zigbee2MQTT ZS06](https://www.zigbee2mqtt.io/devices/ZS06.html)
- [Zosung converter and encodeTuyaTimings](https://github.com/Koenkk/zigbee-herdsman-converters/blob/master/src/lib/zosung.ts)
- [IRremoteESP8266 Electra implementation](https://github.com/crankyoldgit/IRremoteESP8266/blob/master/src/ir_Electra.cpp)
- [Home Assistant custom panels](https://developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/)
- [Tasmota IR Ready](https://github.com/Hollako/Tasmota-IR-Ready)

See LICENSE and NOTICE for upstream licensing and attribution.
