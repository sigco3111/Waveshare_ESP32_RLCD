# Syna Reporter (Windows / macOS)

macOS 기본 버전은 이식된 것입니다. `start.command`를 더블클릭해 시작하거나 `dist-macos/SynaReporter.app`을 사용하세요. 기능 범위, 로그인 시 자동 시작, 테스트는 [macOS 사용법](MACOS.md)에서 다룹니다. Windows 상태 창은 Mac 레이아웃을 포팅한 것으로, 2026-09-14에 첫 번째 실기 Windows 검증을 마치고 새 `dist/SynaReporter.exe`를 빌드했습니다. 사용법과 남은 검증 항목은 [Windows 창 안내](WINDOWS-UI.md)에 있습니다. NetEase Cloud Music, NVIDIA 지표, 아래 설치 방법은 Windows에 적용됩니다.

Windows의 현재 주 진입점은 `installer/windows`의 올인원 설치 프로그램이며, 독립 설치는 작성자 본인의 기기에서 인수 확인을 마쳤습니다. 정리된 소스 디렉토리에는 미리 빌드된 EXE가 포함되어 있지 않으므로, [빌드 안내](../docs/BUILD.md)에 따라 생성하세요.

현재 로컬 빌드를 직접 실행하려면:

```text
dist\SynaReporter.exe
```

아래 경로는 유지 중인 독립 Reporter 패키징 스크립트의 출력물이며, 이번 통합 릴리스의 진입점이 아닙니다:

```text
release\SynaReporter-Setup-1.0.0.exe
```

설치된 단일 파일 프로그램은 Python 런타임과 모든 의존성을 내장하며, 설치 후 로그인 시 자동으로 시작합니다. 창이 관리하는 워커가 비정상 종료되면 자동으로 복구되며, 명시적 명령줄 백그라운드 모드에서는 슈퍼바이저가 유지됩니다. 설치 프로그램은 Private 네트워크에 대해서만 UDP 8766 인바운드 규칙을 추가합니다. 개발자는 소스에서 시작하세요:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\start.ps1
```

첫 실행 시 `reporter/.venv`에 격리된 Python 환경을 만들고 `psutil`과 Windows Runtime 미디어 인터페이스를 설치합니다. Reporter가 수신 대기하는 포트는 다음과 같습니다:

- HTTP `8765`: `/api/v1/health`, `/api/v1/status`
- UDP `8766`: `AI_PANEL_DISCOVER_V1`에 응답하고, 컴퓨터 식별 정보, 에이전트 상태, 성능 스냅샷도 함께 반환합니다

안정적인 `reporter_id`와 컴퓨터 이름은 `%LOCALAPPDATA%\AIAgentPanel\reporter.json`에 저장됩니다.

첫 시작 시 Reporter는 무작위 페어링 토큰과 지문도 함께 생성합니다. 새 보드는 최초 검색 시 발견한 안정적인 Reporter ID와 지문을 자동으로 저장하므로 사용자가 토큰을 복사할 필요가 없습니다. 수동 토큰은 구형 펌웨어 호환이나 고급 필터링용으로만 사용합니다. 로컬 진단 엔드포인트 `http://127.0.0.1:8765/api/v1/pairing`은 여전히 로컬 접근만 허용하며, 평문 토큰을 LAN으로 반환하지 않습니다.

현재 버전은 읽기 전용 상태 엔드포인트만 노출하며, 프롬프트, 코드, 파일 내용, API 키를 읽지 않습니다. 첫 LAN 테스트 중 Windows 방화벽 알림이 뜨면 Private 네트워크만 허용하세요.

보드와 컴퓨터는 서로 도달 가능한 같은 Wi-Fi나 휴대폰 핫스팟에 있어야 합니다. 시작에 성공한 뒤 컴퓨터의 브라우저에서 확인하세요:

```text
http://127.0.0.1:8765/api/v1/health
http://127.0.0.1:8765/api/v1/status
```

현재 MVP 성능 데이터에는 CPU, 메모리, GPU, 디스크 사용량, GPU 온도, 실시간 네트워크 속도가 포함됩니다. Windows에 일반적으로 신뢰할 수 있는 CPU 온도 인터페이스가 없으면 값은 `null`이며 화면에 `--`로 표시됩니다. NVIDIA GPU 지표는 `nvidia-smi`에서 가져오며, NVIDIA GPU가 없으면 GPU 항목에 `--`가 표시됩니다.

## Codex 에이전트 상태

Reporter는 먼저 Codex 로컬 `logs_2.sqlite`에서 고정 형식의 작업 시작/종료 마커를 추출하고, 프로세스 PID와 생성 시간을 결합해 살아 있는 활동 수를 집계합니다. 로그 본문은 읽거나 보고하지 않습니다. 해당 로그 형식은 클라이언트 버전에 따라 달라집니다. 마커가 없으면 `thread_history_1.sqlite`의 `thread_turns` 상태를 읽기 전용으로 조회하는 방식으로 대체하고, `state_5.sqlite`에서 일치하는 작업 공간 이름을 가져옵니다. `inProgress` 턴이 존재하는 동안 상태는 "Working"으로 표시되고, 가장 최근 턴이 끝난 뒤에는 잠시 "Done"이 표시되며, Codex 프로세스는 있으나 활성 턴이 없으면 상태는 "Idle", 프로세스가 종료되면 "Not running"으로 표시됩니다. 여러 Codex 세션이 동시에 실행 중이면 `active_count`가 활성 세션 수를 반환합니다.

이 방식은 VS Code Hook에 의존하지 않으며, `thread_items`, 프롬프트, 대화, 코드, 도구 인수, 터미널 출력을 읽지 않습니다. UDP로는 화면에 집계 상태, 활성 수, 작업 공간 이름의 마지막 경로 조각만 전송합니다.

정식 설치 버전은 더 이상 VBS를 사용하지 않습니다. 설치 프로그램은 숨겨진 슈퍼바이저를 시작하는 시스템 시작 항목을 기록하며, 실행 로그는 `%LOCALAPPDATA%\AIAgentPanel\reporter.log`에 있습니다. VS Code 프로세스와 독립적이므로 상태 동기화에 `Developer: Reload Window`가 더 이상 필요하지 않습니다.

## Codex 쿼터

Reporter는 30초마다 로컬 Codex App Server의 `account/rateLimits/read`를 통해 계정 한도를 읽고, `usedPercent`를 남은 비율로 환산한 뒤 `windowDurationMins`로 단기 쿼터와 주간 쿼터를 구분합니다. 데이터는 컴퓨터 상태와 함께 UDP로 화면에 전송되며, 창에 신뢰할 수 있는 데이터가 없으면 화면에 `--`가 표시되고, 고정값이나 로컬 토큰 소모량 추정치을 사용하지 않습니다.

이미 현재 컴퓨터에 로그인된 Codex 클라이언트를 사용하며, 읽기 전용 한도 엔드포인트만 호출하고, 인증 토큰, 프롬프트, 대화, 코드를 읽지 않습니다. Codex 클라이언트 업그레이드 후 로컬 App Server 프로토콜이 바뀌면 Reporter 어댑터도 그에 맞게 업데이트해야 합니다.

Codex에 로그인하지 않은 상태에서는 Reporter가 즉시 이전 쿼터를 지우고 로그인이 필요한 상태로 보고합니다. 화면에는 "Please log in"이 표시되고 두 쿼터 항목 모두 `--`가 표시됩니다. 로그인에 성공하면 늦어도 다음 30초 폴링 시점에 값이 복원됩니다.

## 음악 재생 정보와 가사

Reporter는 Now Playing 정보를 읽기 전용으로 수집합니다.

- macOS: `MediaRemote` private API를 통해 등록된 앱의 곡 제목, 아티스트, 재생 상태, 진행률을 읽습니다. 브라우저(YouTube 등)를 포함한 어떤 앱이든 Now Playing을 등록하면 수집됩니다. UI 스크립팅이나 플레이어 제어는 하지 않습니다.
- Windows: `GlobalSystemMediaTransportControlsSessionManager` 를 사용하며, NetEase Cloud Music 은 CDP 채널(`127.0.0.1:9223`)과 창 제목·로컬 `playingList` 로 정밀 정보를 읽습니다. 다른 앱은 미디어 세션을 통해 수집됩니다.

NetEase Cloud Music 3.1.39 같은 최신 빌드에서 Windows 미디어 세션을 비활성화하면, Reporter는 창 제목과 로컬 `playingList`에서 현재 노래, 아티스트, 노래 ID, 재생 시간을 읽기 전용으로 읽으므로, 일반적인 바로가기 실행으로는 전체 미디어 블록이 사라지지 않습니다. 정확한 진행률을 위해서는 다음을 실행하세요:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\start_netease_precise.ps1 -Restart
```

이 스크립트는 먼저 기존 NetEase Cloud Music 프로세스를 완전히 종료한 뒤 정밀 모드로 시작하고, 포트가 실제로 사용 가능한지 검증합니다. 검증에 실패하면 오류를 명확히 보고하므로, "시작된 것처럼 보이지만 실제로 미디어 정보가 없는" 경우가 더 이상 발생하지 않습니다. NetEase Cloud Music을 수동으로 종료한 뒤에는 이 스크립트로 시작하세요.

곡이 바뀌면 Reporter는 먼저 NetEase Cloud Music 로컬 캐시 파일 이름에서 후보 노래 ID를 파싱한 뒤 노래 제목과 아티스트로 엄격히 검증합니다. 캐시 일치가 없을 때만 NetEase Cloud Music 검색 엔드포인트를 호출합니다. 브라우저 제목에는 설명 문구가 섞여 있으므로 (`IU 'Love wins all' Live Clip (2024 TOUR ...)`) 인용부나 괄호 안의 곡명을 먼저 추출해 검색하고, 검색어에는 곡명만 넣어 검색 백엔드가 제목을 쪼개지 않게 합니다. 가사는 LRC 타임스탬프로 현재 재생 위치에 맞추며, 네트워크를 사용할 수 없거나, 노래에 가사가 없거나, 신뢰할 수 있는 일치가 없으면 화면에 "No lyrics"가 표시되고, 동명 커버곡의 가사가 적용되지 않습니다. 노래 ID와 가사는 다음 곡 변경까지 캐시되므로, 정상 재생 중에는 네트워크를 반복 요청하지 않습니다.

가사는 YouTube 등 브라우저가 아니라 **NetEase Cloud Music API**에서 가져옵니다. 곡이 NetEase에 없다면 가사만 "No lyrics" 로 표시되고 곡 제목·아티스트·진행률은 정상 동작합니다.

홈 화면 폰트는 일반적인 중국 한자, 일본 히라가나, 가타카나, 반각 가타카나, JIS 한자를 포함하므로, 중국어와 일본어 노래 제목, 아티스트, 한 줄 가사를 동적으로 표시할 수 있습니다. 아무 앱도 재생 중이 아니거나, 방금 재시작해 아직 노래를 불러오지 않았거나, 재생 중이 아니면 화면에 "Not playing"이 표시됩니다.

ESP32 실시간 데이터 링크는 UDP 요청/응답을 사용하므로 HTTP `8765`에 대한 Windows TCP 인바운드 규칙이 필요 없습니다. HTTP 엔드포인트는 로컬 진단 진입점일 뿐입니다. 공용 네트워크에 대해서는 방화벽 권한을 열지 말고, 공유기에서 포트 포워딩을 설정하지 마세요.

보드는 최대 8개의 Reporter 검색, 목록 페이징, 현재 컴퓨터 선택, 안정적인 Reporter ID와 기억된 지문으로 현재 선택 고정을 지원합니다. 보드 자체는 Wi-Fi STA MAC을 안정적인 ID로 사용합니다. 이 메커니즘은 여러 컴퓨터와 보드 사이의 오연결을 방지하기 위한 것으로, 악의적인 LAN 공격에 대한 보호와 동등하지 않습니다. 무작위 논스와 해지 목록을 사용한 양방향 메시지 인증은 이후 보안 강화에서 추가할 예정입니다. 에이전트 상태와 쿼터는 이제 Codex에 연결되어 있습니다. 음악 정보는 Now Playing 을 등록하는 모든 앱(브라우저 포함)에서 수집하며, 가사는 NetEase Cloud Music API 에서 가져옵니다.

릴리스 패키지 빌드:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\build_release.ps1 -Version 1.0.0
```
