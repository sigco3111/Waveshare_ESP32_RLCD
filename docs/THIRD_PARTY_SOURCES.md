# 서드파티 소스와 재빌드

이 프로젝트는 Qt/PySide6, esptool 등의 서드파티 소프트웨어를 사용합니다. 원본 소스의 MIT 라이선스는 서드파티 라이선스를 바꾸지 않으므로, 설치 프로그램 전체와 그에 포함된 의존성을 MIT라고 부르지 마세요.

| 컴포넌트 | 검증된 버전 | 대응 소스 진입점 |
| --- | --- | --- |
| Qt Core/Gui/Widgets/Network, 플랫폼 플러그인 | 6.8.3 | https://github.com/qt/qtbase/tree/v6.8.3 |
| Qt SVG | 6.8.3 | https://github.com/qt/qtsvg/tree/v6.8.3 |
| Qt imageformats 플러그인 | 6.8.3 | https://download.qt.io/archive/qt/6.8/6.8.3/submodules/ |
| PySide6 / Shiboken6 | 6.8.3 | https://github.com/qt/pyside-setup/tree/v6.8.3 |
| esptool | 5.4.0 | https://github.com/espressif/esptool/tree/v5.4.0 |
| pyserial | 3.5 | https://github.com/pyserial/pyserial/tree/v3.5 |
| PyWinRT (runtime/Foundation/Collections/Media.Control) | 3.2.1 | https://github.com/pywinrt/pywinrt/tree/v3.2.1 |
| CPython | 3.11.0 | https://github.com/python/cpython/tree/v3.11.0 |
| PyInstaller | 6.21.0 | https://github.com/pyinstaller/pyinstaller/tree/v6.21.0 |
| ESP-IDF | 6.0.2 | https://github.com/espressif/esp-idf/tree/v6.0.2 |
| OpenSSL (CPython DLL) | 1.1.1q | https://github.com/openssl/openssl/tree/OpenSSL_1_1_1q |
| Mesa / LLVM (opengl32sw.dll) | 11.2.2 / 3.6.2 | https://archive.mesa3d.org/older-versions/11.x/11.2.2/ 및 https://releases.llvm.org/3.6.2/ |

더 많은 의존성 버전은 `release/build-info/windows-validation-20260916/`에 있으며, 릴리스 메타데이터, 라이선스 파일, 소스 URL은 `docs/THIRD_PARTY_AUDIT.json`에 있습니다. 이 항목들은 소스를 찾는 용도이며, 링크만 제공한다고 최종 바이너리의 소스 배포 요구사항이 충족되는 것은 아닙니다.

## 후보 패키지에 제공되는 소스

후보 릴리스 디렉토리의 `third-party-sources/`에는 다운로드 링크만이 아니라 Qt Base, SVG, imageformats, PySide/Shiboken, esptool, Mesa, LLVM, OpenSSL의 버전 고정 업스트림 소스 아카이브가 실제로 제공됩니다. 패키지별 URL, 크기, SHA256은 `SOURCE_ARCHIVES.json`에 있으며, 라이선스와 저작자 표시는 이 아카이브에서 그대로 추출해 `release/licenses/upstream-source-notices/`에 넣습니다. 프로젝트 애플리케이션 소스는 `Syna-source-1.0.0.zip`에 별도로 둡니다.

Qt의 정식 릴리스 모듈 소스 패키지와 GitHub 태그 소스를 사용해 대응 버전을 보존합니다. Mesa/LLVM 버전은 실제 DLL에 내장된 버전 문자열에서 검증했으며, 이 미리 빌드된 DLL의 모든 빌드 옵션이나 벤더 패치를 완전히 재현했다고 주장할 수 없습니다.

## Qt와 수정된 라이브러리

Qt/PySide6은 오픈소스 라이선스를 사용하며, 휠에 동봉된 상용 라이선스 텍스트를 근거로 상용 승인을 주장하지 않습니다. LGPLv3 텍스트와 해당 텍스트가 참조하는 GPLv3 텍스트는 `release/licenses/windows-audit/supplemental/Qt-6.8.3/`에 포함됩니다.

이 프로젝트는 서드파티 라이브러리 수정을 위해 사용자가 프로그램을 디버깅, 리버스 엔지니어링, 교체, 재빌드하는 것을 금지하지 않습니다. Syna의 Python, 설치 백엔드, 패키징 스크립트는 소스로 제공합니다.

재조합 경로: 독립 Python 환경에 고정 버전으로 의존성을 설치하고, 자체 빌드한 호환 PySide6/Shiboken6/Qt를 해당 환경에 설치한 뒤 `docs/BUILD.md`에 따라 Reporter와 설치 프로그램을 빌드하세요. PySide 빌드 참조: https://doc.qt.io/qtforpython-6.8/building_from_source/index.html . 일회성 임시 추출 디렉토리를 수정해 라이브러리 교체가 검증됐다고 가정하지 마세요.

현재 단일 파일 산출물은 아직 수정된 Qt로 재빌드하지 않았으며, 배포자는 대응 소스와 재조합 자료의 전달 방법을 선택하고 구현해야 합니다. 최종 릴리스에는 라이선스를 싣고, 대응 소스와 빌드 자료가 실제로 구할 수 있도록 해야 합니다.

이 후보 디렉토리를 릴리스할 때는 애플리케이션 소스 패키지, 위 서드파티 소스, 빌드 안내를 함께 제공해야 하며, 접근 가능한 다운로드 위치를 유지해야 합니다. EXE만 업로드한 뒤 대응 소스가 이미 포함됐다고 주장하지 마세요. 수정된 Qt 재빌드는 아직 수행하지 않았으며, 관련 제한 사항을 유지해야 합니다.

## esptool

esptool의 GPLv2-or-later는 계속 유효하며, 동봉된 스텁은 별도의 Apache/MIT 파일을 가지고 있고 모두 유지됩니다. 백엔드는 플래싱 기능을 서브프로세스로 호출하지만, 백엔드 프로그램 자체도 esptool을 패키징하고 import하므로 "서브프로세스를 사용한다"는 이유만으로 GPL 배포 의무를 면제할 수 없습니다. 릴리스 시에는 대응 esptool 소스, 이 프로젝트의 백엔드 소스, 의존성, 빌드 안내를 함께 제공해야 하며, 최종 릴리스 조합의 배포 방식을 검증해야 합니다.

## 모델과 폰트

ESP-SR 2.4.7의 실제 설정 모델은 `mn7_cn`과 `fst`입니다. `THIRD_PARTY_AUDIT.json`은 원본 모델 파일 해시를 기록합니다. 모델은 이 프로젝트의 원작이 아니며, 라이선스에는 Espressif 제품 사용 범위가 포함됩니다. 폰트 소스와 해시는 `simulator/assets/fonts/SOURCE.md`에 있으며, OFL/원래 COPYING을 유지합니다.

이것은 배포 공학 기록이며, 미완료 항목은 THIRD_PARTY_AUDIT.md를 참조하세요. 최종 패키지가 릴리스용으로 완전히 승인됐다는 뜻이 아닙니다.
