"""Constants for the Sony Legacy integration."""

from datetime import timedelta

DOMAIN = "sony"

CONF_APP_PORT = "app_port"
CONF_DMR_PORT = "dmr_port"
CONF_IRCC_PORT = "ircc_port"
CONF_PIN = "pin"
CONF_MAC = "mac"

DEFAULT_NAME = "Sony Device"
DEFAULT_APP_PORT = 50202
DEFAULT_DMR_PORT = 52323
DEFAULT_IRCC_PORT = 50001

SCAN_INTERVAL = timedelta(seconds=30)

# Common IRCC command names exposed by the remote entity.
# Availability depends on the device generation / category.
COMMANDS = [
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
    "Power",
    "Eject",
    "Stop",
    "Pause",
    "Play",
    "Rewind",
    "Forward",
    "PopUpMenu",
    "TopMenu",
    "Up",
    "Down",
    "Left",
    "Right",
    "Confirm",
    "Options",
    "Display",
    "Home",
    "Return",
    "Karaoke",
    "Netflix",
    "Mode3D",
    "Next",
    "Prev",
    "Favorites",
    "SubTitle",
    "Audio",
    "Angle",
    "Blue",
    "Red",
    "Green",
    "Yellow",
    "Advance",
    "Replay",
    "Input",
    "TvInput",
    "Media",
    "SyncMenu",
    "GGuide",
    "EPG",
    "ChannelUp",
    "ChannelDown",
    "VolumeUp",
    "VolumeDown",
    "Mute",
]
