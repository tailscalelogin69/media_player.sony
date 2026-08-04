# Sony Legacy (SideView) for Home Assistant

Control **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **Video & TV SideView** app — over local HTTP / IRCC on your LAN.

This is a modern rewrite of the long-lived `media_player.sony` custom component (originally by [dilruacs](https://github.com/dilruacs/media_player.sony) / [alexmohr](https://github.com/alexmohr/media_player.sony)), updated for current Home Assistant and HACS.

---

## Important — same subnet required

**The device must be on the same subnet as Home Assistant.**  
This is a limitation of Sony’s firmware: the unit will not respond correctly to control requests from a different subnet (or from across a VPN / VLAN without proper L2 adjacency).

---

## What this is for

Sony’s newer Bravia (Android / Google TV) models are covered by the built-in **[Sony Bravia TV](https://www.home-assistant.io/integrations/braviatv/)** integration.

This integration is for the **older generation** that only spoke the SideView / IRCC HTTP API:

- Blu-ray Disc players (BDP-Sxxx, UBP-Xxxx, …)
- Home theatre systems (e.g. **BDV-E4100**, BDV-Nxxx, BDV-Exxx, …)
- Older Bravia TVs that pair with the **Video & TV SideView** mobile app
- Other Sony devices that expose IRCC + DMR on the LAN

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

## Requirements

- Home Assistant **2024.1** or newer
- Device and Home Assistant on the **same subnet**
- Device **powered on** for the initial pairing step
- Network control / Remote Start enabled on the device (wording varies by model; look under Network, Home Network, or Remote Start settings)

---

## Installation

### HACS (recommended)

1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Repository URL: `https://github.com/tailscalelogin69/media_player.sony`  
   Category: **Integration**
3. Download **Sony Legacy (SideView)**
4. **Restart** Home Assistant
5. Settings → Devices & services → **Add integration** → search **Sony Legacy**

### Manual

Copy the `custom_components/sony` folder from this repository into your Home Assistant `config/custom_components/` directory, then restart Home Assistant and add the integration from the UI.

```text
<config>/
  custom_components/
    sony/
      __init__.py
      config_flow.py
      const.py
      coordinator.py
      manifest.json
      media_player.py
      remote.py
      translations/
```

---

## Pairing

1. Power the Sony device **on**.
2. Add the integration and enter its **IP address** (static IP or DHCP reservation recommended).
3. Leave ports at the defaults unless your model needs different ones (see [Ports](#ports)).
4. The device should show a **PIN** on screen (or on its front display).
5. Enter that PIN in Home Assistant.

**Tips from upstream**

- If no PIN appears, try the flow again; on some models the first registration attempt with a blank/`0000` PIN triggers the on-screen code.
- Power-cycle the device and retry if registration fails.
- After a successful pair, the PIN is stored in the config entry — you should not need to re-enter it unless you remove the integration or reset the device’s network registration list.

---

## Ports

Most devices use these defaults:

| Setting   | Default |
|-----------|---------|
| App port  | `50202` |
| DMR port  | `52323` |
| IRCC port | `50001` |

Some Blu-ray players use **swapped** ports. Known example from upstream:

| Device   | App port | DMR port | IRCC port |
|----------|----------|----------|-----------|
| BDP-S590 | `52323`  | `50202`  | `52323`   |

This list is incomplete. If your model only works with non-default ports, open a PR or issue so others can benefit.

If setup fails with the defaults, try the alternate set above (especially for BDP / UBP players).

---

## Entities

| Platform       | Purpose |
|----------------|---------|
| `media_player` | Power, transport controls, volume |
| `remote`       | Send arbitrary IRCC commands |

Both entities share the same device entry in Home Assistant.

---

## Remote commands

Send a command:

```yaml
action: remote.send_command
target:
  entity_id: remote.your_sony_remote
data:
  command: Eject
```

`Eject` is a good “is it alive?” test on disc players and home theatre units.

### Command list

Availability depends on the device generation and category. Commands reported by upstream and the protocol library:

| Command | Description |
|---------|-------------|
| `Num0` … `Num9` | Digit keys |
| `Power` | Power toggle / on-off path used by the library |
| `Eject` | Eject disc |
| `Stop` | Stop |
| `Pause` | Pause |
| `Play` | Play |
| `Rewind` | Rewind |
| `Forward` | Fast forward |
| `Next` | Next chapter / track |
| `Prev` | Previous chapter / track |
| `PopUpMenu` | Popup menu |
| `TopMenu` | Top / disc menu |
| `Up` / `Down` / `Left` / `Right` | D-pad |
| `Confirm` | OK / Enter |
| `Options` | Options |
| `Display` | Display / info |
| `Home` | Home |
| `Return` | Return / Back |
| `Karaoke` | Karaoke |
| `Netflix` | Netflix (where supported) |
| `Mode3D` | 3D mode |
| `Favorites` | Favorites |
| `SubTitle` | Subtitles |
| `Audio` | Audio track |
| `Angle` | Angle |
| `Blue` / `Red` / `Green` / `Yellow` | Colour buttons |
| `Advance` | Advance |
| `Replay` | Replay |
| `Input` / `TvInput` / `Media` | Input / source (names vary by firmware) |
| `VolumeUp` / `VolumeDown` / `Mute` | Volume (also available on the media player) |
| `ChannelUp` / `ChannelDown` | Channel (TVs) |
| `GGuide` / `EPG` | Guide / EPG (TVs) |

If a command is not supported by your unit, the device simply ignores it.

---

## Example: BDV-E4100 — power on + analog audio (RCA) input

Goal: turn the system on and switch to the rear **L/R RCA Audio In** so you can play external audio.

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
      command: Input    # try Input, TvInput, Media, or labelled source commands
  # Optional alive check:
  - action: remote.send_command
    target:
      entity_id: remote.bdv_e4100_remote
    data:
      command: Eject
```

Exact input command strings vary by firmware. Use **Developer Tools → Actions → `remote.send_command`** and try candidates until the RCA input is selected. Once you know the working command, bind it to a dashboard button or script.

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Cannot connect | Same subnet? Device powered on? Correct IP? Firewall blocking app/DMR/IRCC ports? |
| No PIN on device | Power-cycle unit; retry setup; confirm Remote Start / network control is enabled |
| Invalid PIN | Re-read the code on the device; codes expire — start the flow again |
| Commands do nothing | Wrong ports for your model (try BDP-S590 set); device asleep without network standby; command not supported on that category |
| Works then stops after HA update | Re-download from HACS and restart; open an issue with HA version + logs |

Enable debug logging if needed:

```yaml
logger:
  default: info
  logs:
    custom_components.sony: debug
    sonyapilib: debug
```

---

## Credits

- Original component: [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony) and [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony)
- Protocol library: [alexmohr/sonyapilib](https://github.com/alexmohr/sonyapilib) (Python port based on work by Kirk Herron / SonyAPILib and others)
- Remote entity and config-flow groundwork: community contributions (including albaintor and others)

---

## License

Apache-2.0 (same as the upstream projects).
