# Changelog

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
