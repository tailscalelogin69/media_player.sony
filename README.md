# Video & TV SideView (Legacy API)

Home Assistant integration for **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **[Video & TV SideView](https://info.tvsideview.sony.net/en_ww/)** app — local HTTP / IRCC control on your LAN.

| | |
|--|--|
| **Domain** | `tv_sideview` |
| **UI name** | Video & TV SideView (Legacy API) |
| **Folder** | `custom_components/tv_sideview/` |

Search **Add integration** for **SideView**, **Video**, or **TV SideView**.  
Does **not** replace or hide official Sony Bravia, PlayStation Network, Songpal, or other integrations.

---

## Important

The device must be on the **same subnet** as Home Assistant (Sony firmware limitation).

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

- Config flow with PIN pairing (no YAML)
- **Media player** — power, play / pause / stop, next / previous, volume
- **Remote** — IRCC commands (`Eject`, `Power`, `Input`, digits, colours, …)
- Local polling only (no cloud)
- HACS custom repository support

Modern rewrite of the classic `media_player.sony` projects ([dilruacs](https://github.com/dilruacs/media_player.sony) / [alexmohr](https://github.com/alexmohr/media_player.sony)), updated for current Home Assistant standards (config entries, async I/O, coordinator, device registry).

---

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet**
- Device **powered on** for initial pairing
- Network control / Remote Start enabled on the device

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
  "https://github.com/tailscalelogin69/media_player.sony/archive/refs/tags/v1.0.0.zip"
unzip -q sideview.zip
cp -a media_player.sony-1.0.0/custom_components/tv_sideview \
  /config/custom_components/
```

Restart Home Assistant, then add the integration from the UI.

Confirm the path is:

```text
/config/custom_components/tv_sideview/manifest.json
```

---

## Pairing

1. Power the device **on**.
2. Add the integration and enter its IP (static IP / DHCP reservation recommended).
3. Leave ports at defaults unless your model needs different ones (see below).
4. Enter the **PIN** shown on the device.

If no PIN appears, power-cycle the unit and retry.

---

## Ports

| Setting | Default |
|---------|---------|
| App | `50202` |
| DMR | `52323` |
| IRCC | `50001` |

| Device | App | DMR | IRCC |
|--------|-----|-----|------|
| BDP-S590 | `52323` | `50202` | `52323` |

---

## Entities

| Platform | Purpose |
|----------|---------|
| `media_player` | Power, transport, volume |
| `remote` | Arbitrary IRCC commands |

### Remote commands

```yaml
action: remote.send_command
target:
  entity_id: remote.your_device_remote
data:
  command: Eject
```

Common commands: `Power`, `Eject`, `Play`, `Pause`, `Stop`, `Rewind`, `Forward`, `Next`, `Prev`, `Up`, `Down`, `Left`, `Right`, `Confirm`, `Return`, `Home`, `Options`, `Display`, `TopMenu`, `PopUpMenu`, `Red`, `Green`, `Yellow`, `Blue`, `Num0`–`Num9`, `Audio`, `SubTitle`, `Input`, `TvInput`, `Media`, `VolumeUp`, `VolumeDown`, `Mute`.

Availability depends on the device.

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
| Cannot connect | Same subnet? Powered on? Correct IP / ports? |
| No PIN | Power-cycle; enable Remote Start / network control |
| Invalid PIN | Codes expire — restart the setup flow |
| Commands do nothing | Wrong ports for model; command not supported |

```yaml
logger:
  default: info
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
