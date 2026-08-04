# Sony Legacy (SideView) for Home Assistant

Control **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **Video & TV SideView** app — over local HTTP / IRCC on your LAN.

This is a modern rewrite of the long-lived `media_player.sony` custom component (originally by dilruacs / alexmohr), updated for current Home Assistant and HACS.

---

## What this is for

Sony’s newer Bravia (Android / Google TV) models are covered by the built-in **Sony Bravia TV** integration.  
This integration is for the **older generation** that only spoke the SideView / IRCC HTTP API:

- Blu-ray Disc players (BDP-Sxxx, UBP-Xxxx, …)
- Home theatre systems (e.g. **BDV-E4100**, BDV-Nxxx, …)
- Older Bravia TVs that pair with the SideView mobile app
- Other Sony devices that expose IRCC + DMR on the LAN

If the official SideView app can control it on your network, this integration almost certainly can too.

---

## Features

- **Config flow** — UI setup with PIN pairing (no YAML required)
- **Media player** entity — power, play / pause / stop, next / previous, volume step / set / mute
- **Remote** entity — send any IRCC command (`Eject`, `Power`, `Input`, coloured buttons, digits, …)
- Local polling only (no cloud)
- HACS-ready

---

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet** (Sony firmware limitation)
- Device powered on for the initial pairing step
- Network / Remote Start enabled on the device (wording varies by model)

---

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Repository: `https://github.com/tailscalelogin69/media_player.sony`  
   Category: **Integration**
3. Download **Sony Legacy (SideView)**
4. Restart Home Assistant
5. Settings → Devices & services → Add integration → search **Sony Legacy**

### Manual

```bash
# inside your Home Assistant config folder
mkdir -p custom_components
# copy the custom_components/sony folder from this repo into custom_components/
```

Restart Home Assistant, then add the integration from the UI.

---

## Pairing

1. Power the Sony device **on**.
2. Add the integration and enter its IP address (static IP / DHCP reservation recommended).
3. Leave ports at the defaults unless your model needs different ones (see below).
4. The device should show a **PIN** on screen (or on its display).
5. Enter that PIN in Home Assistant.

If no PIN appears, try entering `0000` first to force the registration prompt, or power-cycle the device and retry.

---

## Ports

Most devices use the defaults:

| Setting   | Default |
|-----------|---------|
| App port  | `50202` |
| DMR port  | `52323` |
| IRCC port | `50001` |

Some Blu-ray players use swapped ports, for example:

| Device   | App   | DMR   | IRCC  |
|----------|-------|-------|-------|
| BDP-S590 | 52323 | 50202 | 52323 |

If setup fails with defaults, try the alternate set above.

---

## Entities

| Entity        | Purpose |
|---------------|---------|
| `media_player.*` | Power, transport controls, volume |
| `remote.*`       | Send arbitrary IRCC commands |

### Useful remote commands

```yaml
service: remote.send_command
target:
  entity_id: remote.your_sony_remote
data:
  command: Eject          # good “is it alive?” test
```

Other common commands (availability depends on the device):

`Power`, `Play`, `Pause`, `Stop`, `Eject`, `Rewind`, `Forward`, `Next`, `Prev`, `Up`, `Down`, `Left`, `Right`, `Confirm`, `Return`, `Home`, `Options`, `Display`, `TopMenu`, `PopUpMenu`, `Red`, `Green`, `Yellow`, `Blue`, `Num0`–`Num9`, `Audio`, `SubTitle`, `Input`, `VolumeUp`, `VolumeDown`, `Mute`

---

## Example: BDV-E4100 — power on + analog audio input

Typical automation / script pattern:

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
      command: Input        # or the specific input command your unit accepts
  # Optionally verify with:
  - action: remote.send_command
    target:
      entity_id: remote.bdv_e4100_remote
    data:
      command: Eject
```

Exact input-name strings vary by firmware. Use **Developer Tools → Actions → `remote.send_command`** and try `Input`, `TvInput`, `Media`, or the labelled source buttons until the rear L/R RCA (Audio In) is selected. Once you know the working command, put it in a script or dashboard button.

---

## Credits

- Original component: [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony) and [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony)
- Protocol library: [alexmohr/sonyapilib](https://github.com/alexmohr/sonyapilib) (based on work by Kirk Herron and others)
- Remote entity contributions from the community (albaintor and others)

---

## License

Apache-2.0 (same as the upstream projects).
