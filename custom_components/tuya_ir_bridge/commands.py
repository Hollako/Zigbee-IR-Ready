"""Normalize familiar Tasmota-style keys without interpreting executable input."""

HVAC_KEYS = ("Power", "Mode", "Temp", "FanSpeed", "SwingV", "SwingH", "Quiet", "Turbo", "Econo", "Light", "Filter", "Clean", "Beep", "iFeel", "Sleep", "Clock", "SensorTemp")
BOOL_KEYS = {"Power", "Quiet", "Turbo", "Econo", "Light", "Filter", "Clean", "Beep", "iFeel"}


def normalize_keys(command, keys):
    if not isinstance(command, dict):
        raise ValueError("Command must be an object")
    lookup = {key.lower(): key for key in keys}
    result = {}
    for key, value in command.items():
        canonical = lookup.get(str(key).lower())
        if canonical is None or canonical in result:
            raise ValueError(f"Unknown or duplicate command field: {key}")
        result[canonical] = value
    return result


def normalize_hvac(command):
    command = normalize_keys(command, HVAC_KEYS)
    for key in BOOL_KEYS & command.keys():
        value = command[key]
        if isinstance(value, str) and value.lower() in ("on", "off", "true", "false"):
            value = value.lower() in ("on", "true")
        if type(value) is not bool:
            raise ValueError(f"{key} must be true/false or On/Off")
        command[key] = value
    return command
