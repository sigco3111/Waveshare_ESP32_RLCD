#!/usr/bin/env python3
# Copyright (c) 2026 Heimu. MIT License.
"""Offline installer worker. stdout is JSONL; esptool runs in a child process."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import sys
import time
import uuid
import zlib

PUBLIC_HASH = 'e9bfde9cf4e31f3cdc93f544ee5112ab238c1a3a93ead49884331550092fdd71'
FLASH_SIZE = 16 * 1024 * 1024
SUPPORT = Path.home() / 'Library/Application Support/SynaInstaller'


def emit(kind, message='', **extra):
    print(json.dumps(dict(event=kind, message=message, **extra), ensure_ascii=False), flush=True)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(folder):
    result = {}
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            p = Path(base) / name
            key = p.relative_to(folder).as_posix()
            if p.is_symlink():
                target = os.readlink(p)
                if Path(target).is_absolute() or not p.resolve().is_relative_to(folder.resolve()):
                    raise ValueError('Installation content contains an unsafe link: ' + key)
                result[key] = {'link': target}
            elif p.is_file():
                result[key] = {'sha256': sha(p), 'executable': bool(p.stat().st_mode & 0o111)}
    return result


def verify_payload(resources):
    public = resources / 'public.pem'
    if public.is_symlink() or sha(public) != PUBLIC_HASH:
        raise ValueError('Release public key does not match; please re-download the official installer.')
    subprocess.run(['/usr/bin/openssl', 'dgst', '-sha256', '-verify', str(public),
                    '-signature', str(resources / 'manifest.sig'), str(resources / 'manifest.json')],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    expected = json.loads((resources / 'manifest.json').read_text())
    if not expected or inventory(resources / 'Payload') != expected:
        raise ValueError('Installation file verification failed; please re-download the official installer.')
    emit('log', 'Official release signature and all installation files verified.')


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


def esptool_command(port, args, log, timeout=600):
    if getattr(sys, 'frozen', False):
        prefix = [sys.executable, '--esptool']
    else:
        prefix = [sys.executable, str(Path(__file__).resolve()), '--esptool']
    cmd = prefix + ['--chip', 'esp32s3', '--port', port, '--baud', '460800'] + args
    # Save detailed output locally; the UI reports phases rather than thousands
    # of terminal animation lines. Never pass commands through a shell.
    result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    log.flush()
    if result.returncode:
        raise RuntimeError('Board operation failed. Check USB, release BOOT; if it cannot connect, hold BOOT, reconnect, then retry. See the install log for details.')


def flash(resources, port, mode, session):
    if not port.startswith('/dev/cu.') or not Path(port).exists():
        raise ValueError('Please select a connected board USB serial port.')
    fw = resources / 'Payload/Firmware'
    backup_file = session / 'full-flash.bin'
    with (session / 'device.log').open('w') as log:
        def tool(*args):
            esptool_command(port, list(args), log)
        emit('progress', 'Reading full board backup, about 2 minutes; do not unplug.', progress=10)
        tool('--after', 'no-reset', 'read-flash', '0', 'ALL', str(backup_file))
        if backup_file.stat().st_size != FLASH_SIZE:
            raise ValueError('Only ESP32-S3-RLCD-4.2 with 16 MB Flash is supported; nothing was written.')
        emit('progress', 'Verifying full backup; do not unplug.', progress=35)
        tool('--after', 'no-reset', 'verify-flash', '0', str(backup_file))
        (session / 'backup.json').write_text(json.dumps({'bytes': FLASH_SIZE, 'sha256': sha(backup_file),
                                                        'port': port, 'verified': True}, indent=2))
        emit('backup', 'Full backup saved and verified.', path=str(session))
        data = backup_file.read_bytes()
        app = fw / 'xiaozhi.bin'
        assets = fw / 'generated_assets.bin'
        if app.stat().st_size > 0x3f0000 or assets.stat().st_size > 0x800000:
            raise ValueError('Firmware exceeds partition capacity.')
        if mode == 'upgrade':
            offset = upgrade_offset(data, (fw / 'partition-table.bin').read_bytes())
            emit('progress', 'Upgrading firmware while preserving Wi-Fi, activation data, and device configuration.', progress=55)
            args = ['--after', 'no-reset', 'write-flash', hex(offset), str(app)]
            if data[0x800000:0x800000 + assets.stat().st_size] != assets.read_bytes():
                args += ['0x800000', str(assets)]
            tool(*args)
            preserved = session / 'preserved-config.bin'
            preserved.write_bytes(data[0x8000:0x20000])
            tool('--after', 'no-reset', 'verify-flash', '0x8000', str(preserved))
        else:
            emit('progress', 'Backup verified; initializing board.', progress=50)
            tool('--after', 'no-reset', 'erase-flash')
            tool('--after', 'no-reset', 'write-flash', '0x0', str(fw / 'bootloader.bin'),
                 '0x8000', str(fw / 'partition-table.bin'), '0xd000', str(fw / 'ota_data_initial.bin'),
                 '0x20000', str(app), '0x800000', str(assets))
        emit('progress', 'Verifying firmware and restarting board.', progress=78)
        tool('--after', 'hard-reset', 'verify-flash', hex(offset if mode == 'upgrade' else 0x20000), str(app))
    (session / 'firmware-complete.json').write_text(json.dumps({'mode': mode, 'sha256': sha(app)}))


def install_reporter(resources, destination, session):
    source = resources / 'Payload/SynaReporter.app'
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise ValueError('Reporter install location is a symbolic link; please remove that link first.')
    if destination.exists():
        info = plistlib.loads((destination / 'Contents/Info.plist').read_bytes())
        if info.get('CFBundleIdentifier') != 'local.syna.reporter':
            raise ValueError('Another application is already installed at this location; not overwritten.')
    stage = destination.parent / ('.SynaReporter-' + uuid.uuid4().hex + '.app')
    previous = session / 'Previous-SynaReporter.app'
    try:
        subprocess.run(['/usr/bin/ditto', str(source), str(stage)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(stage)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if destination.exists():
            shutil.move(str(destination), str(previous))
        try:
            stage.rename(destination)
        except Exception:
            if previous.exists():
                shutil.move(str(previous), str(destination))
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--esptool':
        import esptool
        esptool.main(sys.argv[2:])
        return
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['ports', 'verify', 'install'])
    parser.add_argument('--resources', type=Path)
    parser.add_argument('--port')
    parser.add_argument('--mode', choices=['upgrade', 'fresh', 'reporter'], default='upgrade')
    parser.add_argument('--confirm-reset', action='store_true')
    args = parser.parse_args()
    if args.action == 'ports':
        from serial.tools import list_ports
        ports = [dict(path=p.device, name=p.description) for p in list_ports.comports()
                 if p.device.startswith('/dev/cu.') and (p.vid is not None or 'usb' in p.device.lower())]
        emit('ports', ports=ports)
        return
    if args.resources is None:
        parser.error('--resources is required')
    verify_payload(args.resources)
    if args.action == 'verify':
        emit('done', 'Installation content verified.')
        return
    if args.mode == 'fresh' and not args.confirm_reset:
        raise ValueError('Fresh install must explicitly confirm erasing existing device data.')
    SUPPORT.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (SUPPORT / 'install.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        session = SUPPORT / 'Backups' / (time.strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:6])
        session.mkdir(parents=True, mode=0o700)
        emit('backup', 'Install log and backup directory created.', path=str(session))
        try:
            if args.mode != 'reporter':
                flash(args.resources, args.port or '', args.mode, session)
            emit('progress', 'Installing Reporter while preserving computer-side configuration.', progress=85)
            dest = install_reporter(args.resources, Path.home() / 'Applications/SynaReporter.app', session)
            (session / 'result.json').write_text(json.dumps({'success': True, 'app': str(dest), 'mode': args.mode}))
            emit('done', 'Installation complete.', app=str(dest), backup=str(session), progress=100)
        except Exception as exc:
            (session / 'error.txt').write_text(str(exc))
            raise


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except Exception as exc:
        emit('error', str(exc))
        sys.exit(1)
