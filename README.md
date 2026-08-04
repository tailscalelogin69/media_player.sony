# Video & TV SideView (Legacy API) for Home Assistant

Control **older Sony TVs, Blu-ray players, and home theatre systems** that work with the classic **[Video & TV SideView](https://info.tvsideview.sony.net/en_ww/)** app — over local HTTP / IRCC on your LAN.

| | |
|--|--|
| **Domain** | `tv_sideview` |
| **UI name** | Video & TV SideView (Legacy API) |
| **Folder** | `custom_components/tv_sideview/` |
| **HACS** | Custom repository (this repo) |

Search in **Add integration** for: **SideView**, **Video**, or **TV SideView**.  
This does **not** hide official Sony Bravia, PlayStation Network, Songpal, or other integrations.

---

## Important — same subnet required

The device must be on the **same subnet** as Home Assistant (Sony firmware limitation).

---

## What this is for

| Use this | Use official HA instead |
|----------|-------------------------|
| Blu-ray (BDP / UBP …) | **Sony Bravia TV** — Android / Google TV |
| Home theatre (**BDV-E4100**, BDV-Nxxx …) | **Songpal** — newer audio products |
| Older TVs that only speak SideView | **PlayStation Network** / console integrations |

If the SideView phone app can control it on your LAN, this integration almost certainly can too.

---

## Clean install (required if you tried earlier versions)

Earlier builds used domains `sony` / `sony_sideview` and HACS sometimes installed into a broken path like `custom_components/sony/_sideview/`. That will **not** load.

On the HA host:

```bash
# Remove ALL old copies
rm -rf /config/custom_components/sony
rm -rf /config/custom_components/sony_sideview
rm -rf /config/custom_components/tv_sideview
```

In **HACS → Integrations**: remove any old “Sony” / “SideView” entry for this repo entirely.

Then:

1. HACS → Integrations → ⋮ → **Custom repositories**  
   URL: `https://github.com/tailscalelogin69/media_player.sony`  
   Category: **Integration**
2. Download **Video & TV SideView (Legacy API)** (v1.2.0+)
3. Confirm the folder is exactly:
   ```text
   /config/custom_components/tv_sideview/manifest.json
   ```
   (not `sony/`, not `sony/_sideview/`)
4. **Restart** Home Assistant
5. Settings → Devices & services → **Add integration** → search **`SideView`**

---

## Features

- Config flow + PIN pairing (no YAML)
- `media_player` — power, transport, volume
- `remote` — IRCC commands (`Eject`, `Power`, `Input`, …)
- Local polling only
- Brand icons in `brand/` (HA 2026.3+ local brands; optional CDN later)

---

## Ports

| Setting | Default |
|---------|---------|
| App | `50202` |
| DMR | `52323` |
| IRCC | `50001` |

| Device | App | DMR | IRCC |
|--------|-----|-----|------|
| BDP-S590 | 52323 | 50202 | 52323 |

---

## Example: BDV-E4100

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
    data:
      command: Eject
```

---

## Changes from upstream (dilruacs / alexmohr)

- Config flow instead of YAML + Configurator
- `MediaPlayerEntityFeature`, async executor I/O, `DataUpdateCoordinator`
- Device registry, translations, HACS
- Domain **`tv_sideview`** so it does not collide with official Sony entries
- Combined media player + remote from both upstream lines
- Still uses `sonyapilib==0.5.0` for the SideView protocol

---

## Credits

- [dilruacs/media_player.sony](https://github.com/dilruacs/media_player.sony), [alexmohr/media_player.sony](https://github.com/alexmohr/media_player.sony)
- [alexmohr/sonyapilib](https://github.com/alexmohr/sonyapilib)
- SideView product info: [info.tvsideview.sony.net](https://info.tvsideview.sony.net/en_ww/)

## License

Apache-2.0
