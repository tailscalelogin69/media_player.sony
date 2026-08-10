# Video & TV SideView (Legacy API)

Home Assistant integration for **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **[Video & TV SideView](https://info.tvsideview.sony.net/en_ww/)** app — local HTTP / IRCC control on your LAN.

| | |
|--|--|
| **Domain** | `tv_sideview` |
| **UI name** | Video & TV SideView (Legacy API) |
| **Folder** | `custom_components/tv_sideview/` |
| **Version** | 1.2.0 |

Search **Add integration** for **SideView**, **Video**, or **TV SideView**.  
Does **not** replace or hide official Sony Bravia, PlayStation Network, Songpal, or other integrations.

Modern rewrite of [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony) and [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony) for current Home Assistant (config flow, async I/O, coordinator, device registry, HACS).

---

## Important

The device must be on the **same subnet** as Home Assistant. This is a **Sony firmware limitation** — the unit will not respond correctly if HA is on another subnet/VLAN without routing tricks that still appear as the same L2/L3 path Sony expects.

---

## Compatibility

| Use this integration | Use official HA instead |
|----------------------|-------------------------|
| Blu-ray (BDP / UBP …) | **Sony Bravia TV** — Android / Google TV |
| Home theatre (**BDV-E4100**, BDV-Nxxx …) | **Songpal** — newer audio products |
| Older TVs that only speak SideView | **PlayStation Network** / console integrations |

If the SideView phone app can control the device on your LAN, this integration almost certainly can too.

---

## Features

- Config flow + PIN pairing (PIN and MAC stored in the config entry)
- Optional **MAC** at setup / options for **Wake-on-LAN** power-on
- Setup **succeeds when the device is offline** (entities default to off; update when reachable)
- **Media player** — power, transport, volume; DMR + library polling
- **Remote** — full IRCC list including **BDV:*** home-theatre commands
- Brand icon under `brand/icon.png`
- HACS custom repository support

---

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet**
- Device **powered on** for initial pairing
- **Media Remote Device Registration** / network remote control enabled on the device
- For power-on from standby: **MAC address** + network standby / Remote Start if available

---

## Installation

### HACS (recommended)

1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Repository: `https://github.com/tailscalelogin69/media_player.sony`  
   Category: **Integration**
3. Download **Video & TV SideView (Legacy API)**
4. Restart Home Assistant
5. Settings → Devices & services → **Add integration** → search **SideView**

### Manual

```bash
cd /tmp
curl -sL -o sideview.zip \
  "https://github.com/tailscalelogin69/media_player.sony/archive/refs/tags/v1.2.0.zip"
unzip -q sideview.zip
cp -a media_player.sony-1.2.0/custom_components/tv_sideview \
  /config/custom_components/
```

Path must be:

```text
/config/custom_components/tv_sideview/manifest.json
```

---

## Pairing

1. Power the device **on** (menu visible on the TV for BDV/BDP).
2. On many 2011–2013 units: **Setup → Network Settings → Media Remote Device Registration** and start registration.
3. In HA, add the integration (IP, name, optional MAC, ports).
4. Enter the **PIN** shown on the device.

PIN and MAC are stored in the config entry (viewable under `.storage/core.config_entries`). You do not need to re-enter the PIN for normal use.

---

## Configuration variables

| Key | Required | Description |
|-----|----------|-------------|
| `host` | yes | IP or hostname |
| `name` | no | Friendly name (also used as CERS device id) |
| `mac` | no | MAC for Wake-on-LAN |
| `pin` | set at pair | Stored automatically after pairing |
| `app_port` | no | Default `50202` |
| `dmr_port` | no | Default `52323` |
| `ircc_port` | no | Default `50001` |

| Device | App | DMR | IRCC |
|--------|-----|-----|------|
| BDP-S590 | `52323` | `50202` | `52323` |
| BDV-E4100 (typical) | `50202` | `52323` | `50001` |

Action list is often on **50002** (from `Ircc.xml`).

---

## Entities

| Platform | Purpose |
|----------|---------|
| `media_player` | Power, transport, volume, state polling |
| `remote` | IRCC / URL commands |

```yaml
action: remote.send_command
target:
  entity_id: remote.your_device_remote
data:
  command: BDV:Function
```

<details>
<summary><strong>Remote command reference</strong> (click to expand)</summary>

Commands come from the device `getRemoteCommandList` when available; the table below is the integration fallback / BDV-E4100 dump.

### Navigation & system

| Command | Description |
|---------|-------------|
| Confirm / Enter | OK / enter |
| Up / Down / Left / Right | D-pad |
| Home | Home menu |
| Options | Options |
| Return | Back |
| Display | Display / info |
| Power | Power |
| Dimmer | Front panel dimmer |

### Digits & volume

| Command | Description |
|---------|-------------|
| Num0–Num9 | Digits |
| VolumeUp / VolumeDown | Volume step |
| Mute | Mute |

### Transport & disc

| Command | Description |
|---------|-------------|
| Play / Pause / Stop | Transport |
| Rewind / Forward | Seek |
| Prev / Next | Chapter |
| Replay / Advance | Skip segments |
| Eject | Tray |
| TopMenu / PopUpMenu | Disc menus |
| Audio | **Disc audio track** (not RCA source) |
| SubTitle / Angle | Playback options |

### Colours & apps

| Command | Description |
|---------|-------------|
| Red / Green / Yellow / Blue | Colour keys |
| Netflix / SEN / Mode3D | Apps / modes |
| Favorites | Favorites |

### BDV home theatre (BDV-E4100 and similar)

| Command | Description |
|---------|-------------|
| **BDV:Function** | **Source cycle** (FM → TV → AUDIO → BT …) — same as SideView / IR FUNCTION |
| BDV:Bluetooth | Bluetooth-related |
| BDV:SoundMode | Sound mode |
| BDV:SoundModeUp / BDV:SoundModeDown | Sound mode step |
| BDV:SoundOutput | Speaker / TV output style |
| BDV:MusicEQ | Music EQ |
| BDV:Sleep | Sleep timer |
| BDV:KeyControl+ / BDV:KeyControl- | Karaoke key control |
| BDV:Echo | Karaoke echo |
| BDV:MicVol+ / BDV:MicVol- | Mic volume |
| BDV:SpeakerIllumination | Speaker lights |
| BDV:FootBall | Football mode |

There is **no** direct IRCC for “jump to AUDIO (RCA)”. Use `BDV:Function` with a known press count from power-on, or accept cycling.

### Generic input names (other models)

| Command | Description |
|---------|-------------|
| Input / TvInput / Media | Model-dependent input switching |

### URL-style (if advertised)

| Command | Description |
|---------|-------------|
| PartyOn / PartyOff | Party streaming |
| ZoomIn / ZoomOut | Browser zoom |
| BrowserBack / BrowserForward | Browser nav |
| BrowserBookmarkList | Bookmarks |

</details>

---

## Power on / off and status

| Action | Behaviour |
|--------|-----------|
| **Turn off** | IRCC Power |
| **Turn on** | WOL (MAC) + Power IRCC, then poll |
| **State** | DMR probe + library (poll ~15s); **off** when unreachable |
| **HA restart with device off** | Setup succeeds; entities stay **off** until the unit is reachable |

---

## Example scripts

### Test tray

```yaml
action: remote.send_command
target:
  entity_id: remote.bluray_remote
data:
  command: Eject
```

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Cannot connect at pair | Same subnet? On? Media Remote registration? |
| Failed setup on restart (old versions) | Use ≥1.2.0 — offline setup is supported |
| Can turn off but not on | Set MAC under Configure; network standby |
| FUNCTION does nothing | Use **`BDV:Function`**, not `Function` or `Audio` |
| Dump full command list | Authenticated GET to `getRemoteCommandList` with stored PIN + name as `X-CERS-DEVICE-ID` |

```yaml
logger:
  default: warning
  logs:
    custom_components.tv_sideview: debug
    sonyapilib: debug
```

---

## Credits

- [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony), [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony)
- [alexmohr/sonyapilib](https://github.com/alexmohr/sonyapilib)
- [Video & TV SideView](https://info.tvsideview.sony.net/en_ww/)

## License

Apache-2.0
