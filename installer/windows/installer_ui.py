"""Syna Windows installer with a separate JSONL worker."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

from PySide6.QtCore import QThread, Signal, QUrl, Qt, QProcess, QProcessEnvironment
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QMainWindow,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


def existing_login_enabled() -> bool:
    if os.name != 'nt':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            value, _ = winreg.QueryValueEx(key, 'SynaReporter')
        if not value:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run') as key:
                approval, _ = winreg.QueryValueEx(key, 'SynaReporter')
            if isinstance(approval, bytes) and approval and approval[0] in (3, 7):
                return False
        except FileNotFoundError:
            pass
        return True
    except OSError:
        return False


def installed_reporter() -> Path | None:
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        base = os.environ.get(variable)
        if base:
            path = Path(base) / 'Syna Reporter' / 'SynaReporter.exe'
            if path.is_file():
                return path
    return None


def enumerate_ports() -> list[dict]:
    # Enumeration does not open a serial port or reset a connected board.
    command = (
        '[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); '
        "$ErrorActionPreference='Stop'; "
        "Get-CimInstance Win32_PnPEntity -Filter \"Name LIKE '%(COM%'\" | "
        'Select-Object Name,PNPDeviceID | ConvertTo-Json -Compress'
    )
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
        capture_output=True, encoding='utf-8-sig', errors='replace', timeout=20,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True,
    )
    rows = json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    ports = {}
    for row in rows:
        name = str(row.get('Name') or '')
        match = re.search(r'\((COM\d+)\)', name, re.I)
        if match:
            port = match[1].upper()
            identifier = str(row.get('PNPDeviceID') or '').upper()
            ports[port] = {'port': port, 'name': name,
                           'esp_usb': 'VID_303A' in identifier,
                           'usb': identifier.startswith('USB\\')}
    return sorted(ports.values(), key=lambda p: (not p['esp_usb'], not p['usb'], int(p['port'][3:])))


class PortScan(QThread):
    found = Signal(list)
    failed = Signal(str)

    def run(self):
        try:
            self.found.emit(enumerate_ports())
        except Exception as error:
            self.failed.emit('Failed to read device list: ' + type(error).__name__)


class InstallerWindow(QMainWindow):
    def __init__(self, scan=True):
        super().__init__()
        self.scanner = None
        self.process = None
        self.backup_path = None
        self.payload_ready = False
        self.output_buffer = b''
        self.completed = False
        self.setWindowTitle('Syna Installer')
        self.resize(720, 740)
        self.setMinimumSize(520, 440)
        self.setFont(QFont('Microsoft YaHei UI', 10))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.setCentralWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(14)
        title = QLabel('Syna')
        title.setObjectName('title')
        layout.addWidget(title)
        layout.addWidget(QLabel('Firmware and Reporter in one install · v1.0.0 · Windows'))
        self.preview = QLabel('Choose a mode, then click Install to begin; full backup and verification run before flashing.')
        self.preview.setObjectName('preview')
        self.preview.setWordWrap(True)
        layout.addWidget(self.preview)
        self.mode = QComboBox()
        self.mode.addItems(['Preserve-config upgrade (recommended)', 'Fresh install / replace other firmware', 'Reporter only'])
        layout.addLayout(self.row(QLabel('Install mode'), self.mode))
        self.ports = QComboBox()
        self.ports.setMinimumContentsLength(24)
        self.ports.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.ports.addItem('No device detected yet', None)
        self.refresh = QPushButton('Refresh devices')
        self.refresh.clicked.connect(self.refresh_ports)
        layout.addLayout(self.row(QLabel('Board'), self.ports, self.refresh))
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.reset = QCheckBox('I understand that fresh install erases existing board data')
        layout.addWidget(self.reset)
        self.login = QCheckBox('Enable Reporter login auto-start after install')
        self.login.setChecked(existing_login_enabled())
        layout.addWidget(self.login)
        self.start = QPushButton('Start install')
        self.start.setEnabled(False)
        self.start.clicked.connect(self.begin_install)
        layout.addWidget(self.start, alignment=Qt.AlignLeft)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel('Choose an install mode, connect the board, then refresh devices.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont('Consolas', 10))
        self.log.setMinimumHeight(125)
        self.log.setMaximumBlockCount(300)
        layout.addWidget(self.log, stretch=1)
        self.backups = QPushButton('View backups and logs')
        self.backups.setEnabled(False)
        self.backups.clicked.connect(self.open_backups)
        self.launch = QPushButton('Open Reporter')
        self.reporter_path = installed_reporter()
        self.launch.setEnabled(self.reporter_path is not None)
        self.launch.clicked.connect(self.open_reporter)
        layout.addLayout(self.row(self.backups, self.launch))
        author = QLabel('Heimu · Bilibili UID 386856267 · QQ 3091479711')
        author.setObjectName('author')
        layout.addWidget(author)
        self.setStyleSheet('''
            QMainWindow, QScrollArea, QWidget { background: #f5f5f7; color: #202124; }
            QLabel#title { font-size: 30px; font-weight: 600; }
            QLabel#preview { background: #eaf2ff; color: #285581; padding: 10px; border-radius: 6px; }
            QLabel#author { color: #777; font-size: 11px; }
            QComboBox, QPushButton { min-height: 28px; padding: 3px 10px; }
            QComboBox, QPlainTextEdit { background: white; border: 1px solid #c9cbd0; border-radius: 4px; }
            QPushButton { background: #fff; border: 1px solid #bfc2c7; border-radius: 5px; }
            QPushButton:disabled { color: #8b8b8b; background: #ececee; border-color: #d8d8dc; }
            QPushButton:hover:enabled { background: #eaf2ff; }
            QProgressBar { border: 1px solid #d1d1d6; border-radius: 4px; text-align: center; min-height: 15px; }
            QProgressBar::chunk { background: #3a82d9; }
        ''')
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.reset.toggled.connect(self.update_controls)
        self.ports.currentIndexChanged.connect(self.update_controls)
        try:
            from worker import verify_payload
            verify_payload()
            self.payload_ready = True
        except Exception as error:
            self.preview.setText('Installation files not ready: ' + str(error))
        self.mode_changed()
        area = self.screen().availableGeometry()
        self.resize(min(720, area.width()-40), min(740, area.height()-60))
        if scan:
            self.refresh_ports()

    @staticmethod
    def row(*widgets):
        row = QHBoxLayout()
        row.setSpacing(12)
        for widget in widgets:
            row.addWidget(widget, 1 if isinstance(widget, QComboBox) else 0)
        return row

    def mode_changed(self):
        mode = self.mode.currentIndex()
        self.reset.setVisible(mode == 1)
        self.reset.setChecked(False)
        self.ports.setEnabled(mode != 2)
        self.hint.setText([
            'Only for Waveshare ESP32-S3-RLCD-4.2 (16 MB). Backup runs automatically before upgrade; Wi-Fi and computer binding are preserved.',
            'Fresh install erases existing board data; a full backup and verification must complete before the real install.',
            'Installs only the computer-side Reporter, preserving existing settings; no board connection needed.',
        ][mode])
        self.update_controls()

    def update_controls(self, *_):
        idle = self.process is None
        mode = self.mode.currentIndex()
        self.mode.setEnabled(idle)
        self.login.setEnabled(idle)
        self.reset.setEnabled(idle)
        self.ports.setEnabled(idle and mode != 2)
        self.refresh.setEnabled(idle and self.scanner is None and mode != 2)
        self.launch.setEnabled(idle and self.reporter_path is not None)
        self.start.setEnabled(idle and self.scanner is None and self.payload_ready and
                              (mode == 2 or bool(self.ports.currentData())) and
                              (mode != 1 or self.reset.isChecked()))

    def begin_install(self):
        if not self.start.isEnabled():
            return
        self.completed = False
        self.output_buffer = b''
        self.progress.setValue(0)
        self.log.clear()
        self.status.setText('Verifying installation files...')
        process = QProcess(self)
        self.process = process
        env = QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUTF8', '1')
        process.setProcessEnvironment(env)
        process.readyReadStandardOutput.connect(self.read_output)
        process.readyReadStandardError.connect(lambda: self.log.appendPlainText(
            bytes(process.readAllStandardError()).decode('utf-8', errors='replace')))
        process.finished.connect(self.install_finished)
        process.errorOccurred.connect(self.process_error)
        mode = ['upgrade', 'fresh', 'reporter'][self.mode.currentIndex()]
        args = [str(Path(__file__).with_name('worker.py')), '--mode', mode,
                '--login', 'on' if self.login.isChecked() else 'off']
        if mode != 'reporter':
            args += ['--port', self.ports.currentData()]
        if mode == 'fresh' and self.reset.isChecked():
            args += ['--confirm-reset']
        self.update_controls()
        if getattr(sys, 'frozen', False):
            resources = Path(__file__).resolve().parent
            process.start(str(resources/'SynaInstallerWorker.exe'),
                          args[1:] + ['--resources', str(resources)])
        else:
            process.start(str(Path(sys.executable).with_name('python.exe')), args)

    def read_output(self):
        self.output_buffer += bytes(self.process.readAllStandardOutput())
        while b'\n' in self.output_buffer:
            line, self.output_buffer = self.output_buffer.split(b'\n', 1)
            try:
                self.handle_event(json.loads(line))
            except (ValueError, TypeError, KeyError):
                self.log.appendPlainText(line.decode('utf-8', errors='replace'))

    def handle_event(self, event):
        message = event.get('message', '')
        if message:
            self.log.appendPlainText(message)
            self.status.setText(message)
        if event.get('event') == 'backup':
            self.backup_path = Path(event['path'])
            self.backups.setEnabled(True)
        if event.get('event') == 'reporter_installed':
            self.reporter_path = Path(event['app'])
        if event.get('event') == 'done':
            self.completed = True
        elif 'progress' in event:
            self.progress.setValue(min(99, max(0, int(event['progress']))))

    def process_error(self, error):
        if error == QProcess.FailedToStart:
            self.status.setText('Could not start installer: ' + self.process.errorString())
            self.install_finished(-1, QProcess.CrashExit)

    def install_finished(self, code, status):
        if self.process is None:
            return
        self.read_output()
        success = code == 0 and status == QProcess.NormalExit and self.completed
        self.process.deleteLater()
        self.process = None
        if success:
            self.progress.setValue(100)
            self.status.setText('Installation complete and verified. Click "Open Reporter".')
        else:
            self.status.setText('Installation did not complete. See the errors and backup log below.')
            self.log.appendPlainText(f'Installer exit code: {code}; do not delete backups.')
        self.update_controls()

    def open_backups(self):
        if self.backup_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.backup_path)))

    def refresh_ports(self):
        if self.scanner is not None or self.process is not None:
            return
        self.refresh.setEnabled(False)
        self.status.setText('Detecting serial port devices...')
        self.scanner = PortScan(self)
        self.update_controls()
        self.scanner.found.connect(self.show_ports)
        self.scanner.failed.connect(self.scan_failed)
        self.scanner.finished.connect(self.scan_finished)
        self.scanner.start()

    def show_ports(self, ports):
        selected = self.ports.currentData()
        self.ports.clear()
        for item in ports:
            self.ports.addItem(item['name'], item['port'])
        if not ports:
            self.ports.addItem('No serial port devices detected', None)
        index = self.ports.findData(selected) if selected else -1
        if index >= 0:
            self.ports.setCurrentIndex(index)
        self.status.setText(f'Detected {len(ports)} serial ports; board model and capacity are verified before install.' if ports else 'No device detected; check the USB cable and refresh.')
        self.log.appendPlainText(self.status.text())
        for item in ports:
            self.log.appendPlainText(item['name'])

    def scan_failed(self, message):
        self.status.setText(message)
        self.log.appendPlainText(message)

    def scan_finished(self):
        scanner = self.scanner
        self.scanner = None
        scanner.deleteLater()
        self.update_controls()

    def open_reporter(self):
        if self.reporter_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.reporter_path)))

    def closeEvent(self, event):
        if self.scanner is not None or self.process is not None:
            self.status.setText('Device detection or installation is still running; please wait before closing.')
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        window = InstallerWindow(scan=False)
        resources = Path(__file__).resolve().parent
        worker = resources/'SynaInstallerWorker.exe'
        results = {'payload': window.payload_ready}
        for name, args in [('backend', ['--verify-only', '--resources', str(resources)]),
                           ('esptool', ['--esptool', 'version'])]:
            result = subprocess.run([str(worker), *args], capture_output=True,
                                    timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
            results[name] = result.returncode == 0
            results[name+'_output'] = result.stdout.decode('utf-8', errors='replace') + result.stderr.decode('utf-8', errors='replace')
        window.mode.setCurrentIndex(2)
        results['reporter_mode'] = window.start.isEnabled()
        # Exercise the same byte parser and completion gate as real installation.
        process = QProcess(window)
        window.process = process
        process.start(str(worker), ['--protocol-test'])
        finished = process.waitForFinished(90000)
        if finished:
            window.install_finished(process.exitCode(), process.exitStatus())
        results['chinese_protocol'] = (finished and window.completed and
            window.progress.value() == 100 and 'Verifying localized path: Syna 🐱' in window.log.toPlainText())
        Path(sys.argv[2]).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        return 0 if all(results[key] for key in ('payload', 'backend', 'esptool', 'reporter_mode', 'chinese_protocol')) else 1
    window = InstallerWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
