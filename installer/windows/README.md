# Windows 올인원 설치 프로그램

소스 진입점은 installer_ui.py, 백엔드 프로토콜 워커는 worker.py, 독립 백엔드 진입점은 backend_entry.py입니다. 릴리스 디렉토리에는 페이로드, 생성된 매니페스트, EXE가 포함되지 않습니다.

빌드 방법: [통합 가이드](../../docs/BUILD.md). build_standalone.py에는 --firmware-build와 --reporter-exe를 반드시 제공해야 하며, prepare_payload.py도 같은 두 매개변수를 받아 테스트 파일을 별도로 준비할 수 있습니다.

생성 후 dist/SynaInstaller-1.0.0.exe를 실행하세요. 읽기 전용 셀프 테스트 명령: SynaInstaller-1.0.0.exe --self-test <절대 보고서 경로.json>, 설치나 플래싱을 수행하지 않습니다.

세 가지 모드: Reporter 전용 설치, 설정 유지 업그레이드, 최초 설치. Reporter 전용은 시리얼 포트에 접근하지 않습니다. 업그레이드는 파티션을 백업하고 검증한 뒤 앱 영역만 쓰고, 최초 설치는 지우기 전 확인이 필요하며 전체 백업 검증 후에만 지웁니다. 마지막에 읽기 되돌림 검증과 리셋을 수행합니다. 실패해도 자동 롤백되지 않으므로 백업을 보관하세요.

백엔드는 ASCII JSON 이스케이프를 사용해 메시지를 전달하므로 Windows 코드 페이지 오류를 피할 수 있습니다. 최종 성공에는 완료 이벤트와 정상 종료가 모두 필요합니다.

현재 작성자의 독립 Reporter 설치와 설정 유지 플래싱 검증은 성공했습니다. 새 디렉토리에서의 재빌드, 다른 PC, 최초 설치, 음성 테스트는 아직 검증이 필요합니다. %LOCALAPPDATA%/SynaInstaller/Backups의 백업에는 개인 데이터가 포함되므로 소스 저장소에 커밋하지 마세요.
