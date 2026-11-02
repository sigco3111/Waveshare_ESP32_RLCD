# 서드파티 배포 감사 (2026-09-16)

## 검증 및 보완 완료

- 검증 환경의 Python 배포 패키지 39개를 기록했습니다. 이 숫자는 환경 매니페스트이며, 모든 패키지가 최종 EXE에 들어갔다고 주장하지 않습니다.
- 세 개의 PyInstaller Analysis 매니페스트를 읽어 Reporter, 설치 프로그램, 백엔드 모듈, 바이너리, 데이터 파일을 기록했으며, requirements.txt만이 아닙니다.
- 실제 Qt 동적 라이브러리에는 Core, Gui, Widgets, Network, Svg가 포함됩니다. 같은 패키지의 플랫폼 플러그인과 이미지 플러그인도 함께 고려해야 합니다.
- Qt 휠 메타데이터에는 상용 라이선스만 들어 있어 원래 패커가 LGPL/GPL 텍스트를 빠뜨린 것을 발견했습니다. Qt 6.8.3 업스트림에서 LGPLv3, GPLv3, GPLv2를 보완했습니다.
- pyserial 3.5와 PyWinRT 3.2.1의 업스트림 라이선스, CPython 런타임 LICENSE를 보완했습니다.
- ESP-IDF 빌드 설명에서 177개 설정 컴포넌트의 라이선스를 수집했습니다. 설정된 컴포넌트가 모두 최종 링크 코드에 기여하는 것은 아니므로, 이 목록은 보수적 수집이며 심볼 단위 SBOM이 아닙니다.
- 실제 설정과 빌드 로그에서 ESP-SR 2.4.7과 mn7_cn/fst를 확인하고, 6개 모델 파일 해시를 기록했습니다.
- Reporter spec과 설치 프로그램 빌드 스크립트는 이제 위 보완 자료와 소스 취득 안내를 통합하므로, 이후 빌드가 휠 메타데이터에만 의존하지 않습니다.

기계 판독 기록: THIRD_PARTY_AUDIT.json, 라이선스 자료: `release/licenses/windows-audit/`, 수집 스크립트: `release/audit_licenses.py`. 모든 파일은 명확히 버전이 고정된 업스트림이나 실제 빌드 환경에서 가져왔으며, 원래 라이선스를 다시 쓰지 않습니다.

## 이후 자료 보완

Qt Base, SVG, imageformats, PySide/Shiboken, esptool, Mesa, LLVM, OpenSSL의 버전 고정 소스 패키지를 취득하고, Qt 저작자 표시와 해당 라이선스 원문을 파싱했습니다. 자료와 해시는 THIRD_PARTY_SOURCE_ARCHIVES.json에 기록합니다. 소스 패키지, 프로젝트 소스 ZIP, 라이선스 안내는 후보 릴리스 디렉토리와 함께 제공합니다. 최종 산출물과 검증 결과는 RELEASE_CANDIDATE.json에 있습니다.

Qt 모듈은 현재 바이너리에 들어가지 않을 수 있는 예제/테스트 선언을 포함하는 보수적 수집 범위를 사용합니다. 나열된 서드파티가 모두 현재 프로그램에서 사용된다고 주장해서는 안 됩니다.

## 정식 배포를 위해 아직 검증할 항목

1. 대응 소스, 원래 라이선스, 프로젝트 빌드 자료가 모두 최종 패키지와 함께 제공되는지 확인하세요. EXE만이 아닙니다.
2. 수정된 Qt의 실제 재빌드를 수행하지 않았습니다. 기존 스크립트는 재빌드 경로를 제공하며, 검증된 호환 라이브러리 교체가 되었다고 주장하지 않습니다.
3. Microsoft VC 런타임의 배포자 적용 라이선스는 작성자가 검증해야 합니다. 기존 설치 환경은 승인 확인을 대체할 수 없습니다. RUNTIME_NOTICES.md를 참조하세요.
4. Mesa/LLVM 버전은 실제 DLL에서 검증했으나, 벤더 패치와 빌드 옵션은 독립적으로 재현하지 않았습니다. 소스와 제한 사항을 유지합니다.
5. 폰트는 소스 기록이 있으며, 이미지 에셋은 작성자의 기존 확인을 따르고 아직 파일 단위로 다시 보관하지 않았습니다.

## 참조 근거

- Qt for Python 서드파티 고지: https://doc.qt.io/qtforpython-6.8/licenses.html
- Qt 6.8.3 LGPLv3 텍스트: https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/LGPL-3.0-only.txt
- esptool 5.4.0: https://github.com/espressif/esptool/blob/v5.4.0/LICENSE
- pyserial 3.5: https://raw.githubusercontent.com/pyserial/pyserial/v3.5/LICENSE.txt
- PyWinRT 3.2.1: https://raw.githubusercontent.com/pywinrt/pywinrt/v3.2.1/LICENSE

이번에는 개발 디렉토리를 변경하지 않았으며, 설치, 플래싱, 업로드도 하지 않았습니다. 결론은 "라이선스 수집 누락을 발견해 보완했으며, 명확한 배포 TODO가 남았다"이며, "모든 서드파티를 검토하고 승인했다"가 아닙니다.
