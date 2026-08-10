"""Constants for the Video & TV SideView (Legacy API) integration."""

from datetime import timedelta

DOMAIN = "tv_sideview"

CONF_APP_PORT = "app_port"
CONF_DMR_PORT = "dmr_port"
CONF_IRCC_PORT = "ircc_port"
CONF_PIN = "pin"
CONF_MAC = "mac"

DEFAULT_NAME = "SideView Device"
DEFAULT_APP_PORT = 50202
DEFAULT_DMR_PORT = 52323
DEFAULT_IRCC_PORT = 50001

# Poll more often so on/off and volume feel responsive in the UI
SCAN_INTERVAL = timedelta(seconds=15)

# Fallback / activity-list names. Live devices also expose their own list via
# getRemoteCommandList (preferred when available).
COMMANDS = [
    # Navigation / system
    "Confirm",
    "Enter",
    "Up",
    "Down",
    "Left",
    "Right",
    "Home",
    "Options",
    "Return",
    "Display",
    "Power",
    "Dimmer",
    # Digits
    "Num0",
    "Num1",
    "Num2",
    "Num3",
    "Num4",
    "Num5",
    "Num6",
    "Num7",
    "Num8",
    "Num9",
    # Transport
    "Play",
    "Pause",
    "Stop",
    "Rewind",
    "Forward",
    "Prev",
    "Next",
    "Replay",
    "Advance",
    "Eject",
    # Disc / menus
    "TopMenu",
    "PopUpMenu",
    "Audio",
    "SubTitle",
    "Angle",
    "Favorites",
    # Colours
    "Yellow",
    "Blue",
    "Red",
    "Green",
    # Volume
    "VolumeUp",
    "VolumeDown",
    "Mute",
    # Apps / misc (generic SideView)
    "Netflix",
    "SEN",
    "Mode3D",
    "Karaoke",
    "Input",
    "TvInput",
    "Media",
    "SyncMenu",
    "GGuide",
    "EPG",
    "ChannelUp",
    "ChannelDown",
    # BDV home theatre (BDV-E4100 and similar — from getRemoteCommandList)
    "BDV:Function",
    "BDV:Bluetooth",
    "BDV:SoundMode",
    "BDV:SoundModeUp",
    "BDV:SoundModeDown",
    "BDV:SoundOutput",
    "BDV:MusicEQ",
    "BDV:Sleep",
    "BDV:KeyControl+",
    "BDV:KeyControl-",
    "BDV:Echo",
    "BDV:MicVol+",
    "BDV:MicVol-",
    "BDV:SpeakerIllumination",
    "BDV:FootBall",
    # URL-type actions some firmwares advertise
    "PartyOn",
    "PartyOff",
    "ZoomIn",
    "ZoomOut",
    "BrowserBack",
    "BrowserForward",
    "BrowserBookmarkList",
]
