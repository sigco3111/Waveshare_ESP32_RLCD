// Copyright (c) 2026 Heimu. Licensed under the MIT License.
import Cocoa
import Foundation
import ServiceManagement

final class Canvas: NSView {
    override var isFlipped: Bool { true }
}

final class ReporterApp: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var backend: Process?
    var timer: Timer?
    var polling = false
    var initialCheck = true
    var stopping = false
    var quitting = false
    var lastSuccess: Date?
    var launchedAt: Date?
    let port = 8765
    let ink = NSColor(calibratedRed: 0.13, green: 0.20, blue: 0.23, alpha: 1)
    let muted = NSColor(calibratedRed: 0.43, green: 0.49, blue: 0.50, alpha: 1)
    let green = NSColor(calibratedRed: 0.12, green: 0.46, blue: 0.36, alpha: 1)
    var statusLabel: NSTextField!
    var detailLabel: NSTextField!
    var hostLabel: NSTextField!
    var cpu: NSTextField!
    var gpu: NSTextField!
    var cpuTemperature: NSTextField!
    var gpuTemperature: NSTextField!
    var memory: NSTextField!
    var disk: NSTextField!
    var upload: NSTextField!
    var download: NSTextField!
    var agent: NSTextField!
    var quota: NSTextField!
    var device: NSTextField!
    var musicTitle: NSTextField!
    var musicDetail: NSTextField!
    var updated: NSTextField!
    var toggle: NSButton!
    var diagnostic: NSButton!
    var loginSwitch: NSSwitch!
    var loginStatus: NSTextField!
    var loginSettings: NSButton!
    let session: URLSession = {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 2
        config.timeoutIntervalForResource = 3
        config.connectionProxyDictionary = [:]
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        return URLSession(configuration: config)
    }()

    var dataDirectory: URL {
        if let override = ProcessInfo.processInfo.environment["SYNA_REPORTER_DATA_DIR"] {
            return URL(fileURLWithPath: override)
        }
        return FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/SynaReporter", isDirectory: true)
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        if CommandLine.arguments.contains("--installer-enable-login") {
            if #available(macOS 13.0, *) {
                do {
                    // Installation may move the app from a development folder
                    // or an older location. Refresh the registered path.
                    if SMAppService.mainApp.status == .enabled { try SMAppService.mainApp.unregister() }
                    try SMAppService.mainApp.register()
                }
                catch { NSLog("Installer login registration: %@", error.localizedDescription) }
            }
        }
        buildMenu()
        buildWindow()
        showWindow()
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in self?.refresh() }
    }

    func buildMenu() {
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let submenu = NSMenu()
        submenu.addItem(withTitle: "Show Status Window", action: #selector(showWindow), keyEquivalent: "0").target = self
        submenu.addItem(NSMenuItem.separator())
        submenu.addItem(withTitle: "Quit Syna Reporter", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = submenu
        menu.addItem(appItem)
        NSApp.mainMenu = menu
    }

    @discardableResult
    func text(_ parent: NSView, _ value: String, _ x: CGFloat, _ y: CGFloat,
              _ width: CGFloat, _ height: CGFloat, _ size: CGFloat = 14,
              _ weight: NSFont.Weight = .regular, _ color: NSColor? = nil) -> NSTextField {
        let label = NSTextField(labelWithString: value)
        label.frame = NSRect(x: x, y: y, width: width, height: height)
        label.font = .systemFont(ofSize: size, weight: weight)
        label.textColor = color ?? ink
        label.lineBreakMode = .byTruncatingTail
        label.isSelectable = true
        parent.addSubview(label)
        return label
    }

    func card(_ parent: NSView, _ rect: NSRect, _ tint: NSColor = .white) -> Canvas {
        let view = Canvas(frame: rect)
        view.wantsLayer = true
        view.layer?.backgroundColor = tint.cgColor
        view.layer?.cornerRadius = 16
        parent.addSubview(view)
        return view
    }

    func metric(_ parent: NSView, _ name: String, _ x: CGFloat) -> NSTextField {
        let view = card(parent, NSRect(x: x, y: 210, width: 166, height: 108))
        text(view, name, 20, 16, 126, 22, 12, .medium, muted)
        return text(view, "—", 20, 40, 126, 42, 28, .semibold)
    }

    func buildWindow() {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 760, height: 750),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Syna Reporter"
        window.isReleasedWhenClosed = false
        window.titlebarAppearsTransparent = true
        window.backgroundColor = NSColor(calibratedRed: 0.95, green: 0.96, blue: 0.95, alpha: 1)
        window.appearance = NSAppearance(named: .aqua)
        let page = Canvas(frame: NSRect(x: 0, y: 0, width: 760, height: 750))
        window.contentView = page
        text(page, "Syna Reporter", 28, 24, 470, 38, 29, .semibold)
        text(page, "Your computer and Syna, at a glance.", 29, 64, 650, 23, 13, .regular, muted)
        text(page, "MAC Status Center", 576, 34, 156, 23, 11, .semibold, muted).alignment = .right

        let banner = card(page, NSRect(x: 28, y: 100, width: 704, height: 96),
                          NSColor(calibratedRed: 0.88, green: 0.94, blue: 0.91, alpha: 1))
        statusLabel = text(banner, "Checking service…", 22, 17, 440, 33, 24, .semibold, green)
        detailLabel = text(banner, "Connecting to local Reporter", 23, 58, 658, 24, 12, .regular, muted)
        hostLabel = text(banner, "", 415, 22, 266, 25, 12, .medium, muted)
        hostLabel.alignment = .right

        cpu = metric(page, "CPU Usage", 28)
        gpu = metric(page, "GPU Usage", 207)
        memory = metric(page, "Memory Usage", 386)
        disk = metric(page, "Disk Space Usage", 565)
        cpuTemperature = text(cpu.superview!, "Temp —", 20, 86, 126, 18, 11, .regular, muted)
        gpuTemperature = text(gpu.superview!, "Temp —", 20, 86, 126, 18, 11, .regular, muted)
        cpuTemperature.toolTip = "Average CPU temperature sensor value, updated every 5 seconds"
        gpuTemperature.toolTip = "Average GPU temperature sensor value, updated every 5 seconds"

        let network = card(page, NSRect(x: 28, y: 332, width: 704, height: 76))
        text(network, "Live Network", 20, 14, 160, 22, 12, .medium, muted)
        upload = text(network, "↑  —", 20, 38, 320, 29, 19, .medium)
        download = text(network, "↓  —", 363, 38, 320, 29, 19, .medium)

        let codex = card(page, NSRect(x: 28, y: 422, width: 346, height: 102))
        text(codex, "CODEX", 20, 15, 160, 21, 11, .semibold, muted)
        agent = text(codex, "Waiting for data", 20, 39, 306, 27, 20, .semibold)
        quota = text(codex, "Short window —    ·    Weekly quota —", 20, 73, 306, 23, 12, .regular, muted)

        let music = card(page, NSRect(x: 388, y: 422, width: 344, height: 102))
        text(music, "NetEase Cloud Music", 20, 15, 304, 21, 11, .semibold, muted)
        musicTitle = text(music, "Waiting for playback", 20, 39, 304, 27, 16, .semibold)
        musicDetail = text(music, "Open NetEase Cloud Music and play a song", 20, 73, 304, 23, 11, .regular, muted)

        let board = card(page, NSRect(x: 28, y: 538, width: 704, height: 72))
        text(board, "Board Communication", 20, 12, 180, 22, 12, .medium, muted)
        device = text(board, "Waiting for board requests", 20, 37, 660, 24, 14, .medium)

        toggle = NSButton(title: "Checking…", target: self, action: #selector(toggleService))
        toggle.bezelStyle = .rounded
        toggle.controlSize = .large
        toggle.frame = NSRect(x: 24, y: 626, width: 133, height: 34)
        toggle.isEnabled = false
        page.addSubview(toggle)
        diagnostic = NSButton(title: "Diagnostics", target: self, action: #selector(openDiagnostic))
        diagnostic.bezelStyle = .rounded
        diagnostic.frame = NSRect(x: 169, y: 626, width: 108, height: 34)
        page.addSubview(diagnostic)
        let logs = NSButton(title: "Open Logs", target: self, action: #selector(openLogs))
        logs.bezelStyle = .rounded
        logs.frame = NSRect(x: 288, y: 626, width: 108, height: 34)
        page.addSubview(logs)
        let author = NSButton(title: "About Author", target: self, action: #selector(aboutAuthor))
        author.bezelStyle = .rounded
        author.frame = NSRect(x: 407, y: 626, width: 108, height: 34)
        page.addSubview(author)
        updated = text(page, "Waiting for first update", 526, 635, 206, 22, 11, .regular, muted)
        updated.alignment = .right
        loginSwitch = NSSwitch(frame: NSRect(x: 28, y: 674, width: 40, height: 24))
        loginSwitch.target = self
        loginSwitch.action = #selector(toggleLogin)
        loginSwitch.setAccessibilityLabel("Start at Login")
        page.addSubview(loginSwitch)
        text(page, "Start at Login", 78, 676, 160, 22, 13, .medium)
        loginStatus = text(page, "", 246, 678, 350, 22, 11, .regular, muted)
        loginSettings = NSButton(title: "Login Items", target: self, action: #selector(openLoginSettings))
        loginSettings.bezelStyle = .rounded
        loginSettings.frame = NSRect(x: 618, y: 671, width: 118, height: 32)
        page.addSubview(loginSettings)
        refreshLoginStatus()
        text(page, "Keeps running after the window is closed · Quitting the app stops the service", 29, 718, 700, 20, 11, .regular, muted)
        window.center()
    }

    @objc func showWindow() {
        window.deminiaturize(nil)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        showWindow()
        return false
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    func refresh() {
        refreshLoginStatus()
        guard !polling && !quitting else { return }
        polling = true
        let url = URL(string: "http://127.0.0.1:\(port)/api/v1/status")!
        session.dataTask(with: url) { [weak self] data, response, error in
            let json = data.flatMap { try? JSONSerialization.jsonObject(with: $0) } as? [String: Any]
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.polling = false
                if let body = json, (response as? HTTPURLResponse)?.statusCode == 200,
                   body["reporter_id"] is String, body["online"] as? Bool == true {
                    self.initialCheck = false
                    self.lastSuccess = Date()
                    self.render(body)
                } else {
                    self.offline()
                    if self.initialCheck {
                        self.initialCheck = false
                        self.startService()
                    }
                }
            }
        }.resume()
    }

    func percent(_ value: Any?) -> String {
        guard let number = value as? NSNumber else { return "—" }
        return String(format: "%.1f%%", number.doubleValue)
    }

    func rate(_ value: Any?) -> String {
        guard let number = value as? NSNumber else { return "—" }
        let speed = max(0, number.doubleValue)
        return speed >= 1048576 ? String(format: "%.2f MB/s", speed / 1048576)
            : String(format: "%.1f KB/s", speed / 1024)
    }

    func render(_ body: [String: Any]) {
        statusLabel.stringValue = stopping ? "Stopping…" : "●  Running"
        statusLabel.textColor = green
        hostLabel.stringValue = body["computer_name"] as? String ?? "This Mac"
        detailLabel.stringValue = backend == nil ? "The service is running in another process; this window only shows its status." : "Collecting computer status and serving data to boards on the same network."
        let performance = body["performance"] as? [String: Any] ?? [:]
        cpu.stringValue = percent(performance["cpu_percent"])
        gpu.stringValue = percent(performance["gpu_percent"])
        func temperature(_ value: Any?) -> String {
            guard let number = value as? NSNumber else { return "Temp —" }
            return String(format: "Temp %.1f°C", number.doubleValue)
        }
        cpuTemperature.stringValue = temperature(performance["cpu_temp_c"])
        gpuTemperature.stringValue = temperature(performance["gpu_temp_c"])
        memory.stringValue = percent(performance["memory_percent"])
        disk.stringValue = percent(performance["disk_percent"])
        upload.stringValue = "↑  " + rate(performance["upload_bytes_per_sec"])
        download.stringValue = "↓  " + rate(performance["download_bytes_per_sec"])
        let state = body["agent"] as? [String: Any] ?? [:]
        let code = state["state"] as? String ?? "offline"
        let names = ["working": "Working", "done": "Done", "idle": "Idle", "offline": "Not running", "login_required": "Please log in to Codex", "waiting": "Waiting for input"]
        let count = (state["active_count"] as? NSNumber)?.intValue ?? 0
        agent.stringValue = (names[code] ?? "Status unavailable") + (code == "working" ? "  ·  \(count) tasks" : "")
        let limits = body["codex_quota"] as? [String: Any] ?? [:]
        quota.stringValue = "Short window \(percent(limits["short_remaining_percent"]))    ·    Weekly quota \(percent(limits["week_remaining_percent"]))"
        let media = body["media"] as? [String: Any] ?? [:]
        if media["available"] as? Bool == true {
            musicTitle.stringValue = media["title"] as? String ?? ""
            musicTitle.toolTip = musicTitle.stringValue
            let singer = media["artist"] as? String ?? ""
            let status = media["playback_status"] as? String == "playing" ? "Playing" : "Paused"
            func clock(_ value: Any?) -> String {
                let seconds = max(0, (value as? NSNumber)?.intValue ?? 0)
                return String(format: "%d:%02d", seconds / 60, seconds % 60)
            }
            musicDetail.stringValue = "\(status) · \(clock(media["position_seconds"]))/\(clock(media["duration_seconds"])) · \(singer)"
            musicDetail.toolTip = musicDetail.stringValue
        } else {
            musicTitle.stringValue = "No song detected"
            musicTitle.toolTip = nil
            musicDetail.stringValue = "Play a song in NetEase Cloud Music"
            musicDetail.toolTip = nil
        }
        let peers = body["devices"] as? [[String: Any]] ?? []
        let ips = peers.compactMap { $0["ip"] as? String }.joined(separator: ", ")
        device.stringValue = peers.isEmpty ? "No requests yet; make sure the board and the Mac are on the same Wi-Fi."
            : "Received requests from \(peers.count) board(s)  ·  \(ips)"
        device.toolTip = "Shows discovery requests received in the last 15 seconds; it does not mean the board has selected this computer."
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        updated.stringValue = "Updated  " + formatter.string(from: Date())
        toggle.title = backend == nil ? "Another process" : "Stop Service"
        toggle.isEnabled = backend != nil && !stopping
        diagnostic.isEnabled = true
    }

    func offline() {
        let starting = backend?.isRunning == true && launchedAt.map { Date().timeIntervalSince($0) < 8 } == true
        statusLabel.stringValue = stopping ? "Stopping…" : (starting ? "Starting…" : "○  Service not running")
        statusLabel.textColor = starting ? green : .systemOrange
        detailLabel.stringValue = starting ? "Initializing the collector and network service." : "No live data. Click Start Service, or open the logs to see why."
        for label in [cpu, gpu, memory, disk] { label?.stringValue = "—" }
        cpuTemperature.stringValue = "Temp —"
        gpuTemperature.stringValue = "Temp —"
        upload.stringValue = "↑  —"
        download.stringValue = "↓  —"
        agent.stringValue = "Waiting for the service"
        musicTitle.stringValue = "Waiting for the service"
        musicDetail.stringValue = "—"
        musicTitle.toolTip = nil
        musicDetail.toolTip = nil
        quota.stringValue = "Short window —    ·    Weekly quota —"
        device.stringValue = "No data is sent to the board while the service is stopped."
        updated.stringValue = lastSuccess == nil ? "Not connected" : "Connection lost, old data cleared"
        toggle.title = backend?.isRunning == true ? "Stop Service" : "Start Service"
        toggle.isEnabled = !stopping && !initialCheck
        diagnostic.isEnabled = false
    }

    func startService() {
        guard backend?.isRunning != true else { return }
        let executable = Bundle.main.bundleURL.appendingPathComponent("Contents/MacOS/ReporterBackend")
        let process = Process()
        process.executableURL = executable
        process.arguments = ["--port", String(port)]
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        process.terminationHandler = { [weak self] finished in
            DispatchQueue.main.async {
                guard let self = self, self.backend === finished else { return }
                self.backend = nil
                self.stopping = false
                self.refresh()
            }
        }
        do {
            try process.run()
            backend = process
            launchedAt = Date()
            offline()
        } catch {
            backend = nil
            offline()
            detailLabel.stringValue = "Failed to start: \(error.localizedDescription)"
        }
    }

    @objc func toggleService() {
        if let process = backend, process.isRunning {
            stopping = true
            toggle.isEnabled = false
            process.terminate()
            offline()
        } else {
            startService()
        }
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        if loginSwitch != nil { refreshLoginStatus() }
    }

    func refreshLoginStatus() {
        guard #available(macOS 13.0, *) else {
            loginSwitch.isEnabled = false
            loginSettings.isEnabled = false
            loginStatus.stringValue = "This feature requires macOS 13 or later"
            return
        }
        switch SMAppService.mainApp.status {
        case .enabled:
            loginSwitch.state = .on
            loginStatus.stringValue = "Enabled; the window and service start automatically at next login"
        case .requiresApproval:
            loginSwitch.state = .on
            loginStatus.stringValue = "Waiting for system permission; enable it in Login Items"
        case .notRegistered:
            loginSwitch.state = .off
            loginStatus.stringValue = "Disabled; open the program manually after logging in"
        case .notFound:
            loginSwitch.state = .off
            loginStatus.stringValue = "The system could not find the app; reopen the full application"
        @unknown default:
            loginSwitch.state = .off
            loginStatus.stringValue = "Unknown status; check the system Login Items"
        }
    }

    @objc func toggleLogin() {
        guard #available(macOS 13.0, *) else { return }
        do {
            if loginSwitch.state == .on {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
        } catch {
            let alert = NSAlert()
            alert.messageText = "Cannot change the auto-start setting"
            alert.informativeText = error.localizedDescription
            alert.addButton(withTitle: "OK")
            alert.beginSheetModal(for: window)
        }
        refreshLoginStatus()
    }

    @objc func openLoginSettings() {
        if #available(macOS 13.0, *) { SMAppService.openSystemSettingsLoginItems() }
    }

    @objc func openDiagnostic() {
        NSWorkspace.shared.open(URL(string: "http://127.0.0.1:\(port)/api/v1/status")!)
    }

    @objc func openLogs() {
        try? FileManager.default.createDirectory(at: dataDirectory, withIntermediateDirectories: true)
        NSWorkspace.shared.open(dataDirectory)
    }

    @objc func aboutAuthor() {
        let alert = NSAlert()
        alert.messageText = "About Author"
        alert.informativeText = "Syna · v1.0.0\nAuthor: Heimu\n\nBilibili UID 386856267\nQQ 3091479711\n\nOfficial Repository: github.com/heimumumu/Waveshare_ESP32_RLCD\nRelease Download: the repository Releases page\n\nCopyright © 2026 Heimu\nOriginal parts use MIT; third-party components keep their own licenses."
        alert.addButton(withTitle: "Close")
        alert.addButton(withTitle: "Official Repository")
        alert.addButton(withTitle: "Release Download")
        alert.beginSheetModal(for: window) { response in
            if response == .alertSecondButtonReturn {
                NSWorkspace.shared.open(URL(string: "https://github.com/heimumumu/Waveshare_ESP32_RLCD")!)
            } else if response == .alertThirdButtonReturn {
                NSWorkspace.shared.open(URL(string: "https://github.com/heimumumu/Waveshare_ESP32_RLCD/releases")!)
            }
        }
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        quitting = true
        timer?.invalidate()
        guard let process = backend, process.isRunning else { return .terminateNow }
        process.terminate()
        DispatchQueue.global().async {
            process.waitUntilExit()
            DispatchQueue.main.async { NSApp.reply(toApplicationShouldTerminate: true) }
        }
        return .terminateLater
    }
}

// Preserve command-line and worker behavior for existing launchers and tests.
if !CommandLine.arguments.contains("--installer-enable-login") && CommandLine.arguments.dropFirst().contains(where: { $0.hasPrefix("--") }) {
    let executable = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent().appendingPathComponent("ReporterBackend").path
    let arguments = [executable] + Array(CommandLine.arguments.dropFirst())
    let pointers = arguments.map { strdup($0) } + [nil]
    execv(executable, pointers)
    exit(1)
}
let application = NSApplication.shared
let delegate = ReporterApp()
application.delegate = delegate
application.run()
