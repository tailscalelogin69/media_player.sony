# Sony SideView (Legacy API) for Home Assistant

Control **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **Video & TV SideView** app — over local HTTP / IRCC on your LAN.

This is a modern rewrite of the long-lived `media_player.sony` custom component (originally by [dilruacs](https://github.com/dilruacs/media_player.sony) / [alexmohr](https://github.com/alexmohr/media_player.sony)), updated for current Home Assistant and HACS.

**Integration domain:** `sony_sideview`  
**UI title:** Sony SideView (Legacy API)

This does **not** replace or hide official integrations (Sony Bravia TV, PlayStation Network, Songpal, etc.). Search for those by their own names; this one appears as **Sony SideView (Legacy API)** only.

---

## Important — same subnet required

**The device must be on the same subnet as Home Assistant.**  
This is a limitation of Sony’s firmware: the unit will not respond correctly to control requests from a different subnet (or from across a VPN / VLAN without proper L2 adjacency).

---

## What this is for

| Use this integration | Use the official integration instead |
|----------------------|--------------------------------------|
| Blu-ray players (BDP-Sxxx, UBP-Xxxx, …) | **Sony Bravia TV** — Android / Google TV Bravia |
| Home theatre (e.g. **BDV-E4100**, BDV-Nxxx) | **Songpal** — newer soundbars / AV that speak Songpal |
| Older Bravia TVs that only pair with SideView | **PlayStation Network** / PS4 / PS5 integrations |
| Any device the SideView phone app controls via LAN | |

If the official SideView app can control it on your network, this integration almost certainly can too.

---

## Features

| Feature | Details |
|---------|---------|
| Config flow | UI setup with PIN pairing — no YAML required |
| Media player | Power, play / pause / stop, next / previous, volume step / set / mute |
| Remote entity | Send any IRCC command (`Eject`, `Power`, `Input`, coloured buttons, digits, …) |
| Local only | Polling over LAN — no cloud |
| HACS | Install as a custom repository |

---

## Changes from the original repositories

What was fixed and modernized versus [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony) and [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony):

### Home Assistant compatibility
- **Removed YAML-only `setup_platform` / `PLATFORM_SCHEMA`** — replaced with a full **config flow** (`config_flow.py`) and config entries
- **Removed deprecated Configurator** PIN UI — replaced with config-flow steps (`user` → `pin`)
- **Replaced deprecated `SUPPORT_*` flags** with `MediaPlayerEntityFeature`
- **Replaced string states** with `MediaPlayerState` where applicable
- **All entity I/O is async** — blocking `sonyapilib` calls run via `hass.async_add_executor_job`
- **`DataUpdateCoordinator`** for polled power / playback / volume state
- **Device registry** — proper `DeviceInfo`, unique IDs, manufacturer/model
- **`manifest.json`** with `config_flow`, `iot_class`, `integration_type`, `version`, `issue_tracker`
- **Translations** (`translations/en.json`) for flow titles and errors
- **HACS** — `hacs.json`, installable as a custom repository

### Architecture (combined best of both upstreams)
- From **alexmohr**: volume level / set support, battle-tested `sonyapilib` usage, device port notes
- From **dilruacs / albaintor**: remote entity, config-entry direction, dual media_player + remote platforms
- Clean package layout: `__init__`, `const`, `coordinator`, `config_flow`, `media_player`, `remote`

### UI / discovery collision fix (v1.1.0)
- **Domain renamed** from generic `sony` → **`sony_sideview`**
- **Display name** set to **Sony SideView (Legacy API)** so it does not occupy or dominate a generic “Sony” result in Add Integration
- Official Sony Bravia, PlayStation Network, Songpal, and related integrations remain fully visible and selectable
- Component folder is `custom_components/sony_sideview/` (matches domain)

### Behaviour preserved from upstream
- Same-subnet requirement (Sony firmware)
- PIN registration flow against the device
- Configurable app / DMR / IRCC ports (defaults + known BDP-S590 alternate set)
- Full IRCC command list on the remote entity (`Eject`, transport, D-pad, colours, etc.)
- Still uses **`sonyapilib==0.5.0`** for the wire protocol

### Removed / not carried forward
- YAML `configuration.yaml` platform setup
- `custom_updater` / `tracker.json` workflow
- Old `sony.conf` JSON credential file on disk (credentials live in the config entry)
- Sync-only entity methods and broad bare `except` paths where avoidable

---

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet**
- Device **powered on** for the initial pairing step
- Network control / Remote Start enabled on the device (wording varies by model)

---

## Installation

### HACS (recommended)

1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Repository URL: `https://github.com/tailscalelogin69/media_player.sony`  
   Category: **Integration**
3. Download **Sony SideView (Legacy API)**
4. **Restart** Home Assistant
5. Settings → Devices & services → **Add integration** → search **SideView** or **Sony SideView**

If you previously installed an older build that used the `sony` domain folder, remove `custom_components/sony` after upgrading so only `sony_sideview` remains, then restart.

### Manual

Copy `custom_components/sony_sideview` into your Home Assistant `config/custom_components/` directory, restart, then add the integration from the UI.

---

## Pairing

1. Power the Sony device **on**.
2. Add **Sony SideView (Legacy API)** and enter its **IP address** (static IP / DHCP reservation recommended).
3. Leave ports at the defaults unless your model needs different ones (see [Ports](#ports)).
4. The device should show a **PIN** on screen (or on its front display).
5. Enter that PIN in Home Assistant.

**Tips from upstream**

- If no PIN appears, retry; on some models the first registration attempt triggers the on-screen code.
- Power-cycle the device and retry if registration fails.
- After a successful pair, the PIN is stored in the config entry.

---

## Ports

| Setting   | Default |
|-----------|---------|
| App port  | `50202` |
| DMR port  | `52323` |
| IRCC port | `50001` |

Known alternate (from upstream):

| Device   | App port | DMR port | IRCC port |
|----------|----------|----------|-----------|
| BDP-S590 | `52323`  | `50202`  | `52323`   |

If setup fails with defaults (especially BDP / UBP players), try the alternate set.

---

## Entities

| Platform       | Purpose |
|----------------|---------|
| `media_player` | Power, transport controls, volume |
| `remote`       | Send arbitrary IRCC commands |

### Remote commands

```yaml
action: remote.send_command
target:
  entity_id: remote.your_device_remote
data:
  command: Eject
```

| Command | Description |
|---------|-------------|
| `Num0` … `Num9` | Digit keys |
| `Power` | Power |
| `Eject` | Eject disc |
| `Stop` / `Pause` / `Play` | Transport |
| `Rewind` / `Forward` | Seek |
| `Next` / `Prev` | Chapter / track |
| `PopUpMenu` / `TopMenu` | Menus |
| `Up` / `Down` / `Left` / `Right` / `Confirm` | D-pad |
| `Options` / `Display` / `Home` / `Return` | Navigation |
| `Red` / `Green` / `Yellow` / `Blue` | Colour buttons |
| `Audio` / `SubTitle` / `Angle` | Stream options |
| `Input` / `TvInput` / `Media` | Source (names vary by firmware) |
| `VolumeUp` / `VolumeDown` / `Mute` | Volume |
| `ChannelUp` / `ChannelDown` | Channel (TVs) |
| `Netflix` / `Karaoke` / `Mode3D` / … | App / mode keys where supported |

---

## Example: BDV-E4100 — power on + analog RCA input

```yaml
sequence:
  - action: media_player.turn_on
    target:
      entity_id: media_player.bdv_e4100
  - delay: "00:00:03"
  - action: remote.send_command
    target:
      entity_id: remote.bdv_e4100_remote
    data:
      command: Input
  - action: remote.send_command
    target:
      entity_id: remote.bdv_e4100_remote
    data:
      command: Eject
```

Try `Input`, `TvInput`, or `Media` until the rear L/R RCA input is selected.

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Cannot connect | Same subnet? Powered on? Correct IP? Ports? |
| No PIN | Power-cycle; enable Remote Start / network control; retry |
| Invalid PIN | Codes expire — restart the flow |
| Commands do nothing | Wrong ports; network standby off; unsupported command |
| Old `sony` folder still present | Delete `custom_components/sony` after upgrading to `sony_sideview` |

```yaml
logger:
  default: info
  logs:
    custom_components.sony_sideview: debug
    sonyapilib: debug
```

---

## Credits

- [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony) and [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony)
- [alexmohr/sonyapilib](https://github.com/alexmohr/sonyapilib) (based on Kirk Herron / SonyAPILib and others)
- Remote entity / config-flow groundwork from community contributors (including albaintor)

---

## License

Apache-2.0 (same as the upstream projects).
