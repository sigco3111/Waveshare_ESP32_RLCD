# 빌드 가이드

다음 명령은 프로젝트 루트에서 실행합니다. 검증 결과: [빌드 기록](BUILD_VALIDATION.md).

## Reporter

Python 3.11을 사용하세요. Windows에서는 프로젝트 루트에서 실행합니다:

```powershell
python -m venv reporter/.venv
reporter/.venv/Scripts/python.exe -m pip install -r reporter/requirements-build.txt
Push-Location reporter
.venv/Scripts/python.exe -m PyInstaller --noconfirm --distpath dist --workpath build SynaReporter.spec
Pop-Location
```

출력물은 `reporter/dist/SynaReporter.exe`입니다. 소스 실행 진입점은 `reporter/reporter.py`이며, Mac 빌드 진입점은 `reporter/build_macos.command`입니다.

## ESP-IDF 펌웨어

1. Git, ESP-IDF **6.0.2**, ESP32-S3 툴체인을 설치하고 공식 ESP-IDF 환경을 활성화하세요.
2. `xiaozhi/upstream.lock`이 지정한 저장소를 고정된 커밋으로 체크아웃하고 서브모듈을 초기화하세요. Windows 소스와 빌드 경로는 공백 없는 ASCII 경로를 사용하세요.
3. 활성화된 환경에 `xiaozhi/requirements-firmware.txt`를 설치하세요.
4. `python <project>/xiaozhi/apply_ui_overlay.py <upstream> --phase source`를 실행하세요.
5. 업스트림 디렉토리에서 다음 명령으로 컴포넌트를 해결하고, 컴포넌트 패치를 적용한 뒤 빌드하세요:

```powershell
idf.py -DIDF_TARGET=esp32s3 '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;syna.sdkconfig.defaults' -DBOARD_NAME=esp32-s3-rlcd-4.2 reconfigure
python <project>/xiaozhi/apply_ui_overlay.py <upstream> --phase components
python scripts/build.py waveshare/esp32-s3-rlcd-4.2 --name esp32-s3-rlcd-4.2 --language en-US
```

`<project>`와 `<upstream>`은 교체할 경로입니다. 출력물은 업스트림 `build` 디렉토리에 있습니다. `build_windows.ps1`은 작성자의 기존 도구 디렉토리 구성을 위한 편의 래퍼이며, 일반 환경에서는 위의 수동 진입점을 권장합니다. `build_macos.sh`는 업스트림 경로와 `SYNA_IDF_ROOT`를 받습니다.

## Windows 올인원 설치 프로그램

먼저 Reporter와 펌웨어 빌드를 완료한 뒤 다음을 실행하세요:

```powershell
reporter/.venv/Scripts/python.exe -m pip install esptool==5.4.0
reporter/.venv/Scripts/python.exe installer/windows/build_standalone.py --firmware-build C:/syna/xiaozhi/build --reporter-exe reporter/dist/SynaReporter.exe
```

`C:/syna/xiaozhi/build`를 펌웨어 출력 디렉토리로 교체하세요. 설치 프로그램 출력물은 `installer/windows/dist`에 있습니다.

페이로드를 준비한 뒤 `installer/windows`에서 `python -m unittest -v test_installer.py`를 실행하세요. 테스트는 PySide6을 사용하며, 펌웨어 호스트 테스트에는 추가로 C++ 컴파일러가 필요하고, 경로 설정은 스크립트 헤더에 있습니다.

펌웨어 호스트 테스트는 패치된 업스트림 소스를 `SYNA_FIRMWARE_SOURCE`로, Visual Studio의 `vcvars64.bat`를 `SYNA_VCVARS`로 설정할 수 있습니다.

## 시뮬레이터

CMake, SDL2, LVGL **9.5.0**이 필요합니다. 해당 버전의 전체 소스를 `simulator/vendor/lvgl-9.5.0`에 배치하고 원래 라이선스를 유지한 뒤 `simulator/CMakeLists.txt`로 빌드하세요. 폰트 소스와 라이선스는 소스와 함께 유지되며, Python 폰트 생성기를 권장합니다. PowerShell 시뮬레이터 스크립트에는 여전히 작성자의 로컬 경로가 들어 있으므로 사용 전에 조정하거나, CMake를 통해 SDL2 검색 경로를 직접 설정하세요.
