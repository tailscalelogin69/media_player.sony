"""IRCC sender matching the official Video & TV SideView app.

The framing and the per-device key tables were taken from the SideView APK
(com.sony.tvsideview.common.ircc.IrccClient / class c, and
com.sony.tvsideview.common.unr.cers.CersClient methods W, X and Y).

A tap is one SOAP call whose 13-byte payload starts with control START (0).
The app only sends REPEAT (1) while a key is held, then STOP (3) on release.
SOAP fault 803 is treated as success (the set accepted the key but was busy).
Fault 606 is an auth failure.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# control byte — IrccClient.Control
CTRL_START = 0
CTRL_REPEAT = 1
CTRL_STOP = 3

# KeyData.Category(category, format, frame)
BD1 = (7258, 3, 3)  # BDP 5th/6th gen
AUSYS3 = (80, 2, 3)  # BDV volume block
AUSYS3E = (208, 2, 3)  # BDV transport / function
AUSYS3SE = (528, 3, 3)  # BDV navigation
AUSYS3EE = (1552, 3, 3)  # BDV colour keys
DVD4 = (3578, 3, 3)
DVD4E = (3834, 3, 3)
TV1 = (1, 1, 3)

# App waits 40s only for a Blu-ray recorder (MajorDeviceType.BDR).
# Every other SideView device, including BDV home theatre and TV, waits 120s.
# WolModel.f16306k / f16307l. The wait ends early once IRCC or DMR answers.
WOL_WAIT_RECORDER = 40
WOL_WAIT_DEFAULT = 120

SOAP_HEAD = (
    '<?xml version="1.0"?>\n'
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n'
    "  <s:Body>\n"
    '    <u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1">\n'
    "      <IRCCCode>"
)
SOAP_TAIL = (
    "</IRCCCode>\n"
    "    </u:X_SendIRCC>\n"
    "  </s:Body>\n"
    "</s:Envelope>\n"
)
SOAP_ACTION = '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"'

# Names the SideView Key enum actually sends. Aliases cover the labels this
# integration already documented and the short names inside KeyData.
_ALIASES = {
    "volplus": "VolumeUp",
    "volume+": "VolumeUp",
    "volminus": "VolumeDown",
    "volume-": "VolumeDown",
    "muting": "Mute",
    "ff": "Forward",
    "fr": "Rewind",
    "flashf": "Advance",
    "flashr": "Replay",
    "open": "Eject",
    "cancel": "Return",
    "option": "Options",
    "options": "Options",
    "popup": "PopUpMenu",
    "popupmenu": "PopUpMenu",
    "topmenu": "TopMenu",
    "subtitle": "SubTitle",
    "soundmode": "BDV:SoundModeUp",
    "bdv:soundmode": "BDV:SoundModeUp",
    "bdv:soundmodeup": "BDV:SoundModeUp",
    "function": "Function",
    "bdv:function": "Function",
    "previous": "Prev",
    "prev": "Prev",
    "enter": "Confirm",
    "ok": "Confirm",
    "back": "Return",
    "poweroff": "Power",
    "poweron": "Power",
    "num12": "Num12",
    "dot": "DOT",
}


def _keys(*rows: tuple[str, tuple[int, int, int], int]) -> dict[str, tuple[tuple[int, int, int], int]]:
    return {name: (cat, code) for name, cat, code in rows}


# CersClient.W — DeviceType.BDP5G / BDP6G_A. Power/Netflix/Karaoke/Mode3D are
# the extra BD1 codes the same category table has always shipped with; the
# app itself loads Power from getRemoteCommandList when the unit is online.
_BDP = _keys(
    ("Play", BD1, 26),
    ("Stop", BD1, 24),
    ("Pause", BD1, 25),
    ("Forward", BD1, 28),
    ("Rewind", BD1, 27),
    ("Next", BD1, 86),
    ("Prev", BD1, 87),
    ("Advance", BD1, 117),
    ("Replay", BD1, 118),
    ("Display", BD1, 65),
    ("Eject", BD1, 22),
    ("Favorites", BD1, 94),
    ("Angle", BD1, 101),
    ("Audio", BD1, 100),
    ("SubTitle", BD1, 99),
    ("Yellow", BD1, 105),
    ("Blue", BD1, 102),
    ("Red", BD1, 103),
    ("Green", BD1, 104),
    ("Num1", BD1, 0),
    ("Num2", BD1, 1),
    ("Num3", BD1, 2),
    ("Num4", BD1, 3),
    ("Num5", BD1, 4),
    ("Num6", BD1, 5),
    ("Num7", BD1, 6),
    ("Num8", BD1, 7),
    ("Num9", BD1, 8),
    ("Num0", BD1, 9),
    ("Up", BD1, 57),
    ("Down", BD1, 58),
    ("Left", BD1, 59),
    ("Right", BD1, 60),
    ("Confirm", BD1, 61),
    ("Return", BD1, 67),
    ("Options", BD1, 63),
    ("Home", BD1, 66),
    ("TopMenu", BD1, 44),
    ("PopUpMenu", BD1, 41),
    ("Power", BD1, 21),
    ("Karaoke", BD1, 74),
    ("Netflix", BD1, 75),
    ("Mode3D", BD1, 77),
)

# CersClient.X — DeviceType.BDV3G (BDV-E4100 and the same home-theatre remote).
_BDV = _keys(
    ("Prev", AUSYS3SE, 48),
    ("Next", AUSYS3SE, 49),
    ("Replay", AUSYS3SE, 33),
    ("Advance", AUSYS3SE, 32),
    ("Play", AUSYS3E, 2),
    ("Rewind", AUSYS3SE, 51),
    ("Forward", AUSYS3SE, 52),
    ("Display", AUSYS3SE, 24),
    ("Pause", AUSYS3E, 1),
    ("Stop", AUSYS3E, 0),
    ("VolumeUp", AUSYS3, 18),
    ("VolumeDown", AUSYS3, 19),
    ("Mute", AUSYS3, 20),
    ("BDV:SoundModeUp", AUSYS3E, 75),
    ("Eject", AUSYS3SE, 60),
    ("Favorites", AUSYS3EE, 75),
    ("Audio", AUSYS3SE, 18),
    ("SubTitle", AUSYS3SE, 17),
    ("Yellow", AUSYS3EE, 7),
    ("Blue", AUSYS3EE, 4),
    ("Red", AUSYS3EE, 5),
    ("Green", AUSYS3EE, 6),
    ("Function", AUSYS3E, 105),
    ("Num1", AUSYS3SE, 0),
    ("Num2", AUSYS3SE, 1),
    ("Num3", AUSYS3SE, 2),
    ("Num4", AUSYS3SE, 3),
    ("Num5", AUSYS3SE, 4),
    ("Num6", AUSYS3SE, 5),
    ("Num7", AUSYS3SE, 6),
    ("Num8", AUSYS3SE, 7),
    ("Num9", AUSYS3SE, 8),
    ("Num0", AUSYS3SE, 9),
    ("TopMenu", AUSYS3SE, 25),
    ("PopUpMenu", AUSYS3SE, 26),
    ("Home", AUSYS3E, 7),
    ("Options", AUSYS3SE, 115),
    ("Return", AUSYS3SE, 125),
    ("Up", AUSYS3SE, 120),
    ("Down", AUSYS3SE, 121),
    ("Right", AUSYS3SE, 123),
    ("Left", AUSYS3SE, 122),
    ("Confirm", AUSYS3SE, 124),
    # Not in the hardcoded BDV map; the app reads it from the device.
    # BD1 power is the fallback when that list never arrived.
    ("Power", BD1, 21),
)

# CersClient.Y — DeviceType.NETBOX2010 / DVD-era players.
_DVD = _keys(
    ("Prev", DVD4, 48),
    ("Next", DVD4, 49),
    ("Replay", DVD4, 92),
    ("Advance", DVD4E, 20),
    ("Play", DVD4, 50),
    ("Rewind", DVD4, 34),
    ("Forward", DVD4, 35),
    ("Display", DVD4, 84),
    ("Pause", DVD4, 57),
    ("Stop", DVD4, 56),
    ("VolumeUp", TV1, 18),
    ("VolumeDown", TV1, 19),
    ("Mute", TV1, 20),
    ("Favorites", DVD4E, 94),
    ("Audio", DVD4, 100),
    ("SubTitle", DVD4, 99),
    ("Yellow", DVD4E, 105),
    ("Blue", DVD4E, 102),
    ("Red", DVD4E, 103),
    ("Green", DVD4E, 104),
    ("Num1", DVD4, 0),
    ("Num2", DVD4, 1),
    ("Num3", DVD4, 2),
    ("Num4", DVD4, 3),
    ("Num5", DVD4, 4),
    ("Num6", DVD4, 5),
    ("Num7", DVD4, 6),
    ("Num8", DVD4, 7),
    ("Num9", DVD4, 8),
    ("Num0", DVD4, 9),
    ("Home", DVD4, 83),
    ("Options", DVD4E, 23),
    ("Return", DVD4, 14),
    ("Up", DVD4, 121),
    ("Down", DVD4, 122),
    ("Right", DVD4, 124),
    ("Left", DVD4, 123),
    ("Confirm", DVD4, 11),
    ("Power", TV1, 21),
)

# TV1 codes the app uses for volume, plus the adjacent channel/power keys
# from the same TV1 map (format 1, category 1, frame 3). Navigation on a
# live TV still comes from getRemoteCommandList.
_TV = _keys(
    ("VolumeUp", TV1, 18),
    ("VolumeDown", TV1, 19),
    ("Mute", TV1, 20),
    ("ChannelUp", TV1, 16),
    ("ChannelDown", TV1, 17),
    ("Power", TV1, 21),
)

PROFILES: dict[str, dict[str, tuple[tuple[int, int, int], int]]] = {
    "bdp": _BDP,
    "bdv": _BDV,
    "dvd": _DVD,
    "tv": _TV,
}

PROFILE_LABELS = {
    "auto": "Auto (device list, then a guessed remote)",
    "bdv": "Home theatre (BDV) — SideView BDV3G map",
    "bdp": "Blu-ray player (BDP) — SideView BD1 map",
    "dvd": "DVD / network player — SideView DVD4 map",
    "tv": "TV — SideView TV1 volume / power / channel",
}


def canonical_name(name: str) -> str:
    """Fold app short-names and older integration labels onto one key."""
    raw = (name or "").strip()
    if not raw:
        return raw
    folded = _ALIASES.get(raw.lower().replace(" ", ""))
    return folded or raw


def encode_ircc(control: int, fmt: int, category: int, code: int, frame: int) -> str:
    """Build the base64 IRCC payload the SideView app posts."""
    raw = bytes(
        (
            control & 0xFF,
            0,
            (fmt >> 8) & 0xFF,
            fmt & 0xFF,
            (category >> 24) & 0xFF,
            (category >> 16) & 0xFF,
            (category >> 8) & 0xFF,
            category & 0xFF,
            (code >> 24) & 0xFF,
            (code >> 16) & 0xFF,
            (code >> 8) & 0xFF,
            code & 0xFF,
            frame & 0xFF,
        )
    )
    return base64.b64encode(raw).decode("ascii")


def decode_ircc(value: str) -> tuple[int, int, int, int] | None:
    """Inverse of the app's Ircc code parser (class c.l)."""
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError):
        return None
    if len(raw) < 13:
        return None
    fmt = ((raw[2] & 0xFF) << 8) + (raw[3] & 0xFF)
    category = (
        ((raw[4] & 0xFF) << 24)
        + ((raw[5] & 0xFF) << 16)
        + ((raw[6] & 0xFF) << 8)
        + (raw[7] & 0xFF)
    )
    code = (
        ((raw[8] & 0xFF) << 24)
        + ((raw[9] & 0xFF) << 16)
        + ((raw[10] & 0xFF) << 8)
        + (raw[11] & 0xFF)
    )
    frame = raw[12] & 0xFF
    return fmt, category, code, frame


def code_for(profile: str, name: str) -> str | None:
    """START payload for a profile key, or None."""
    table = PROFILES.get(profile) or {}
    found = table.get(canonical_name(name))
    if not found:
        return None
    (category, fmt, frame), key_code = found
    return encode_ircc(CTRL_START, fmt, category, key_code, frame)


def guess_profile(name: str | None, nickname: str | None = None) -> str:
    """Pick a fallback remote the way the app picks DeviceType."""
    blob = f"{name or ''} {nickname or ''}".lower()
    if "bdv" in blob or "home theatre" in blob or "home theater" in blob:
        return "bdv"
    if "dvd" in blob or "netbox" in blob:
        return "dvd"
    if "bravia" in blob or "tv" in blob.split():
        return "tv"
    return "bdp"


def profile_names(profile: str) -> list[str]:
    return sorted((PROFILES.get(profile) or {}).keys())


def names_for(name: str) -> set[str]:
    """Every label that should hit the same key.

    The APK's Key enum calls the source key ``Function`` and the sound-field
    key ``BDV:SoundModeUp``. A live getRemoteCommandList often publishes the
    longer ``BDV:`` names instead. Both have to match.
    """
    raw = (name or "").strip()
    if not raw:
        return set()
    canon = canonical_name(raw)
    found = {raw, canon}
    folded = raw.lower().replace(" ", "")
    for alias, target in _ALIASES.items():
        if alias == folded or target == canon or target == raw:
            found.add(target)
    if canon == "Function":
        found.update({"Function", "BDV:Function"})
    if canon == "BDV:SoundModeUp":
        found.update({"BDV:SoundModeUp", "BDV:SoundMode", "SoundMode"})
    return found


def _command_attr(obj: Any, attr: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)


def wol_wait_seconds(profile: str) -> int:
    """Seconds to wait after the magic packet, matching WolModel.

    Only a Blu-ray recorder uses the short timer. We have no recorder
    profile, so BDV / BDP / DVD / TV all use the app's 120s deadline.
    """
    if profile == "bdr":
        return WOL_WAIT_RECORDER
    return WOL_WAIT_DEFAULT


def _lookup_device_command(device: Any, name: str) -> Any:
    """Find a live getRemoteCommandList entry, including BDV: aliases.

    api_version 0 means sonyapilib invented a BD1 list. Those codes are
    wrong for a BDV or DVD, so ignore them and use the app tables.
    """
    commands = getattr(device, "commands", None) or {}
    if not commands or getattr(device, "api_version", 1) == 0:
        return None
    wanted = {item.lower() for item in names_for(name)}
    for key, obj in commands.items():
        candidates = {str(key).lower()}
        obj_name = _command_attr(obj, "name")
        if obj_name:
            candidates.add(str(obj_name).lower())
        if candidates & wanted:
            return obj
    return None
    url = getattr(device, "control_url", None)
    if url:
        return str(url)
    host = device.host
    port = getattr(device, "ircc_port", 50001) or 50001
    return f"http://{host}:{port}/IRCC"


def _request_headers(device: Any) -> dict[str, str]:
    headers = {
        "content-type": "text/xml; charset=utf-8",
        "soapaction": SOAP_ACTION,
    }
    extra = dict(getattr(device, "headers", {}) or {})
    for key, value in extra.items():
        if key.lower() in ("content-type", "soapaction", "content-length"):
            continue
        headers[key] = value
    return headers


def _fault_code(body: str) -> int | None:
    start = body.find("errorCode")
    if start < 0:
        return None
    digits = []
    seen = False
    for char in body[start:]:
        if char.isdigit():
            digits.append(char)
            seen = True
        elif seen:
            break
    if not digits:
        return None
    try:
        return int("".join(digits))
    except ValueError:
        return None


def post_ircc(device: Any, ircc_b64: str, timeout: float = 3.0) -> bool:
    """POST one IRCC code. 803 counts as success, matching IrccClient.e."""
    import requests
    url = _control_url(device)
    body = SOAP_HEAD + ircc_b64 + SOAP_TAIL
    try:
        resp = requests.post(
            url,
            data=body.encode("utf-8"),
            headers=_request_headers(device),
            cookies=getattr(device, "cookies", None),
            timeout=timeout,
        )
    except requests.RequestException as err:
        _LOGGER.debug("IRCC post failed: %s", err)
        return False
    if resp.status_code < 400:
        return True
    fault = _fault_code(resp.text or "")
    if fault == 803:
        _LOGGER.debug("IRCC 803 (busy) treated as success")
        return True
    if fault == 606:
        _LOGGER.warning("IRCC 606 forbidden — the device wants pairing again")
    else:
        _LOGGER.debug("IRCC HTTP %s fault %s", resp.status_code, fault)
    return False


def _post_url(device: Any, url: str) -> bool:
    """URL-type command from getRemoteCommandList (app uses HTTP GET)."""
    import requests
    try:
        resp = requests.get(
            url,
            headers=_request_headers(device),
            cookies=getattr(device, "cookies", None),
            timeout=4,
        )
    except requests.RequestException as err:
        _LOGGER.debug("URL command failed: %s", err)
        return False
    return resp.status_code < 400


def send_command(device: Any, name: str, profile: str = "auto") -> bool:
    """Send one key the way SideView does.

    Live getRemoteCommandList wins. Otherwise the APK table for `profile`
    (or a guess when profile is ``auto``).
    """
    resolved = canonical_name(name)
    live = _lookup_device_command(device, name)
    if live is not None:
        value = _command_attr(live, "value") or ""
        kind = (_command_attr(live, "type") or "").lower()
        if kind == "url" or str(value).startswith("http"):
            return _post_url(device, str(value))
        decoded = decode_ircc(str(value))
        if decoded:
            fmt, category, code, frame = decoded
            payload = encode_ircc(CTRL_START, fmt, category, code, frame)
            return post_ircc(device, payload)
        if value:
            return post_ircc(device, str(value))

    chosen = profile
    if chosen in (None, "", "auto"):
        chosen = guess_profile(
            getattr(device, "nickname", None),
            getattr(device, "nickname", None),
        )
    payload = code_for(chosen, resolved)
    if payload:
        _LOGGER.debug("IRCC fallback %s/%s", chosen, resolved)
        return post_ircc(device, payload)

    _LOGGER.debug("No IRCC code for %s (profile %s)", name, chosen)
    return False


def _self_check() -> None:
    """Encoder must reproduce the well-known TV1 VolumeUp payload."""
    volume_up = encode_ircc(CTRL_START, TV1[1], TV1[0], 18, TV1[2])
    if volume_up != "AAAAAQAAAAEAAAASAw==":
        raise SystemExit(f"TV1 VolumeUp mismatch: {volume_up}")
    power = code_for("tv", "Power")
    if power != "AAAAAQAAAAEAAAAVAw==":
        raise SystemExit(f"TV1 Power mismatch: {power}")
    decoded = decode_ircc(volume_up)
    if decoded != (1, 1, 18, 3):
        raise SystemExit(f"decode mismatch: {decoded}")
    if canonical_name("BDV:Function") != "Function":
        raise SystemExit("alias failed")
    if "BDV:Function" not in names_for("Function"):
        raise SystemExit("live-list alias failed")
    if wol_wait_seconds("bdv") != 120 or wol_wait_seconds("tv") != 120:
        raise SystemExit("WOL wait must match the app (120s)")
    if wol_wait_seconds("bdr") != 40:
        raise SystemExit("recorder WOL wait must be 40s")
    if "VolumeUp" not in _BDV or _BDV["VolumeUp"][0] != AUSYS3:
        raise SystemExit("BDV volume category wrong")
    if code_for("bdv", "bdv:soundmode") != code_for("bdv", "BDV:SoundModeUp"):
        raise SystemExit("sound mode alias mismatch")
    print("ircc self-check ok", volume_up, "bdv keys", len(_BDV), "bdp", len(_BDP))


if __name__ == "__main__":
    _self_check()
