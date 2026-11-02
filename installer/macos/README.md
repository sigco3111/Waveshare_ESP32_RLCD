# Mac 원클릭 설치 프로그램

Copyright (c) 2026 Heimu. 설치 프로그램 원본 코드는 프로젝트 MIT 라이선스를 사용합니다.

`Installer.swift`는 네이티브 AppKit 창을 제공하고, `worker.py`는 릴리스 파일 검증, 기기 백업, 파티션 감지, 플래싱, Reporter 원자 교체를 처리합니다. PyInstaller가 Python과 esptool을 함께 묶으므로 설치 시 의존성 다운로드가 필요 없습니다.

## 빌드

Apple Silicon Mac에서 Python 3.12, Xcode Command Line Tools, 검증된 Reporter `.app`, ESP-IDF 펌웨어 빌드 디렉토리를 준비하세요. 빌드는 기기를 플래싱하지 않습니다.

```bash
python3.12 -m venv .codex-tmp/installer-venv
.codex-tmp/installer-venv/bin/pip install -r installer/macos/requirements-build.txt
.codex-tmp/installer-venv/bin/python installer/macos/build.py \
  --worker-python .codex-tmp/installer-venv/bin/python \
  --firmware-build /path/to/xiaozhi/build \
  --reporter-app reporter/dist-macos/SynaReporter.app
```

기본 툴체인 경로와 펌웨어 경로는 이 프로젝트의 로컬 관례를 따릅니다. 빌드는 대응하는 ESP-IDF LICENSE, 펌웨어 의존성 디렉토리, Reporter의 `.venv-macos`에서 라이선스도 함께 읽으므로, 누락된 것이 있으면 먼저 프로젝트 환경을 준비하세요. Python 런타임 라이선스, 의존성 라이선스, 폰트 저작자 표시는 모두 Payload/Legal에 수집됩니다.

릴리스 개인키는 `~/Library/Application Support/SynaReleaseSigning/private.pem`에 있으며, 설치 프로그램에 포함되지 않습니다. 공개키는 `release/keys/syna-release-public.pem`을 사용하며, SHA-256이 워커 내부에 고정되어 있습니다. 서명 주체를 바꿀 때는 공개키 지문을 동기화하고 공식 채널로 사용자에게 알리세요.

출력물: `release/artifacts/v1.0.0-macos-installer/`로, DMG, 사용자 가이드, 서명 매니페스트를 포함합니다. 설치 프로그램은 아직 Developer ID 서명이나 Apple 공증을 사용하지 않으므로, 프로젝트 릴리스 서명을 Apple 인증으로 설명하지 마세요.

## 검증

```bash
python3.12 -m unittest discover -s installer/macos -p 'test_*.py' -v
python3 release/sign_release.py verify release/artifacts/v1.0.0-macos-installer
```

테스트는 OTA 이중 파티션 선택, 손상된 파티션/OTA 레코드, 잘못된 보드 모델, 링크 이스케이프, 설치 파일 변경, 백업 검증 실패 시 쓰기 차단, 최초 설치 백업 순서, 무관한 앱 덮어쓰기 거부를 다룹니다. 실제 설치 점검 기록은 `VERIFICATION.md`에 있습니다. 사용자 조작 방법은 [사용자 가이드](USER_GUIDE.md)에 있습니다.
