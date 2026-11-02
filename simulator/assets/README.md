# UI asset notes

The current home screen was rebuilt from the user-provided 400×300 monochrome music status screen reference. Every icon is generated separately with the built-in image generation mode and stored in `source/music_ui_icons/`; `generate_assets.py` only crops, scales, recolors, positions, and binarizes them, and does not redraw icons with drawing code.

## Current icons and generation prompts

| File | Final size | Image generation prompt summary |
| --- | ---: | --- |
| `clock.png` | 22×22 | Extract the round pixel clock at the top of the reference, keeping the octagonal outline, hour hand, minute hand, and stepped pixels. |
| `thermometer.png` | 18×32 | Generate a vertical thermometer consistent with the reference: narrow tube, center indicator line, and round base. |
| `humidity.png` | 18×29 | Generate a pixel droplet with a pointed top, round bottom, hollow center, and a small inner highlight at the lower left. |
| `agent_status.png` | 23×23 | Generate a thick outer ring, inner ring, and center point with a short wedge, used as the running-status symbol. |
| `waveform.png` | 24×16 | Generate five square-ended playback waveform bars: short, medium, long, medium, short. |
| `music_note.png` | 28×35 | Generate a bold music symbol with two filled note heads, two vertical stems, and a stepped connecting beam. |
| `artist.png` | 12×12 | Generate a small artist icon made of a square head, shoulders, and a flat base. |
| `wifi.png` | 20×14 | Generate a Wi-Fi icon made of three arcs and one solid dot. |
| `desktop.png` | 19×14 | Generate a device icon made of a rectangular monitor, short stand, and flat base. |
| `laptop.png` | 18×14 | Generate a computer-connection icon made of a screen outline, hinge, and a base with a notch in the center. |
| `battery.png` | 35×14 | Generate a battery outline, a terminal on the right, and exactly four solid charge segments. |

All prompts share these constraints: pure black 1-bit pixel graphics, a truly transparent background, stepped pixel edges preserved, no text, no grayscale, no shadows, no panels, no watermark, and no extra elements. The agent icon is recolored to white during compositing, to match the black status capsule in the reference.

## Legacy assets

`source/icons/` and `source/ciallo_maid_pixel_transparent.png` are assets from the previous version of the status home screen. The current music status home screen no longer references them, but they are kept for now so they can be used for rollback or for building other screens.

## Regenerating the LVGL assets

```bash
python3 simulator/assets/generate_assets.py
```

The generator is portable and needs Pillow plus the vendored LVGL image
converter (`pypng` and `lz4` for the converter, `pngquant` on `PATH`).

The output includes `generated/screen_base.png` and the LVGL 1-bit C arrays in `src/assets/` that can be linked directly.
