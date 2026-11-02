# Copyright (c) 2026 Syna contributors. MIT.
# Partition validation ported unchanged from installer/macos/worker.py.
import hashlib
import struct
import zlib
FLASH_SIZE = 16 * 1024 * 1024

def parse_partitions(data):
    entries = []
    digest = hashlib.md5()
    checked = False
    for pos in range(0, len(data), 32):
        row = data[pos:pos + 32]
        if row == b'\xff' * 32:
            if not checked:
                raise ValueError('Partition table is missing its checksum record.')
            return entries
        if len(row) != 32:
            break
        if row[:2] == b'\xeb\xeb':
            if row[16:] != digest.digest():
                raise ValueError('Device partition table checksum failed.')
            checked = True
            continue
        magic, kind, subtype, offset, size, label, flags = struct.unpack('<HBBII16sI', row)
        if magic != 0x50aa or offset + size > FLASH_SIZE:
            raise ValueError('Device partition table is not supported; use fresh install mode.')
        digest.update(row)
        entries.append((kind, subtype, offset, size, label.rstrip(b'\0'), flags))
    raise ValueError('Partition table is incomplete.')

def upgrade_offset(backup, partition_image):
    actual = parse_partitions(backup[0x8000:0x9000])
    if actual != parse_partitions(partition_image):
        raise ValueError('Existing partitions are incompatible; nothing was written. Use fresh install for other firmware.')
    choices = []
    for pos in (0xd000, 0xe000):
        row = backup[pos:pos + 32]
        seq, _, state, crc = struct.unpack('<I20sII', row)
        if seq == 0xffffffff or crc != zlib.crc32(row[:4], 0xffffffff) or state in (3, 4):
            continue
        if state == 1:
            raise ValueError('Device has not confirmed the previous OTA update; start the device normally before upgrading.')
        choices.append(seq)
    if choices:
        slot = (max(choices) - 1) % 2
    elif backup[0xd000:0xf000] == b'\xff' * 0x2000:
        slot = 0
    else:
        raise ValueError('Could not reliably determine the boot partition; firmware was not written.')
    entry = next(x for x in actual if x[0] == 0 and x[1] == 0x10 + slot)
    offset, size = entry[2:4]
    app = backup[offset:offset + size]
    if app[0] != 0xe9 or b'esp32-s3-rlcd-4.2' not in app:
        raise ValueError('This board model was not recognized; nothing was written. Use fresh install mode on first use.')
    return offset
