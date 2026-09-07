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

**Legacy Base64** sends only the generated Base64 string. The converter supplies
38 kHz. Other carrier frequencies are rejected instead of silently changed.

Both publish to `zigbee2mqtt/<friendly name>/set/ir_code_to_send`, without retained
messages. Native signed mark/space durations are merged before uint16 little-endian
/ FastLZ literal framing / Base64 conversion. Trailing silence is removed from
the packet and retained for pacing. Internal durations above 65535 µs, changing
carriers, signals beginning with a space, and oversized signals are rejected;
they are never clamped. Sends sharing a topic are serialized. MQTT publication
does not confirm physical IR delivery.

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

The panel reuses Tasmota IR Ready toolbar/sidebar styling with a vanilla Web
Component. Automatic blaster discovery, editing/deletion and richer media controls
remain future work. This is not yet a full replica of the Tasmota editor.

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
