# LVGL desktop visual simulator

This directory previews the 400×300 monochrome interface of the ESP32-S3-RLCD-4.2 on Windows and in VS Code, without connecting or flashing the board.

## Current screens

- Desktop status home screen: rebuilt pixel-for-pixel from the user-provided 400×300 music status screen reference, containing the clock, temperature and humidity, AI Agent status, Codex quota, current song, artist, playback progress, and a single lyric line; the original play-button area now shows only the current lyric.
- Computer list: rounded cards, pixel font, and compact spacing consistent with the home screen, simulating discovery of three computers, selection of the current computer, and online/offline status; the selected row uses a bold rounded border.

## Running

Run the `UI Simulator: Run` task in VS Code, or run this in a terminal:

```powershell
& .\simulator\scripts\run.ps1
```

The simulator is displayed at 2× scale; the logical resolution always stays 400×300.

The first build compiles LVGL; later builds only recompile the files that changed. To clear the CMake configuration cache, run:

```powershell
& .\simulator\scripts\configure.ps1 -Fresh
```

## Keyboard controls

| Key | Function |
| --- | --- |
| `Space` | Switch between the status home screen and the computer performance screen |
| `C` | Open the computer list |
| `↑` / `↓` | Select a computer |
| `Enter` | Confirm the current computer and return to the home screen |
| `Esc` | Return to the home screen |
| `R` | Cycle through the simulated Working/Waiting/Done states |

The computer list also supports click-to-highlight selection with the mouse. When porting to hardware, these actions map to the board's KEY button.

## Project boundaries

- `src/ui/`: portable LVGL UI code, later shared by the simulator and the ESP32 firmware.
- `src/main.c`: Windows-only SDL2 startup and keyboard simulation.
- `vendor/lvgl-9.5.0/`: locked LVGL dependency; not modified directly.
- Build output goes to `C:\ai-panel-build\simulator`, so the Windows toolchain is not affected by non-ASCII build paths.

Dynamic numbers use the LVGL built-in Latin font; the Chinese home-screen text has already been converted to 1-bit embedded bitmaps and does not depend on the host system fonts. When large amounts of dynamic Chinese text are needed later, generate a trimmed Chinese font subset to keep Flash usage under control.

## Monochrome assets

- `assets/source/music_ui_icons/`: image-generation sources for the clock, temperature/humidity, agent, playback, song, artist, network, computer, and battery icons on the current screen.
- `assets/source/icons/` and the character images: spare assets from the previous version of the screen; the current home screen does not reference them.
- `assets/generate_assets.ps1`: places the generated images, composites them with the Chinese text and layout lines into a strict 400×300 1-bit base image, and then generates the LVGL C arrays; the script does not redraw icons with drawing code.
- `src/assets/`: monochrome resources that can be linked directly into the simulator and later ported to the ESP32 firmware.

After changing an icon or the static layout, run `UI Assets: Regenerate` in VS Code, then run the simulator.

## Music data scope

The current UI uses "Chapter 7 of the Night" as NetEase Cloud Music preview data and shows only a single lyric line. The desktop Reporter later obtains the title, artist, playback state, and progress through the Windows system media session; the first version of lyrics support targets NetEase Cloud Music only, and other players do not provide lyrics yet.
