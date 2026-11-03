#!/usr/bin/env python3
# Copyright (c) 2026 Heimu. Generator: MIT; generated font data: SIL OFL 1.1.
"""Build the Syna UI CJK code point list.

The board shows Korean conversation bubbles and YouTube/NetEase track titles.
The bitmap subset is served by Unifont 16px, where Korean, Chinese and
Japanese all cost 32 bytes per glyph at 16px, so the scripts trade against
each other almost one for one. Korean is the primary script for this build:
Han and Kana are dropped and the freed budget goes to the full Hangul
syllable block plus jamo.

The previous code point list is kept as the base so that every symbol,
arrow, box drawing and punctuation glyph that was already on the device
stays on the device. Only the Han and Kana entries are removed, and Hangul
is added.

Run:  python3 generate_cjk_codepoints.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'fonts' / 'cjk-codepoints.json'
BASE = HERE / 'fonts' / 'cjk-codepoints.base.json'

# Hangul syllables (composed), jamo, and Hangul compatibility jamo.
HANGUL_SYLLABLES = range(0xAC00, 0xD7A4)
HANGUL_JAMO = range(0x1100, 0x1200)
HANGUL_COMPAT_JAMO = range(0x3130, 0x3190)
HANGUL_SYMBOLS = range(0x3200, 0x33FF)
HANGUL_EXT_B = range(0xA960, 0xA97F)
HANGUL_JAMO_EXT_B = range(0xD7B0, 0xD7FF)

# Blocks that hold Han ideographs, radicals, compatibility forms and
# ideographic marks. Kana blocks are listed separately below.
HAN_BLOCKS = (
    (0x2E80, 0x2EFF),    # CJK radicals supplement
    (0x2F00, 0x2FDF),    # Kangxi radicals
    (0x3005, 0x3007),    # ideographic iteration/closing/zero marks
    (0x3400, 0x4DBF),    # CJK unified ideographs extension A
    (0x4E00, 0x9FFF),    # CJK unified ideographs
    (0xF900, 0xFAFF),    # CJK compatibility ideographs
    (0x20000, 0x2A6DF),  # extension B
    (0x2A700, 0x2EBEF),  # extension C-F
    (0x2F800, 0x2FA1F),  # compatibility supplement
)
KANA_BLOCKS = (
    (0x3040, 0x309F),    # hiragana
    (0x30A0, 0x30FF),    # katakana
    (0x31F0, 0x31FF),    # katakana phonetic extensions
)


def in_blocks(cp: int, blocks: tuple[tuple[int, int], ...]) -> bool:
    return any(low <= cp <= high for low, high in blocks)


def main() -> None:
    base = json.loads(BASE.read_text())

    kept = [cp for cp in base if not in_blocks(cp, HAN_BLOCKS + KANA_BLOCKS)]

    # Full Korean support, added on top of the preserved base.
    hangul = set()
    for block in (
        HANGUL_SYLLABLES,
        HANGUL_JAMO,
        HANGUL_COMPAT_JAMO,
        HANGUL_SYMBOLS,
        HANGUL_EXT_B,
        HANGUL_JAMO_EXT_B,
    ):
        hangul.update(block)

    final = sorted(set(kept) | hangul)
    OUT.write_text(json.dumps(final) + '\n')

    print(f'wrote {OUT} with {len(final)} code points ({len(hangul)} Hangul added)')


if __name__ == '__main__':
    main()
