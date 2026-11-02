# Syna project-specific code and modifications: Copyright (c) 2026 Heimu.
# SPDX-License-Identifier: MIT; third-party notices remain applicable.
"""Explicit per-user launchd installation, status, stop and uninstall commands."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import plistlib
import subprocess
import sys

from platform_support import application_data_dir, codex_executable

LABEL = "local.syna.reporter"


def service_definition(python: Path, entry: Path) -> dict:
    root = application_data_dir()
    environment = {"SYNA_REPORTER_DATA_DIR": str(root), "PYTHONUNBUFFERED": "1"}
    codex = codex_executable()
    if codex:
        environment["SYNA_CODEX_EXECUTABLE"] = codex
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python), str(entry), "--no-supervisor"],
        "WorkingDirectory": str(entry.parent),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "EnvironmentVariables": environment,
        "StandardOutPath": str(root / "launchd.stdout.log"),
        "StandardErrorPath": str(root / "launchd.stderr.log"),
        "ProcessType": "Background",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the macOS login-start background service for Syna Reporter")
    parser.add_argument("action", choices=["install", "start", "stop", "status", "uninstall"])
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This tool only works on macOS")
    domain = f"gui/{os.getuid()}"
    target = f"{domain}/{LABEL}"
    plist = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    if args.action == "status":
        return subprocess.run(["launchctl", "print", target]).returncode
    if args.action in {"stop", "uninstall"}:
        subprocess.run(["launchctl", "bootout", target], check=False)
        if args.action == "uninstall":
            plist.unlink(missing_ok=True)
        print("Service stopped; " + ("Login startup removed; configuration and logs are kept." if args.action == "uninstall" else "It will still start at the next login."))
        return 0
    if args.action == "install":
        entry = Path(__file__).resolve().with_name("reporter.py")
        # Do not resolve the venv interpreter symlink: doing so bypasses its dependencies.
        python = Path(sys.executable).absolute()
        definition = service_definition(python, entry)
        application_data_dir().mkdir(parents=True, exist_ok=True)
        plist.parent.mkdir(parents=True, exist_ok=True)
        temporary = plist.with_suffix(".tmp")
        temporary.write_bytes(plistlib.dumps(definition))
        temporary.replace(plist)
        subprocess.run(["launchctl", "bootout", target], check=False, capture_output=True)
    if not plist.exists():
        parser.error("The service is not installed yet; run install first")
    subprocess.run(["launchctl", "bootstrap", domain, str(plist)], check=True)
    print("Reporter started and will run automatically after login. Do not move the project or delete .venv-macos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
