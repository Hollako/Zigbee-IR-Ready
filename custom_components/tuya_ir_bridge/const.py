"""Integration constants."""
DOMAIN = "tuya_ir_bridge"
DEVICE_TYPES = ["climate", "media_player", "remote", "light"]
PLATFORMS = [*DEVICE_TYPES, "switch"]
HVAC_MODES = ["off", "auto", "cool", "heat", "dry", "fan_only"]
FAN_MODES = ["auto", "min", "low", "medium", "high", "max"]
SWING_MODES = ["off", "vertical", "horizontal", "both", "highest", "high", "middle", "low", "lowest", "left max", "left", "horizontal middle", "right", "right max", "wide"]
FEATURES = ["SwingV", "SwingH", "Quiet", "Turbo", "Econo", "Light", "Filter", "Clean", "Beep", "Sleep", "iFeel"]
PROTOCOLS = ["electra", "nec", "samsung"]
