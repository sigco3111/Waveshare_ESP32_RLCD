# Third-party copyright and licensing

This project is an integration and customization built on third-party components. The root MIT license covers only the original code and changes that Heimu is entitled to license,
and does not cover the original rights in third-party code and assets. Do not remove original copyright notices when modifying third-party files.

The 2026-09-16 actual build verification is in [distribution audit record](docs/THIRD_PARTY_AUDIT.md),
and the corresponding source and rebuild routes are in [third-party source notes](docs/THIRD_PARTY_SOURCES.md). Supplementary licenses are archived in
`release/licenses/windows-audit/` and `release/licenses/upstream-source-notices/`.
Updated packaging scripts carry these materials with the package; use the latest candidate package and its checksum manifest, and do not use old EXEs from before the supplementary materials.

| Component | Source and license |
| --- | --- |
| Xiaozhi ESP32 base | 78/xiaozhi-esp32, version in xiaozhi/upstream.lock; MIT, Copyright 2025 Shenzhen Xinzhi Future Technology Co., Ltd. / Project Contributors |
| LVGL | Developer obtained 9.5.0 upstream source; license copy release/licenses/lvgl-9.5.0-LICENCE.txt; MIT |
| esp_codec_dev | Component resolved during ESP-IDF build; retains that component's actual version under Apache-2.0; the old Arduino lib directory is not included in this source export |
| Other libraries and runtimes | Retain original licenses within their directories; Reporter distribution also includes Python, PyInstaller, and dependencies from requirements.txt |
| Syna UI bitmap fonts | Digits/Western text from Arimo, Chinese bitmaps from GNU Unifont 16.0.04, large boot text from Noto Sans CJK SC; used uniformly under SIL OFL 1.1; see simulator/assets/fonts/SOURCE.md and the corresponding licenses; not covered by root MIT |
| Icons and backgrounds | Confirmed by Heimu on 2026-09-13 as self-made; the original parts are licensed under this project's MIT |
| Custom wake word | Configured phrase ni hao xi na; based on Espressif ESP-SR MultiNet7; the model is not Heimu's original work; see release/licenses/esp-sr-2.4.7-LICENSE.txt |

The Xiaozhi license copy is at release/licenses/xiaozhi-MIT.txt. Original license headers, licenses, and NOTICE files in the source are retained.
Before publishing full firmware and asset packages, item-by-item distribution verification of resource sources and ESP-IDF/voice model dependencies is still required.
Do not present third-party components as Heimu's independent original work, and do not mark unverified resources as MIT.

## Font verification and replacement

The original generation script used Windows Arial / SimSun; now it uses Arimo, GNU Unifont, and Noto Sans CJK SC provided with the project.
Small-size Chinese text uses Unifont's native 16-pixel bitmap, while Western text and digits use Arimo separately; the 28-pixel boot signature keeps Noto.
Unifont's upstream font is dual-licensed; this project selects SIL OFL 1.1, with the original COPYING fully retained.
The new bitmap font is called Syna UI; its generator is MIT, the font data remains OFL, with original author information and license attached.
The old font data is kept only in local backups and must not be uploaded or used in official releases. The new Python generator does not depend on Windows fonts.

## Wake word source

The pinned Xiaozhi upstream declares a dependency on espressif/esp-sr ~2.4.7; the current board configuration uses
CONFIG_SR_MN_CN_MULTINET7_QUANT=y, with the recognition phrase ni hao xi na.
This is a recognition word configured with Espressif MultiNet7; no separately trained "ni hao xi na" model was found.
ESP-SR 2.4.7's ESPRESSIF MIT license is limited to Espressif products; it allows corresponding use and sale and must be retained.
It is not standard MIT without hardware restrictions, and must not be relabeled as this project's MIT.
Source: https://components.espressif.com/components/espressif/esp-sr/versions/2.4.7/license
The actually resolved component versions, model files, and their respective licenses must be saved during official builds; this source directory does not include the development machine's build cache or device model images.
# Windows status window additional dependencies

The Windows UI uses PySide6 Essentials 6.8.3, Shiboken6, and the accompanying Qt Core/Gui/Widgets/Network,
from https://download.qt.io/official_releases/QtForPython/ . The project's original window code uses MIT,
while these dependencies keep their own LGPL/GPL/third-party licenses and are not re-licensed by the project MIT.
Official notice: https://doc.qt.io/qtforpython-6.8/licenses.html .
The build configuration collects Python package metadata and licenses. The current Windows UI and installation have been accepted on the author's computer,
but before public distribution the Qt licenses, corresponding source acquisition method, and dynamic library replacement /
rebuild instructions must still be re-verified against the final product. Passing the tests does not mean third-party distribution materials have been verified.
