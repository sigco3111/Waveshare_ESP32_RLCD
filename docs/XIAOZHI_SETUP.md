# Xiaozhi 설정

1. 보드 최초 부팅 후 화면 안내에 따라 기기 핫스팟에 연결하고, 안내된 설정 페이지를 열어 사용 가능한 Wi-Fi를 설정하세요. 컴퓨터 바인딩과 Wi-Fi 설정은 기기 페이지에서 완료됩니다.
2. 브라우저에서 https://xiaozhi.me/ 를 열고 로그인한 뒤 "콘솔"로 들어갑니다.
3. 기기에 활성화 코드가 표시되거나 안내되면 콘솔 안내에 따라 기기를 추가하고 현재 활성화 코드를 입력해 본인 계정 또는 에이전트에 바인딩하세요. 이미 바인딩된 기기는 먼저 원래 계정에서 조회하세요. 플래시를 지운다고 클라우드 바인딩이 반드시 해제되는 것은 아닙니다.
4. 기기와 연결된 에이전트에서 "역할 설정"을 열어 역할 페르소나, 음성, 페이지에서 제공하는 모델 옵션을 설정하고 저장한 뒤 다시 웨이크업해 테스트하세요. 반영되지 않으면 기기를 재시작하세요.
5. Xiaozhi 콘솔은 음성 대화 설정용입니다. 컴퓨터 성능, 에이전트, 음악 데이터에는 컴퓨터 측 Reporter가 필요하며, 보드에서도 컴퓨터를 선택해야 합니다.

활성화 코드가 없으면 먼저 기기가 이미 온라인인지 확인하세요. 이미 정상적으로 대화할 수 있는 기기는 대개 다시 활성화할 필요가 없습니다. 콘솔 항목 이름은 웹 페이지에 실제 표시되는 대로 따릅니다.

바인딩이 완료되면 보드 상태가 `activating → idle` 로 바뀌며, 재부팅 후에도 유지됩니다.

## MiniMax 잔액 설정

Xiaozhi 콘솔과 별개로, 보드 화면의 잔액 표시를 채우려면 보드 설정 페이지의 **API Balance** 항목에서 MiniMax API를 직접 지정해야 합니다. MiniMax를 지정해도 AI 음성 대화는 Xiaozhi 클라우드를 그대로 사용합니다.

| 항목 | 값 |
| --- | --- |
| Provider Display Name | `MiniMax` |
| API Base URL | `https://api.minimax.io/v1` |
| API Key | MiniMax에서 발급한 키 |
| Balance Fetch Method | `Custom HTTP endpoint` |
| Balance Endpoint URL | `https://api.minimax.io/v1/token_plan/remains` |
| Request Method | `GET` |
| Authentication | `Bearer` |
| Header / Parameter Name | `Authorization` |
| Balance JSON Path | `model_remains[0].current_weekly_remaining_percent` |
| Fixed Unit | `%` |
| Numeric Scale | `1` |
| Unit JSON Path | 비움 |
| POST JSON | 비움 |

`model_remains` 는 배열이므로 `Balance JSON Path` 에 `[0]` 인덱스를 반드시 넣어야 합니다. 빠지면 화면에 `--` 만 표시됩니다.
