#!/usr/bin/env python3
# Copyright (c) 2026 Heimu. Generator: MIT; generated font data: SIL OFL 1.1.
"""Portable, reproducible Syna UI bitmap assets.

Python/Pillow equivalent of `generate_assets.ps1`. It composites the bundled
icon sources with the English UI labels into strict 1-bit images and then emits
the LVGL C arrays. No Windows system fonts or System.Drawing are required, so
the assets can be regenerated identically on Linux and macOS.

Requires Pillow and pypng (for the vendored LVGL image converter).
"""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GENERATED = HERE / 'generated'
ASSET_DIRS = [HERE.parent / 'src' / 'assets',
               ROOT / 'xiaozhi/overlay/main/boards/waveshare/esp32-s3-rlcd-4.2']
LVGL_CONVERTER = HERE.parent / 'vendor/lvgl-9.5.0/scripts/LVGLImage.py'
ARIMO = HERE / 'fonts/Arimo-Regular.ttf'

# Icon sources are cropped out of the bundled artwork and scaled into place.
MUSIC_ICONS = HERE / 'source/music_ui_icons'
SYNA_ICONS = HERE / 'source/syna_icons'
PERFORMANCE_SHEET = HERE / 'source/performance_icon_sheet.png'

ICONS = {
    'Clock':       (MUSIC_ICONS / 'clock.png',       (328, 296, 601, 641)),
    'Thermometer': (MUSIC_ICONS / 'thermometer.png', (280, 292, 381, 1085)),
    'Humidity':    (MUSIC_ICONS / 'humidity.png',    (120, 220, 749, 1145)),
    'AgentStatus': (MUSIC_ICONS / 'agent_status-v2.png', (280, 274, 675, 683)),
    'Waveform':    (MUSIC_ICONS / 'waveform.png',    (300, 140, 933, 709)),
    'MusicNote':   (MUSIC_ICONS / 'music_note.png',  (120, 188, 893, 1013)),
    'Artist':      (MUSIC_ICONS / 'artist.png',      (376, 308, 501, 641)),
    'Wifi':        (MUSIC_ICONS / 'wifi.png',        (248, 132, 1001, 785)),
    'Desktop':     (MUSIC_ICONS / 'desktop.png',     (176, 68, 1109, 905)),
    'Laptop':      (MUSIC_ICONS / 'laptop.png',      (128, 88, 1165, 921)),
    'Battery':     (MUSIC_ICONS / 'battery-v2.png',  (420, 160, 1165, 440)),
}

PERFORMANCE_ICONS = {
    'CpuTemperature': (205, 75, 210, 235),
    'GpuTemperature': (580, 95, 275, 220),
    'Performance':    (1045, 120, 225, 145),
    'Realtime':       (185, 430, 235, 165),
    'Host':           (600, 395, 260, 285),
    'Healthy':        (1060, 410, 185, 215),
    'Network':        (205, 745, 195, 195),
    'Upload':         (655, 750, 140, 185),
    'Download':       (1090, 750, 135, 190),
}

SYNA_ICON_SOURCES = {
    'Wallet': SYNA_ICONS / 'api_wallet.png',
    'Speech': SYNA_ICONS / 'speech_bubble.png',
    'TodoChecked': SYNA_ICONS / 'todo_checked.png',
    'TodoUnchecked': SYNA_ICONS / 'todo_unchecked.png',
}

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def font(name, size):
    """Resolve a font family without depending on Windows system fonts."""
    if name == 'Arial':
        # Arimo is the metric-compatible Arial clone bundled with the project.
        return ImageFont.truetype(str(ARIMO), size)
    if name == 'Consolas':
        for candidate in ('Consolas', 'DejaVuSansMono.ttf', 'Menlo.ttc', 'Courier New.ttf'):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        raise RuntimeError('No monospace font available for the Consolas fallback')
    raise ValueError('Unsupported font family: ' + name)


def new_canvas(width, height):
    image = Image.new('RGB', (width, height), WHITE)
    return image, ImageDraw.Draw(image)


def text_mask(canvas, text, fnt, x, y):
    """Render text as a crisp 1-bit glyph mask.

    The original generator drew with TextRenderingHint.SingleBitPerPixelGridFit,
    so glyph stems stay solid. Rendering through the antialiased path and then
    thresholding drops thin strokes (the "F" of OFFLINE lost its stem), so the
    text is rasterised in monochrome mode instead.
    """
    layer = Image.new('1', canvas.size, 0)
    ImageDraw.Draw(layer).text((x, y), text, font=fnt, fill=1, anchor='la')
    return layer


def draw_text(canvas, text, fnt, x, y, color=BLACK):
    canvas.paste(color, (0, 0), text_mask(canvas, text, fnt, x, y))


def draw_centered_text(canvas, text, fnt, bounds, color=BLACK):
    x0, y0, x1, y1 = bounds
    length = fnt.getlength(text)
    draw_text(canvas, text, fnt, x0 + ((x1 - x0) - length) / 2, y0, color)


def dashed_line(draw, x0, y0, x1, y1, dash=4, gap=3, color=BLACK):
    """Draw a dashed 1px line (mirrors the GDI Dot/Dash pen styles)."""
    total = abs(x1 - x0) + abs(y1 - y0)
    if not total:
        return
    dx = (x1 - x0) / total
    dy = (y1 - y0) / total
    position = 0
    while position < total:
        end = min(position + dash, total)
        draw.line([(x0 + dx * position, y0 + dy * position),
                   (x0 + dx * end, y0 + dy * end)], fill=color, width=1)
        position = end + gap


def crop_and_scale(path, source_box, destination, white=False):
    """Crop a source region and scale it into `destination` (x, y, w, h).

    `source_box` is (x, y, width, height) inside the source image, matching the
    Rectangle(x, y, width, height) crops used by the original generator.
    """
    image = Image.open(path).convert('RGBA')
    sx, sy, sw, sh = source_box
    image = image.crop((sx, sy, sx + sw, sy + sh))
    x, y, width, height = destination
    image = image.resize((max(1, width), max(1, height)), Image.BICUBIC)
    if white:
        # Color-key the near-white background away and paint the shape black.
        pixels = image.load()
        for py in range(image.height):
            for px in range(image.width):
                r, g, b, a = pixels[px, py]
                if min(r, g, b) >= 200:
                    pixels[px, py] = (255, 255, 255, 0)
                else:
                    pixels[px, py] = (0, 0, 0, 255)
    else:
        background = Image.new('RGBA', image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    return image.convert('RGB')


def paste(canvas, source, destination):
    """Paste an already-scaled source at the destination origin."""
    x, y = destination
    canvas.paste(source, (x, y))


def to_one_bit(image):
    """Threshold the composited image to pure black and white."""
    grey = image.convert('L')
    return grey.point(lambda value: 0 if value < 170 else 255, mode='1').convert('RGB')


def export_icon(source_path, destination_path, width, height):
    """Crop to the dark pixels of an icon and export it as a 1-bit PNG."""
    source = Image.open(source_path).convert('RGBA')
    min_x, min_y = source.width, source.height
    max_x = max_y = -1
    for y in range(0, source.height, 2):
        for x in range(0, source.width, 2):
            r, g, b, a = source.getpixel((x, y))
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if a > 32 and luma < 150:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        raise RuntimeError('No dark icon pixels found in ' + str(source_path))
    padding = max(4, int(max(max_x - min_x, max_y - min_y) * 0.035))
    crop_x = max(0, min_x - padding)
    crop_y = max(0, min_y - padding)
    crop_right = min(source.width - 1, max_x + padding)
    crop_bottom = min(source.height - 1, max_y + padding)
    image = source.crop((crop_x, crop_y, crop_right + 1, crop_bottom + 1))
    image = image.resize((width, height), Image.BICUBIC)
    background = Image.new('RGB', image.size, WHITE)
    background.paste(image, (0, 0), image)
    to_one_bit(background).save(destination_path)


def build_screen_base():
    screen, draw = new_canvas(400, 300)
    arial12, arial13, arial14 = font('Arial', 12), font('Arial', 13), font('Arial', 14)
    arial16, arial17, arial18 = font('Arial', 16), font('Arial', 17), font('Arial', 18)
    consolas11 = font('Consolas', 11)

    for box in ((6, 7, 394, 62, 11), (6, 69, 175, 251, 8),
                (178, 69, 394, 251, 8), (6, 259, 394, 294, 10)):
        draw.rounded_rectangle(box[:4], radius=box[4], outline=BLACK, width=1)
    draw.line([(189, 13), (189, 56)], fill=BLACK, width=1)
    draw.line([(288, 13), (288, 56)], fill=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Clock'], (20, 23, 22, 22)), (20, 23))
    paste(screen, crop_and_scale(*ICONS['Thermometer'], (205, 15, 18, 32)), (205, 15))
    paste(screen, crop_and_scale(*ICONS['Humidity'], (306, 16, 18, 29)), (306, 16))
    draw_text(screen, 'TEMP', arial14, 230, 15)
    draw_text(screen, 'HUMID', arial14, 331, 15)
    draw_text(screen, 'AI AGENT', arial18, 49, 82)

    draw.rounded_rectangle((46, 108, 134, 137), radius=5, fill=BLACK)
    paste(screen, crop_and_scale(*ICONS['AgentStatus'], (52, 111, 23, 23), white=True), (52, 111))
    draw_text(screen, 'WORK', arial16, 81, 112, WHITE)
    draw.line([(17, 146), (162, 146)], fill=BLACK, width=1)
    draw_text(screen, '5H QUOTA', arial13, 17, 159)
    draw_text(screen, 'WEEK QUOTA', arial13, 17, 202)
    draw.rounded_rectangle((17, 177, 163, 192), radius=4, outline=BLACK, width=1)
    draw.rounded_rectangle((17, 220, 163, 235), radius=4, outline=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Waveform'], (193, 82, 24, 16)), (193, 82))
    draw_text(screen, 'PLAYING', arial14, 223, 82)
    draw.line([(193, 103), (380, 103)], fill=BLACK, width=1)
    draw.rounded_rectangle((193, 114, 245, 169), radius=4, outline=BLACK, width=1)
    paste(screen, crop_and_scale(*ICONS['MusicNote'], (205, 124, 28, 35)), (205, 124))
    draw_text(screen, 'CHAPTER 7', arial16, 258, 115)
    paste(screen, crop_and_scale(*ICONS['Artist'], (259, 143, 12, 12)), (259, 143))
    draw_text(screen, 'JAY CHOU', arial13, 278, 141)

    dashed_line(draw, 193, 181, 380, 181, dash=1, gap=3)
    draw.ellipse((268, 178, 275, 185), fill=BLACK)
    draw_text(screen, '01:54', consolas11, 193, 188)
    draw_text(screen, '04:31', consolas11, 353, 188)
    draw_centered_text(screen, 'NIGHT FALLS', arial17, (184, 215, 388, 240))

    paste(screen, crop_and_scale(*ICONS['Wifi'], (20, 270, 20, 14)), (20, 270))
    draw_text(screen, 'WiFi LINK', arial12, 48, 270)
    paste(screen, crop_and_scale(*ICONS['Desktop'], (126, 270, 19, 14)), (126, 270))
    draw_text(screen, 'Device OK', arial12, 150, 270)
    paste(screen, crop_and_scale(*ICONS['Laptop'], (216, 270, 18, 14)), (216, 270))
    draw_text(screen, 'PC LINK', arial12, 238, 270)
    paste(screen, crop_and_scale(*ICONS['Battery'], (314, 270, 35, 14)), (314, 270))
    draw_text(screen, '87%', arial13, 358, 270)

    to_one_bit(screen).save(GENERATED / 'screen_base.png')


def build_performance_base():
    screen, draw = new_canvas(400, 300)
    arial12, arial13, arial14 = font('Arial', 12), font('Arial', 13), font('Arial', 14)
    consolas11, consolas12 = font('Consolas', 11), font('Consolas', 12)

    for box in ((6, 7, 394, 57, 11), (6, 64, 181, 254, 9),
                (188, 64, 394, 254, 9), (6, 259, 394, 294, 10)):
        draw.rounded_rectangle(box[:4], radius=box[4], outline=BLACK, width=1)
    draw.line([(156, 13), (156, 51)], fill=BLACK, width=1)
    draw.line([(262, 13), (262, 51)], fill=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Clock'], (20, 22, 22, 22)), (20, 22))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['CpuTemperature'],
                                 (166, 16, 29, 32)), (166, 16))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['GpuTemperature'],
                                 (272, 17, 38, 30)), (272, 17))
    draw_text(screen, 'CPU TEMP', arial12, 201, 16)
    draw_text(screen, 'GPU TEMP', arial12, 319, 16)

    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Performance'],
                                 (17, 75, 20, 15)), (17, 75))
    draw_text(screen, 'PERFORMANCE', arial14, 42, 72)
    draw.line([(16, 92), (170, 92)], fill=BLACK, width=1)

    draw_text(screen, 'CPU', consolas12, 17, 103)
    draw_text(screen, 'Memory', consolas12, 17, 143)
    draw_text(screen, 'GPU', consolas12, 17, 182)
    draw_text(screen, 'Disk', consolas12, 17, 222)
    for bar_y in (117, 156, 196, 235):
        draw.rounded_rectangle((16, bar_y, 170, bar_y + 13), radius=4, outline=BLACK, width=1)

    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Realtime'],
                                 (199, 74, 25, 17)), (199, 74))
    draw_text(screen, 'LIVE STATUS', arial14, 230, 72)
    draw.line([(199, 92), (383, 92)], fill=BLACK, width=1)
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Host'],
                                 (200, 106, 58, 62)), (200, 106))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Healthy'],
                                 (268, 102, 16, 18)), (268, 102))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Network'],
                                 (268, 123, 16, 17)), (268, 123))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Upload'],
                                 (269, 145, 14, 17)), (269, 145))
    paste(screen, crop_and_scale(PERFORMANCE_SHEET, PERFORMANCE_ICONS['Download'],
                                 (269, 167, 14, 17)), (269, 167))
    draw_text(screen, 'HOST OK', arial12, 291, 103)
    draw_text(screen, 'NET LATENCY', arial12, 291, 124)
    draw_text(screen, 'UPLOAD', arial12, 291, 146)
    draw_text(screen, 'DOWNLOAD', arial12, 291, 168)

    dashed_line(draw, 196, 187, 386, 187, dash=6, gap=4)
    dashed_line(draw, 196, 187, 196, 246, dash=6, gap=4)
    dashed_line(draw, 386, 187, 386, 246, dash=6, gap=4)
    dashed_line(draw, 196, 246, 386, 246, dash=6, gap=4)
    draw.line([(200, 239), (382, 239)], fill=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Wifi'], (20, 270, 20, 14)), (20, 270))
    draw_text(screen, 'WiFi LINK', arial12, 48, 270)
    paste(screen, crop_and_scale(*ICONS['Desktop'], (126, 270, 19, 14)), (126, 270))
    draw_text(screen, 'Device OK', arial12, 150, 270)
    paste(screen, crop_and_scale(*ICONS['Laptop'], (216, 270, 18, 14)), (216, 270))
    draw_text(screen, 'PC LINK', arial12, 238, 270)
    paste(screen, crop_and_scale(*ICONS['Battery'], (314, 270, 35, 14)), (314, 270))
    draw_text(screen, '87%', arial13, 358, 270)

    to_one_bit(screen).save(GENERATED / 'performance_base.png')


def build_syna_base():
    screen, draw = new_canvas(400, 300)
    arial12, arial14 = font('Arial', 12), font('Arial', 14)

    for box in ((6, 7, 394, 62, 11), (6, 69, 204, 251, 8),
                (210, 69, 394, 251, 8), (6, 259, 394, 294, 10)):
        draw.rounded_rectangle(box[:4], radius=box[4], outline=BLACK, width=1)
    draw.line([(190, 13), (190, 56)], fill=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Clock'], (20, 23, 22, 22)), (20, 23))
    draw_text(screen, 'API BALANCE', arial14, 243, 13)
    draw_text(screen, 'Syna-sama', arial14, 43, 79)
    draw.line([(17, 103), (193, 103)], fill=BLACK, width=1)
    draw_text(screen, "TODAY'S TODOS", arial14, 244, 79)
    draw.line([(221, 103), (383, 103)], fill=BLACK, width=1)

    paste(screen, crop_and_scale(*ICONS['Wifi'], (20, 270, 20, 14)), (20, 270))
    draw_text(screen, 'WiFi LINK', arial12, 48, 270)
    paste(screen, crop_and_scale(*ICONS['Desktop'], (126, 270, 19, 14)), (126, 270))
    draw_text(screen, 'Device OK', arial12, 150, 270)
    paste(screen, crop_and_scale(*ICONS['Laptop'], (216, 270, 18, 14)), (216, 270))
    draw_text(screen, 'PC LINK', arial12, 238, 270)
    paste(screen, crop_and_scale(*ICONS['Battery'], (314, 270, 35, 14)), (314, 270))
    draw_text(screen, '87%', arial12, 358, 270)

    to_one_bit(screen).save(GENERATED / 'syna_base.png')


STATUS_DEFINITIONS = {
    'status_working': 'WORKING',
    'status_waiting': 'WAITING',
    'status_done': 'DONE',
    'status_idle': 'IDLE',
    'status_offline': 'OFFLINE',
}

WIFI_STATUS_DEFINITIONS = {
    'wifi_unconfigured': 'WiFi UNSET',
    'wifi_connecting': 'WiFi BUSY',
    'wifi_provisioning': 'WiFi SETUP',
    'wifi_connected': 'WiFi LINK',
}

PC_STATUS_DEFINITIONS = {
    'pc_disconnected': 'PC OFFLINE',
    'pc_connected': 'PC LINKED',
}


def build_status_badges():
    consolas12 = font('Consolas', 12)
    for key, label in STATUS_DEFINITIONS.items():
        badge, draw = new_canvas(88, 29)
        draw.rounded_rectangle((0, 0, 88, 29), radius=5, fill=BLACK)
        paste(badge, crop_and_scale(*ICONS['AgentStatus'], (6, 3, 23, 23), white=True), (6, 3))
        draw_text(badge, label, consolas12, 35, 4, WHITE)
        to_one_bit(badge).save(GENERATED / (key + '.png'))

    for key, label in WIFI_STATUS_DEFINITIONS.items():
        badge, draw = new_canvas(78, 18)
        draw_text(badge, label, consolas12, 2, 0)
        to_one_bit(badge).save(GENERATED / (key + '.png'))

    for key, label in PC_STATUS_DEFINITIONS.items():
        badge, draw = new_canvas(76, 18)
        draw_text(badge, label, consolas12, 2, 0)
        to_one_bit(badge).save(GENERATED / (key + '.png'))


def convert(name):
    """Run the vendored LVGL image converter and mirror the result."""
    png = GENERATED / (name + '.png')
    if not png.exists():
        png = GENERATED / (name.replace('ui_', '') + '.png')
    if not LVGL_CONVERTER.exists():
        raise RuntimeError('Missing LVGL image converter: ' + str(LVGL_CONVERTER))
    command = [sys.executable, str(LVGL_CONVERTER), '--ofmt', 'C', '--cf', 'I1',
               '--background', '0xffffff', '--align', '1',
               '--output', str(ASSET_DIRS[0]), '--name', 'ui_' + name, str(png)]
    subprocess.run(command, check=True)
    produced = ASSET_DIRS[0] / ('ui_' + name + '.c')
    for directory in ASSET_DIRS[1:]:
        shutil.copy2(produced, directory / produced.name)


def main():
    GENERATED.mkdir(parents=True, exist_ok=True)
    for directory in ASSET_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    build_screen_base()
    build_performance_base()
    build_syna_base()
    build_status_badges()

    export_icon(SYNA_ICON_SOURCES['Wallet'], GENERATED / 'syna_wallet.png', 26, 26)
    export_icon(SYNA_ICON_SOURCES['Speech'], GENERATED / 'syna_speech.png', 20, 18)
    export_icon(SYNA_ICON_SOURCES['TodoChecked'], GENERATED / 'syna_todo_checked.png', 15, 15)
    export_icon(SYNA_ICON_SOURCES['TodoUnchecked'], GENERATED / 'syna_todo_unchecked.png', 15, 15)

    names = ['screen_base', 'performance_base', 'syna_base',
             'syna_wallet', 'syna_speech', 'syna_todo_checked', 'syna_todo_unchecked']
    names += list(STATUS_DEFINITIONS)
    names += list(WIFI_STATUS_DEFINITIONS)
    names += list(PC_STATUS_DEFINITIONS)
    for name in names:
        convert(name)
    print('Generated one-bit UI assets in ' + str(ASSET_DIRS[0]))


if __name__ == '__main__':
    main()
