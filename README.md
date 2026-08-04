# Video & TV SideView (Legacy API)

Home Assistant integration for **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **[Video & TV SideView](https://info.tvsideview.sony.net/en_ww/)** app — local HTTP / IRCC control on your LAN.

| | |
|--|--|
| **Domain** | `tv_sideview` |
| **UI name** | Video & TV SideView (Legacy API) |
| **Folder** | `custom_components/tv_sideview/` |
| **Version** | 1.1.0 |

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

Confirmed working class of hardware includes many BDP Blu-ray players and BDV home theatre systems listed in the original sonyapilib / media_player.sony projects.

---

## Features

- Config flow + PIN pairing (no YAML)
- Optional **MAC** at setup (auto-detected when the device reports it, or manual) for **Wake-on-LAN** power-on
- Options flow: change MAC / ports without re-pairing
- **Media player** — power, transport, volume; status via DMR + library polling
- **Remote** — IRCC commands (`Eject`, `Power`, `Input`, digits, colours, …)
- Brand icon under `brand/icon.png` (HA 2026.3+ local brands)
- HACS custom repository support

---

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet**
- Device **powered on** for initial pairing
- **Media Remote Device Registration** / network remote control enabled on the device
- For power-on from standby: **MAC address** + network standby / Remote Start if the model offers it

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
  "https://github.com/tailscalelogin69/media_player.sony/archive/refs/tags/v1.1.0.zip"
unzip -q sideview.zip
cp -a media_player.sony-1.1.0/custom_components/tv_sideview \
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
3. In HA, add the integration:
   - **IP** (static / DHCP reservation recommended)
   - **Name**
   - **MAC** (optional) — `AA:BB:CC:DD:EE:FF` for power-on; leave blank to auto-detect after pair
   - Ports — leave defaults unless your model differs
4. Enter a dummy PIN if asked first, then the **PIN shown on the TV/device** when prompted.

If no PIN appears: power-cycle, confirm Media Remote registration is enabled, retry.

After pairing, if MAC was not detected you get an optional MAC step (or set it later under **Configure** on the integration).

---

## Configuration variables

| Key | Required | Description |
|-----|----------|-------------|
| `host` | yes | IP or hostname |
| `name` | no | Friendly name |
| `mac` | no | MAC for Wake-on-LAN (`AA:BB:CC:DD:EE:FF`) |
| `app_port` | no | Default `50202` |
| `dmr_port` | no | Default `52323` |
| `ircc_port` | no | Default `50001` |

### Devices with non-default ports

This list is incomplete — open a PR if you find others.

| Device | App | DMR | IRCC |
|--------|-----|-----|------|
| BDP-S590 | `52323` | `50202` | `52323` |
| BDV-E4100 (typical) | `50202` | `52323` | `50001` |

Action list is often on **50002** (discovered automatically from `Ircc.xml`).

---

## Entities

| Platform | Purpose |
|----------|---------|
| `media_player` | Power, transport, volume, state polling |
| `remote` | Arbitrary IRCC commands |

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
| Num0–Num9 | Digits |
| Power | Power |
| Eject | Eject |
| Stop / Pause / Play | Transport |
| Rewind / Forward | Seek |
| Next / Prev | Chapter |
| Up / Down / Left / Right / Confirm | Navigation |
| Return / Home / Options / Display | Menus |
| TopMenu / PopUpMenu | Disc menus |
| Red / Green / Yellow / Blue | Colour keys |
| Audio / SubTitle / Angle | Playback options |
| Netflix / Karaoke / Mode3D | Apps / modes |
| Input / TvInput / Media | Input switching (model-dependent) |
| VolumeUp / VolumeDown / Mute | Volume (also on media_player) |
| Advance / Replay / Favorites | Misc |

Availability depends on the device.

---

## Power on / off and status

| Action | Behaviour |
|--------|-----------|
| **Turn off** | IRCC Power / library power off |
| **Turn on** | Wake-on-LAN (needs **MAC**) + Power IRCC, then poll until reachable |
| **State** | DMR HTTP probe + library power/playback (poll ~15s) |
| **Volume** | RenderingControl when the unit is awake |

Without a MAC, power-**off** and commands still work while the unit is awake; power-**on** from deep standby usually will not.

Find MAC: device network menu, router DHCP list, or `ip neigh show <ip>` while the unit is on.

---

## Example scripts

### BDV — power on, switch input, volume 27

```yaml
alias: BDV audio at 27
sequence:
  - action: media_player.turn_on
    target:
      entity_id: media_player.bluray
  - delay: "00:00:08"
  - action: remote.send_command
    target:
      entity_id: remote.bluray_remote
    data:
      command: Input
  - delay: "00:00:02"
  - action: media_player.volume_set
    target:
      entity_id: media_player.bluray
    data:
      volume_level: 0.27
mode: single
```

Try `Input`, `TvInput`, or `Media` until the rear analog RCA input is selected.

### Test IRCC with Eject

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
| Cannot connect | Same subnet? On? Correct IP/ports? Media Remote registration enabled? |
| No PIN | Power-cycle; open registration menu on device |
| Invalid PIN | Codes expire — restart setup |
| Commands work, status wrong | Update to ≥1.1.0 (DMR probe); wait one poll cycle |
| Can turn off but not on | Set **MAC** under Configure; enable network standby |
| Commands do nothing | Wrong ports for model; command not supported |

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
