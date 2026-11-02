# Copyright (c) 2026 Heimu. SPDX-License-Identifier: MIT
"""Windows status window, ported from native_ui.swift without changing its layout.

Qt coordinates are device-independent pixels. The backend stays in a separate
worker process; UI polling never blocks the event loop or stops an external worker.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from PySide6.QtCore import Qt, QTimer, QProcess, QUrl, QLockFile
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QAction
from PySide6.QtNetwork import QLocalServer, QLocalSocket, QNetworkAccessManager, QNetworkRequest, QNetworkProxy, QNetworkReply
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QCheckBox, QMessageBox, QSystemTrayIcon, QMenu, QScrollArea, QVBoxLayout, QStyle
from PySide6.QtGui import QDesktopServices
from platform_support import application_data_dir

REPOSITORY = 'https://github.com/heimumumu/Waveshare_ESP32_RLCD'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'


def launch_command():
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    executable = Path(sys.executable)
    if os.name == 'nt' and executable.with_name('pythonw.exe').exists():
        executable = executable.with_name('pythonw.exe')
    return [str(executable), str(Path(__file__).with_name('reporter.py'))]


def login_enabled():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, 'SynaReporter')
        return value == subprocess.list2cmdline(launch_command())
    except FileNotFoundError:
        return False


def set_login(enabled):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, 'SynaReporter', 0, winreg.REG_SZ, subprocess.list2cmdline(launch_command()))
        else:
            try:
                winreg.DeleteValue(key, 'SynaReporter')
            except FileNotFoundError:
                pass


def number(value, suffix=''):
    return f'{value:.1f}{suffix}' if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else '—'


def rate(value):
    if number(value) == '—':
        return '—'
    value = max(0, value)
    return f'{value / 1048576:.2f} MB/s' if value >= 1048576 else f'{value / 1024:.1f} KB/s'


class ElidedLabel(QLabel):
    """Preserve full accessible text and tooltip while clipping long song names."""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        painter.setFont(self.font())
        painter.drawText(self.rect(), int(self.alignment()), self.fontMetrics().elidedText(self.text(), Qt.ElideRight, self.width()))


class ReporterWindow(QWidget):
    def __init__(self, *, preview=False):
        super().__init__()
        self.preview = preview
        self.worker = None
        self.wanted = True
        self.quitting = False
        self.first_poll = True
        self.polling = False
        self.restart_delay = 1000
        self.labels = {}
        self.setWindowTitle('Syna Reporter')
        self.setStyleSheet('QWidget {background:#f2f5f2;color:#21333b;} QPushButton {background:white;border:1px solid #d7dfd9;border-radius:7px;padding:5px;} QPushButton:hover {background:#e0eee6;} QPushButton:disabled {color:#89958f;} QCheckBox {spacing:10px;}')
        font = QFont()
        font.setFamilies(['Segoe UI', 'Microsoft YaHei UI', 'Microsoft YaHei'])
        self.setFont(font)
        # Keep the original design dimensions; scroll on smaller work areas so
        # high DPI never leaves service or startup controls below the screen.
        self.content = QWidget()
        self.content.setFixedSize(760, 750)
        self.scroll = QScrollArea(self)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setWidget(self.content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        self.setMinimumSize(320, 240)
        self.fit_to_screen()
        self.build_window()
        self.network = QNetworkAccessManager(self)
        self.network.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.tray = QSystemTrayIcon(self.make_icon(), self)
        self.tray.setToolTip('Syna Reporter · Double-click to show the status window')
        menu = QMenu(self)
        menu.addAction('Show Status Window', self.reveal)
        menu.addAction('About Author', self.about)
        menu.addSeparator()
        menu.addAction('Quit Syna Reporter', self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.reveal() if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger) else None)
        self.setWindowIcon(self.make_icon())
        if not preview:
            self.tray.show()
            self.refresh_login()
            self.timer.start(1000)
            self.refresh()

    @staticmethod
    def make_icon():
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor('#1f755c'))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 32, 32, 8, 8)
        p.setPen(Qt.white)
        p.setFont(QFont('Segoe UI', 19, QFont.Bold))
        p.drawText(pix.rect(), Qt.AlignCenter, 'S')
        p.end()
        return QIcon(pix)

    def fit_to_screen(self):
        area = self.screen().availableGeometry()
        height = min(750, max(240, area.height() - 64))
        width = 760 + (self.style().pixelMetric(QStyle.PM_ScrollBarExtent) if height < 750 else 0)
        self.resize(min(width, max(320, area.width() - 32)), height)

    def text(self, parent, value, x, y, w, h, size=14, bold=False, muted=False, key=None):
        label = ElidedLabel(value, self.content if parent is self else parent)
        label.setGeometry(x, y, w, h)
        font = QFont('Segoe UI')
        font.setFamilies(['Segoe UI', 'Microsoft YaHei UI', 'Microsoft YaHei'])
        font.setPixelSize(size)
        font.setWeight(QFont.DemiBold if bold else QFont.Normal)
        label.setFont(font)
        label.setStyleSheet('background:transparent;color:' + ('#6e7d80' if muted else '#21333b') + ';')
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if key:
            self.labels[key] = label
        return label

    def card(self, x, y, w, h, tint='white'):
        card = QWidget(self.content)
        card.setGeometry(x, y, w, h)
        card.setStyleSheet(f'background:{tint};border-radius:16px;')
        return card

    def button(self, title, x, w, action, y=626):
        button = QPushButton(title, self.content)
        button.setGeometry(x, y, w, 34)
        button.clicked.connect(action)
        return button

    def build_window(self):
        self.text(self, 'Syna Reporter', 28, 24, 470, 38, 29, True)
        self.text(self, 'Your computer and Syna, at a glance.', 29, 64, 650, 23, 13, muted=True)
        self.text(self, 'WINDOWS Status Center', 570, 34, 162, 23, 11, True, True).setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        banner = self.card(28, 100, 704, 96, '#e0f0e8')
        self.text(banner, 'Checking service…', 22, 17, 395, 33, 24, True, key='status')
        self.text(banner, 'Connecting to local Reporter', 23, 58, 658, 24, 12, muted=True, key='detail')
        self.text(banner, '', 415, 22, 266, 25, 12, muted=True, key='host').setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        for key, title, x in [('cpu','CPU Usage',28), ('gpu','GPU Usage',207), ('memory','Memory Usage',386), ('disk','Disk Space Usage',565)]:
            card = self.card(x, 210, 166, 108)
            self.text(card, title, 20, 16, 126, 22, 12, muted=True)
            self.text(card, '—', 20, 40, 126, 42, 28, True, key=key)
            if key in ('cpu','gpu'):
                self.text(card, 'Temp —', 20, 86, 126, 18, 11, muted=True, key=key+'_temp')
        card = self.card(28, 332, 704, 76)
        self.text(card, 'Live Network', 20, 14, 160, 22, 12, muted=True)
        self.text(card, '↑  —', 20, 38, 320, 29, 19, key='upload')
        self.text(card, '↓  —', 363, 38, 320, 29, 19, key='download')
        card = self.card(28, 422, 346, 102)
        self.text(card, 'CODEX', 20, 15, 306, 21, 11, True, True, key='quota_status')
        self.text(card, 'Waiting for data', 20, 39, 306, 27, 20, True, key='agent')
        self.text(card, 'Short window —    ·    Weekly quota —', 20, 73, 306, 23, 12, muted=True, key='quota')
        card = self.card(388, 422, 344, 102)
        self.text(card, 'NetEase Cloud Music', 20, 15, 304, 21, 11, True, True)
        self.text(card, 'Waiting for playback', 20, 39, 304, 27, 16, True, key='music')
        self.text(card, 'Open NetEase Cloud Music and play a song', 20, 73, 304, 23, 11, muted=True, key='music_detail')
        card = self.card(28, 538, 704, 72)
        self.text(card, 'Board Communication', 20, 12, 180, 22, 12, muted=True)
        self.text(card, 'Waiting for board requests', 20, 37, 660, 24, 14, key='device')
        self.labels['device'].setToolTip('Shows discovery requests received in the last 15 seconds; it does not mean the board has selected this computer.')
        self.toggle = self.button('Checking…', 28, 129, self.toggle_service)
        self.toggle.setEnabled(False)
        self.diagnostic = self.button('Diagnostics', 169, 108, lambda: QDesktopServices.openUrl(QUrl('http://127.0.0.1:8765/api/v1/status')))
        self.button('Open Logs', 288, 108, self.open_logs)
        self.button('About Author', 407, 108, self.about)
        self.text(self, 'Waiting for first update', 526, 635, 206, 22, 11, muted=True, key='updated').setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.login = QCheckBox('Start at Login', self.content)
        self.login.setGeometry(28, 674, 210, 26)
        self.login.clicked.connect(self.toggle_login)
        self.text(self, '', 246, 678, 360, 22, 11, muted=True, key='login')
        self.button('Startup Items', 618, 114, lambda: QDesktopServices.openUrl(QUrl('ms-settings:startupapps')), y=671)
        self.text(self, 'Keeps running after the window is closed · Quitting from the tray menu stops the service', 29, 718, 700, 20, 11, muted=True)

    def put(self, key, value):
        self.labels[key].setText(value)
        if key in ('music','music_detail','host'):
            self.labels[key].setToolTip(value)

    def render(self, body):
        self.put('status', '●  Running')
        self.put('detail', 'Collecting computer status and serving data to boards on the same network.' if self.worker else 'The service is running in another process; this window only shows its status.')
        self.put('host', body.get('computer_name', 'This computer'))
        perf = body.get('performance', {})
        for key in ('cpu','gpu','memory','disk'):
            self.put(key, number(perf.get(key+'_percent'), '%'))
        for key in ('cpu','gpu'):
            self.put(key+'_temp', 'Temp ' + number(perf.get(key+'_temp_c'), '°C'))
        for key, arrow in [('upload','↑'),('download','↓')]:
            self.put(key, arrow+'  '+rate(perf.get(key+'_bytes_per_sec')))
        agent = body.get('agent', {})
        state = agent.get('state', 'offline')
        names = {'working':'Working','done':'Done','idle':'Idle','offline':'Not running','login_required':'Please log in to Codex','waiting':'Waiting for input'}
        self.put('agent', names.get(state, 'Status unavailable') + (f"  ·  {agent.get('active_count',0)} tasks" if state == 'working' else ''))
        quota = body.get('codex_quota', {})
        self.put('quota_status', 'CODEX · Update failed, showing the last data' if quota.get('stale') else
                 'CODEX · Quota temporarily unavailable' if quota.get('source') == 'unavailable' else 'CODEX')
        self.put('quota', 'Short window '+number(quota.get('short_remaining_percent'),'%')+'    ·    Weekly quota '+number(quota.get('week_remaining_percent'),'%'))
        media = body.get('media', {})
        def clock(value):
            seconds = max(0,int(value or 0))
            return f'{seconds//60}:{seconds%60:02d}'
        if media.get('available'):
            self.put('music', media.get('title', ''))
            self.put('music_detail', ('Playing' if media.get('playback_status') == 'playing' else 'Paused')+f" · {clock(media.get('position_seconds'))}/{clock(media.get('duration_seconds'))} · {media.get('artist','')}")
        else:
            self.put('music', 'No song detected')
            self.put('music_detail', 'Play a song in NetEase Cloud Music')
        devices = body.get('devices', [])
        self.put('device', f"Received requests from {len(devices)} board(s)  ·  "+', '.join(p.get('ip','') for p in devices) if devices else 'No requests yet; make sure the board and the computer are on the same Wi-Fi.')
        self.put('updated', 'Updated  '+time.strftime('%H:%M:%S'))
        self.toggle.setText('Stop Service' if self.worker else 'Another process')
        self.toggle.setEnabled(self.worker is not None)
        self.diagnostic.setEnabled(True)
        self.restart_delay = 1000

    def offline(self):
        self.put('host', '')
        self.put('status', 'Starting…' if self.wanted and self.worker else '○  Service not running')
        self.put('detail', 'No live data. Click Start Service, or open the logs to see why.')
        for key in ('cpu','gpu','memory','disk'):
            self.put(key, '—')
        for key in ('cpu','gpu'):
            self.put(key+'_temp', 'Temp —')
        self.put('upload', '↑  —')
        self.put('download', '↓  —')
        self.put('agent', 'Waiting for the service')
        self.put('quota', 'Short window —    ·    Weekly quota —')
        self.put('quota_status', 'CODEX')
        self.put('music', 'Waiting for the service')
        self.put('music_detail', '—')
        self.put('device', 'No data is sent to the board while the service is stopped.')
        self.put('updated', 'Not connected / old data cleared')
        self.toggle.setText('Stop Service' if self.worker else 'Start Service')
        self.toggle.setEnabled(True)
        self.diagnostic.setEnabled(False)

    def refresh(self):
        if self.polling or self.quitting:
            return
        self.polling = True
        request = QNetworkRequest(QUrl('http://127.0.0.1:8765/api/v1/status'))
        request.setTransferTimeout(2000)
        reply = self.network.get(request)
        def finished():
            self.polling = False
            try:
                if reply.error() != QNetworkReply.NoError:
                    raise ValueError('service unavailable')
                body = json.loads(bytes(reply.readAll()))
                if not isinstance(body.get('performance'), dict):
                    raise ValueError('not a Reporter response')
                self.render(body)
            except (ValueError, TypeError, AttributeError):
                self.offline()
                if self.first_poll and self.wanted:
                    self.start_service()
            finally:
                self.first_poll = False
                reply.deleteLater()
        reply.finished.connect(finished)

    def start_service(self):
        if self.worker or self.quitting:
            return
        self.wanted = True
        process = QProcess(self)
        self.worker = process
        command = launch_command()
        process.setProgram(command[0])
        process.setArguments(command[1:]+['--worker'])
        process.setStandardOutputFile(QProcess.nullDevice())
        process.setStandardErrorFile(QProcess.nullDevice())
        process.finished.connect(lambda *_: self.worker_finished(process))
        process.errorOccurred.connect(lambda error: self.worker_finished(process) if error == QProcess.FailedToStart else None)
        process.start()
        self.offline()

    def worker_finished(self, process):
        if self.worker is not process:
            return
        self.worker = None
        process.deleteLater()
        if self.wanted and not self.quitting:
            delay = self.restart_delay
            self.restart_delay = min(30000, delay*2)
            QTimer.singleShot(delay, lambda: self.start_service() if self.wanted else None)
        self.offline()

    def toggle_service(self):
        if self.worker:
            self.wanted = False
            # Only kill our direct worker, never an unrelated Reporter process.
            self.worker.kill()
        else:
            self.start_service()

    def refresh_login(self):
        try:
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RUN_KEY) as key:
                    winreg.QueryValueEx(key, 'SynaReporter')
                self.login.setChecked(True)
                self.login.setEnabled(False)
                self.put('login', 'The old startup item is still present; run the new installer first')
                return
            except FileNotFoundError:
                pass
            self.login.setEnabled(True)
            enabled = login_enabled()
            self.login.setChecked(enabled)
            self.put('login', 'Enabled; the window and service start automatically at next login' if enabled else 'Disabled; open the program manually after logging in')
            if enabled:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run') as key:
                        approval, _ = winreg.QueryValueEx(key, 'SynaReporter')
                    if isinstance(approval, bytes) and approval and approval[0] in (3, 7):
                        self.put('login', 'Disabled by the system; allow it in Startup Items')
                except FileNotFoundError:
                    pass
        except OSError as exc:
            self.put('login', 'Cannot read startup items: '+str(exc))

    def toggle_login(self, enabled):
        try:
            set_login(enabled)
        except OSError as exc:
            QMessageBox.warning(self, 'Cannot change the auto-start setting', str(exc))
        self.refresh_login()

    def open_logs(self):
        directory = application_data_dir()
        directory.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def about(self):
        box = QMessageBox(self)
        box.setWindowTitle('About Author')
        box.setText('Syna · v1.0.0\nAuthor: Heimu')
        box.setInformativeText('Bilibili UID 386856267\nQQ 3091479711\n\nOfficial Repository: github.com/heimumumu/Waveshare_ESP32_RLCD\nRelease Download: the repository Releases page\n\nCopyright © 2026 Heimu\nOriginal parts use MIT; third-party components keep their own licenses.')
        repo = box.addButton('Official Repository', QMessageBox.ActionRole)
        releases = box.addButton('Release Download', QMessageBox.ActionRole)
        box.addButton('Close', QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() in (repo, releases):
            QDesktopServices.openUrl(QUrl(REPOSITORY+('/releases' if box.clickedButton() is releases else '')))

    def reveal(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if not self.preview:
            self.refresh_login()

    def closeEvent(self, event):
        if self.quitting:
            event.accept()
        elif self.tray.isSystemTrayAvailable():
            self.hide()
            event.ignore()
        else:
            event.ignore()
            QMessageBox.information(self, 'System tray unavailable', 'Minimize the window to the taskbar; to stop the program, press Alt+F4 and choose Quit.')
            if QMessageBox.question(self, 'Quit program', 'Quit Syna Reporter and stop the service?') == QMessageBox.Yes:
                self.quit()

    def quit(self):
        self.quitting = True
        self.wanted = False
        self.timer.stop()
        if self.worker:
            self.worker.kill()
            self.worker.waitForFinished(3000)
        self.tray.hide()
        QApplication.instance().quit()


def run():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    root = application_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    name = 'syna-reporter-ui-'+hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:20]
    lock = QLockFile(str(root/'windows-ui.lock'))
    if not lock.tryLock(0):
        socket = QLocalSocket()
        socket.connectToServer(name)
        if socket.waitForConnected(2000):
            socket.write(b'show')
            socket.waitForBytesWritten(1000)
        return 0
    QLocalServer.removeServer(name)
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.UserAccessOption)
    if not server.listen(name):
        raise RuntimeError('Cannot create the window communication channel: '+server.errorString())
    window = ReporterWindow()
    def connected():
        peer = server.nextPendingConnection()
        window.reveal()
        peer.disconnectFromServer()
        peer.deleteLater()
    server.newConnection.connect(connected)
    app.aboutToQuit.connect(lambda: window.quit() if not window.quitting else None)
    window.show()
    return app.exec()
