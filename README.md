# Zigbee IR Ready

Home Assistant custom integration for Tuya/Zosung Zigbee IR blasters managed by
Zigbee2MQTT. **Installed entirely through HACS. No companion app, add-on, Docker
container, compiler, or separate encoder server is required.**

Version 0.2.0 replaces the small Python encoder set with the actual
**IRremoteESP8266 C++ protocol engine**, compiled into self-contained helpers
bundled inside the integration. This is the library behind Tasmota's IR commands.
Signals are generated locally from device state or protocol data, converted to
Tuya payloads, and published through Home Assistant's MQTT integration.

## Protocol coverage

- **IRhvac:** upstream common AC state encoding, including Electra, Gree, Daikin
  variants, Mitsubishi variants, Fujitsu, Panasonic, LG, Samsung and more.
- **IRsend:** upstream scalar and byte-state send dispatch, including NEC,
  Samsung, Sony, RC5, RC6 and others; accepts Protocol, Bits, hexadecimal Data
  and Repeat. Raw microsecond timing arrays are also supported.
- The panel loads the catalogue from the executable: **66 HVAC entries and 124
  general send entries**, plus RAW. It is no longer a hard-coded shortlist.

This provides upstream encoder coverage, not a promise that every Tuya blaster
can reproduce every signal or that every Tasmota syntax extension is supported.
Tasmota may bundle a different library revision. IRsend needs model-specific
Data values, just as Tasmota does. AC state encoding needs no learned code files.

## Installation and update

1. Add `https://github.com/Hollako/Zigbee-IR-Ready` in HACS as a custom
   **Integration** repository and download it.
2. Restart Home Assistant and add **Zigbee IR Ready** in Devices & services.
3. Open **Zigbee IR Ready** in the sidebar as an administrator.
4. Select device type, exact protocol variant and MQTT property topic, e.g.
   `zigbee2mqtt/Living Room IR/set/ir_code_to_send`.
5. Select transport and create the device. Creation validates encoding without
   transmitting and creates native HA entities.

**Requirements:** 64-bit Linux Home Assistant (`amd64` or `aarch64`, including
64-bit Raspberry Pi), MQTT, Zigbee2MQTT and a compatible blaster. Windows/macOS
and 32-bit Linux HA installations are not supported by the bundled executable.
HA OS and HA Container need no additional encoder installation.

Updating from 0.1.x: update all files, restart HA and reload the panel. Existing
Electra devices and old NEC/Samsung numeric command maps remain supported.
Old devices retain legacy Base64 transport; new devices default to Zosung JSON.
There are no runtime source or binary downloads.

## Transport

**Zosung JSON** sends a complete message with `key1.freq` and generated Base64
`key1.key_code`. It requires a recent Zigbee2MQTT Zosung converter that accepts
complete JSON IR messages on `ir_code_to_send`. Use this for protocols requiring
36 kHz or 40 kHz. Your blaster must physically support the requested carrier.

The MQTT payload is a JSON-encoded string containing the complete message.
Outer quotes and escaped inner quotes are intentional: Zigbee2MQTT parses the
MQTT value first, then the Zosung converter parses the resulting string.

**Legacy Base64** sends only the generated Base64 string. The converter supplies
38 kHz. Other carrier frequencies are rejected instead of silently changed.

Both publish to `<base topic>/<friendly name>/set/ir_code_to_send`, without retained
messages. Native signed mark/space durations are merged before uint16 little-endian
/ FastLZ literal framing / Base64 conversion. Trailing silence is removed from
the packet and retained for pacing. Internal durations above 65535 µs, changing
carriers, signals beginning with a space, and oversized signals are rejected;
they are never clamped. Sends sharing a topic are serialized. MQTT publication
does not confirm physical IR delivery.

Use the exact, case-sensitive MQTT base topic configured in Zigbee2MQTT. For
example, a device shown as `Zigbee/Master Room IR` needs
`Zigbee/Master Room IR/set/ir_code_to_send`.

## Climate

Choose the exact protocol and numeric Model (`-1` uses the upstream default).
Set your model's temperature range and step. Optional IRhvac settings include
SwingV, SwingH, Quiet, Turbo, Econo, Light, Filter, Clean, Beep, iFeel, Sleep,
Clock and SensorTemp. Unsupported features can be ignored by the model encoder.

State is optimistic. Previous command state is retained per climate entity and
restored through HA state restoration, allowing upstream toggle/state-dependent
logic to compare states. The physical remote can still desynchronize that estimate.

## Commands and actions

Remote, Media Player and Light accept named IRsend command objects. Protocol is
inherited from the device unless overridden per command. Samsung example:

```json
{"power": {"Bits": 32, "Data": "0xE0E040BF", "Repeat": 0}}
```

Use values for your own model. Media Player and Light require `turn_on` and
`turn_off`; power-toggle codes are not reliable discrete on/off commands. Use
hex strings to preserve large Data values. State protocols require complete byte
strings of `ceil(Bits / 8)` bytes. Variable-length protocols need explicit Bits.

Use `remote.send_command` with saved names, or the administrator actions:

```yaml
action: tuya_ir_bridge.irsend
data:
  entity_id: remote.living_room_tv
  command:
    Protocol: SONY
    Bits: 12
    Data: "0xA90"
    Repeat: 0
```

```yaml
action: tuya_ir_bridge.irhvac
data:
  entity_id: climate.living_room_ac
  command:
    Power: "On"
    Mode: Cool
    Temp: 24
    FanSpeed: Auto
    SwingV: Auto
```

IRhvac uses the target climate's configured Protocol and Model. Keys are
case-insensitive; booleans accept true/false or On/Off. Temperatures use Celsius.
RAW uses `Protocol: RAW`, `Frequency: 38000`, and a Data array of positive,
alternating mark/space timings. Direct IRsend also accepts `38,9000,4500,...`.
Tasmota compressed raw strings, GlobalCache syntax, DataLSB and GPIO/channel
commands are not implemented.

## Validation and limitations

Native tests cover changing state for six AC families, NEC/Samsung/Sony/RC5/RC6,
invalid requests and transport encoding. Electra output is compared against the
independent Python port. An isolated Home Assistant 2026.6.2 test exercises
imports, creation, storage, climate actions/options and Sony remote sends with
MQTT transmission mocked.

`engine/catalogue-audit.json` records synthetic vectors across the catalogue;
it is **not hardware certification**. Known exceptions include long internal
gaps in some MIDEA, CARRIER_AC40 and MULTIBRACKETS requests, and an upstream YORK
common-HVAC dispatch failure. Other entries need specific models/state lengths.
Physical testing remains necessary.

The panel adapts the Tasmota IR Ready editor and remote card. Automatic blaster
discovery, device deletion, source-cycle tracking and online profile browsing
remain future work. It is not a complete replica of every Tasmota feature.

### Tabbed editor, learning and remotes (0.3.0)

- **Climate → Capabilities:** select the HVAC modes, fan speeds and swing
  positions exposed in Home Assistant. Off is always included. Select no fan or
  swing options to hide those controls. These choices describe your appliance;
  they cannot add hardware features absent from its protocol.
- **Climate → Behavior & Switches:** choose individual feature switches, grouped
  under the same Home Assistant device. They change the current IR state, which
  is reused by later commands. Initial feature values only seed that state.
  Deselecting a feature makes its existing switch unavailable, preserving its
  identity if you enable it again. Sleep uses the configured minutes (0 means
  the protocol's default). IR feature state is optimistic.
- **Remote / Media / Light:** edit commands in Power & Volume, Navigation,
  Playback, Channels & Colors, Keypad, Sources and Custom Commands tabs.
  Enter Bits and hexadecimal Data, or expand Advanced for full IRsend objects.
  Direct source commands named `source:HDMI 1` become media-player sources.
- **Learn:** point the original remote at the same Zigbee blaster and press a
  button. Learning waits up to 30 seconds and ignores retained MQTT messages.
  The captured code fills the command; **Test** transmits it, and **Save Changes**
  persists it. Cancel stops waiting; the blaster's own learning window may stay
  open until it times out. Learned commands use the Zosung 38 kHz assumption.
  This is optional button learning, not a replacement for generated HVAC state.
- **IR Remotes sidebar:** use the adapted Tasmota remote card with navigation,
  volume, keypad, source and custom buttons. Media players also receive a
  companion `remote` entity. Only configured commands appear. Media-player
  capabilities are enabled from configured commands; power-on/off are required.

The remote card can also be used in a dashboard by adding
`/tuya_ir_bridge_static/remote_card.js` as a JavaScript module resource and using:

```yaml
type: custom:zigbee-ir-ready-remote-card
entity: remote.living_room_tv
```

The sidebar loads its resources automatically. Backend learning/switch tests
and browser tests use mocked MQTT and HA services; physical validation of these
new features is still needed. Restart Home Assistant after updating to 0.3.0.

### Editing an existing device

Click a device in the panel's left sidebar to open **Edit Device**. Change its
name, MQTT topic, transport, protocol, model, temperature limits, HVAC options or
command map, then click **Save Changes**. Changes apply immediately to the existing
entity and persist across restarts; its entity ID stays the same. Saving does not
transmit IR. **Cancel Changes** reloads saved settings. Device type is fixed;
use **New Device** for a different type. Existing Home Assistant name overrides
remain in effect.

After updating through HACS, restart Home Assistant and reload the panel to load
the new frontend. Native dropdowns follow Home Assistant's light/dark theme.

## Architecture and rebuilding

```text
custom_components/tuya_ir_bridge/
  manifest.json, __init__.py, config_flow.py
  hub.py, native.py          Local engine and device storage
  signal.py, codec.py        Carrier/polarity validation and Tuya payloads
  commands.py, services.py   IRsend / IRhvac actions
  climate.py, remote.py, media_player.py, light.py, entity.py
  websocket_api.py           Admin panel API and protocol catalogue
  www/manager.js, panel.js   Sidebar and Tasmota-derived CSS
  bin/                      Static Linux executables and checksums
engine/
  main.cpp, build.py         Host adapter and build script
  upstream.json              Pinned upstream revision
  vendor/                   Corresponding source and JSON header
  catalogue-audit.json       Synthetic encoder/transport audit
tests/                      Protocol, panel and HA smoke tests
.github/workflows/           Validation, build and upstream checks
hacs.json, README.md, info.md, LICENSE, NOTICE
```

Upstream revision: `1e2f0f3ef0a93cbf2a8ddb2e95130f8f4c584b3f`. The host capture
boundary is patched to preserve polarity/carrier and advance the simulated timer.
Protocol algorithms are compiled from upstream. Requests use separate bounded
processes so global capture state cannot mix different devices' signals.

Rebuild/replace the binaries from included source on a Linux development machine
with Python, g++ and (for ARM64) g++-aarch64-linux-gnu:

```sh
mkdir -p .build
tar -xzf engine/vendor/IRremoteESP8266-source.tar.gz -C .build
python3 engine/build.py .build/IRremoteESP8266 amd64
python3 engine/build.py .build/IRremoteESP8266 aarch64
python3 -m unittest discover -s tests -v
node --test tests/panel.test.cjs
```

The scripts regenerate checksums for modified builds. These are development
instructions, not installation requirements. Weekly upstream checks produce a
review artifact. Encoder updates ship through tested integration releases.

Sources: [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266),
[Zosung converter](https://github.com/Koenkk/zigbee-herdsman-converters/blob/master/src/lib/zosung.ts),
[Tasmota IR Ready](https://github.com/Hollako/Tasmota-IR-Ready).
See LICENSE, NOTICE and engine/vendor for licenses and corresponding source.
