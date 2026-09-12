# Changelog

## 0.4.7

- Fix climate saves rejected with `Unknown device fields` by keeping the
  frontend-only default swing controls inside `hvac_options` instead of sending
  them as device fields.
- Allowlist the editor values sent to the backend so UI helper values cannot
  block sensor or availability-topic persistence.
- Include offending field names in future backend validation errors.

## 0.4.6

- Match the Tasmota IR Ready manager shell with Home Assistant's native menu
  button, an empty initial selection view, grouped device sidebar, and a compact
  editor toolbar showing the selected device name.
- Move Create and Save to the top-right toolbar and style Save with the Home
  Assistant primary color and Delete with the error color.
- Persist linked temperature, humidity and power sensors plus the Zigbee2MQTT
  availability topic explicitly on every climate save. Keep stored sensor
  selections visible when an entity is temporarily unavailable.

## 0.4.5

- Constrain the wider Previous and Next row to the main remote-control width so
  it cannot expand the Lovelace card.
- Filter linked climate entity selectors to matching temperature, humidity and
  power categories. Replace new availability selections with a Zigbee2MQTT
  availability topic subscription while retaining old saved entity links.

## 0.4.4

- Split remote-card playback controls across two rows, with wider Previous and
  Next buttons on their own track-navigation row.

## 0.4.3

- Version every JavaScript module imported by the sidebar manager so Home
  Assistant browsers cannot reuse an older Sources editor after a HACS update.
- Add a release regression test that keeps the manifest, remote card and all
  imported frontend asset cache keys on the same version.

## 0.4.2

- Add a Cycle Source command to the Sources editor. Media players expose it as
  an Input action that can be selected repeatedly, while retaining direct source
  commands. The Lovelace remote card displays the matching input-cycle button.
- Display playback controls on the remote card with recognizable Material Design
  icons for play, pause, play/pause, stop, previous, next, rewind and fast-forward.
- Return immediately after publishing an IR command to MQTT so one blaster's
  cooldown does not delay later automation actions. Consecutive commands to the
  same blaster still observe safe transmission spacing.

## 0.4.1

- Display Learn buttons in orange with a wand icon and Test buttons in green
  with a play icon. Automatically close the learning dialog after showing its
  success message.

## 0.4.0

- Match the Tasmota-style AC editor with Connection, Capabilities and Behavior
  tabs, pill selectors and toggle controls.
- Add linked temperature, humidity, power and availability entities; initial
  mode and target; precision; Celsius/Fahrenheit; away temperature; MQTT delay;
  default swing values; keep-mode-on-power-on and ignore-off-temperature.
- Simplify remote commands to one code field with Learn and Test. Decode learned
  signals into protocol, bit count and hexadecimal data automatically, while
  retaining undecodable raw signals.
- Register the Lovelace remote card through both the global frontend module and
  the manager fallback, and refresh the card picker after registration.

## 0.3.2

- Compact command editing into one responsive row containing Format, Bits, Hex,
  Advanced, Learn, Test and Clear controls.

- Remove the separate IR Remotes sidebar. Register the remote card globally so
  **Zigbee IR Ready Remote** appears in Lovelace's Add Card picker without adding
  a dashboard resource manually.

## 0.3.1

- Keep the learning dialog open on failure and success, with a visible error,
  Retry, countdown and explicit Done/Close controls. Log backend learning errors.
- Register the learning MQTT handler as an event-loop callback so it can safely
  complete its asyncio future instead of running in an executor thread.

- Display climate feature switches as normal toggles using their last sent
  state, instead of separate On/Off buttons. IR state remains optimistic.

- Add Delete Device with confirmation. Remove saved commands and settings,
  loaded entities, disabled registry entries, feature switches and companion
  remotes. Preserve the physical blaster and unrelated virtual devices.
- Wait for active entity commands and reject queued sends after deletion.
- Validate deletion cancellation, storage failure and registry cleanup in tests.

## 0.3.0

- Add a tabbed editor, climate capability selections and dynamic feature switches.
- Add optional Zigbee2MQTT button learning, cancellation, command testing and
  per-button editors for power, navigation, playback, channels, keypad and sources.
- Adapt the Tasmota remote card into an IR Remotes sidebar and dashboard card;
  create companion remotes for media players and expose configured media controls.

- Send Zosung messages as JSON strings on the MQTT attribute topic so
  Zigbee2MQTT passes text to the converter. Previously, its MQTT parser produced
  an object that affected converters turned into an invalid IR code.
- Preserve the generated timing code and carrier frequency. Legacy Base64 is
  unchanged. Zosung still requires a converter supporting full JSON messages.

Validation: 22 Python tests, 5 panel tests, browser checks for learning and
remote controls, and isolated Home Assistant smoke tests. Hardware confirmation
of the new learning/features and Zosung fix is pending. Legacy Base64 Electra
operation has been confirmed by the user. Restart Home Assistant after updating.

## 0.2.1

- Fix unreadable native dropdown options in dark mode and follow theme changes.
- Add editing from the sidebar, Save Changes and Cancel Changes. Update protocol,
  blaster, command maps and climate parameters without replacing entity IDs.
- Validate edits before saving, preserve legacy transport/address settings, and
  apply updates after any active command completes. Saving sends no IR.
- Bump the panel cache URL so the updated interface loads after restarting HA.

Validation: 20 Python tests, 5 panel tests, a real Edge browser regression for
dark/light themes and editing, and isolated Home Assistant smoke tests.

## 0.2.0

- Replace the three-protocol backend with bundled, static IRremoteESP8266 engines
  for Linux AMD64 and ARM64. Installation remains entirely through HACS.
- Load the protocol selector from the engine catalogue: 66 HVAC and 124 general
  send entries, plus RAW. Display notes for known upstream/transport exceptions.
- Add Tasmota-style IRsend objects and IRhvac actions, protocol Model selection,
  additional HVAC features, and per-climate previous-state restoration.
- Preserve native mark/space polarity and carrier frequency; support full Zosung
  JSON for carrier-aware sends and retain the legacy 38 kHz Base64 option.
- Preserve existing Electra and numeric NEC/Samsung configurations.
- Include corresponding engine source, version pin, build tooling and checksums.

Validation: 20 Python tests, 3 panel tests, identical AMD64/ARM64 representative
vectors, and isolated Home Assistant 2026.6.2 smoke tests with MQTT mocked.
Physical hardware has not been validated. Read README for timing, carrier and
upstream exceptions. Requires 64-bit Linux HA; restart after updating.

## 0.1.1

- Fix invalid administrator checks causing the panel's Unknown error.
- Clarify the initial protocol selector and add panel/API regression tests.

## 0.1.0

- Initial HACS scaffold with Electra, NEC and Samsung Python encoders.
