# UI 에셋 안내

현재 홈 화면은 사용자 제공 400×300 흑백 음악 상태 화면 레퍼런스에서 재구성했습니다. 모든 아이콘은 내장 이미지 생성 모드로 각각 생성해 `source/music_ui_icons/`에 저장합니다. `generate_assets.py`는 이들을 자르고, 크기를 조정하고, 색상을 바꾸고, 배치하고, 이진화만 하며, 드로잉 코드로 아이콘을 다시 그리지 않습니다.

## 현재 아이콘과 생성 프롬프트

| 파일 | 최종 크기 | 이미지 생성 프롬프트 요약 |
| --- | ---: | --- |
| `clock.png` | 22×22 | 레퍼런스 상단의 둥근 픽셀 시계를 추출하며, 팔각형 외곽선, 시침, 분침, 계단식 픽셀을 유지합니다. |
| `thermometer.png` | 18×32 | 레퍼런스와 일관된 세로 온도계를 생성합니다. 좁은 관, 중앙 지시선, 둥근 베이스를 포함합니다. |
| `humidity.png` | 18×29 | 뾰족한 위쪽, 둥근 아래쪽, 빈 중앙, 왼쪽 아래의 작은 내부 하이라이트가 있는 픽셀 물방울을 생성합니다. |
| `agent_status.png` | 23×23 | 굵은 바깥 링, 안쪽 링, 짧은 쐐기가 있는 중심점을 생성하며, 실행 상태 기호로 사용합니다. |
| `waveform.png` | 24×16 | 짧음, 중간, 김, 중간, 짧음 순서의 네모 끝 재생 파형 막대 다섯 개를 생성합니다. |
| `music_note.png` | 28×35 | 채워진 음표 머리 둘, 세로 기둥 둘, 계단식 연결 빔이 있는 굵은 음악 기호를 생성합니다. |
| `artist.png` | 12×12 | 네모 머리, 어깨, 평평한 베이스로 이루어진 작은 아티스트 아이콘을 생성합니다. |
| `wifi.png` | 20×14 | 세 개의 호와 하나의 실점(dot)으로 이루어진 Wi-Fi 아이콘을 생성합니다. |
| `desktop.png` | 19×14 | 직사각형 모니터, 짧은 스탠드, 평평한 베이스로 이루어진 기기 아이콘을 생성합니다. |
| `laptop.png` | 18×14 | 화면 외곽선, 경첩, 중앙에 홈이 있는 베이스로 이루어진 컴퓨터 연결 아이콘을 생성합니다. |
| `battery.png` | 35×14 | 배터리 외곽선, 오른쪽 단자, 정확히 네 개의 실 충전 세그먼트를 생성합니다. |

모든 프롬프트는 다음 제약을 공유합니다: 순수 블랙 1비트 픽셀 그래픽, 완전히 투명한 배경, 계단식 픽셀 가장자리 유지, 텍스트 없음, 그레이스케일 없음, 그림자 없음, 패널 없음, 워터마크 없음, 여분 요소 없음. 에이전트 아이콘은 합성 시 흰색으로 다시 칠해져 레퍼런스의 검은 상태 캡슐과 일치합니다.

## 레거시 에셋

`source/icons/`와 `source/ciallo_maid_pixel_transparent.png`는 이전 버전 상태 홈 화면의 에셋입니다. 현재 음악 상태 홈 화면은 이들을 참조하지 않지만, 롤백이나 다른 화면 제작에 쓸 수 있도록 일단 유지합니다.

## LVGL 에셋 재생성

```bash
python3 simulator/assets/generate_assets.py
```

생성기는 이식 가능하며 Pillow와 내장 LVGL 이미지 변환기가 필요합니다(변환기용으로 `pypng`와 `lz4`, `PATH`상의 `pngquant`).

출력물에는 `generated/screen_base.png`와 직접 링크할 수 있는 `src/assets/`의 LVGL 1비트 C 배열이 포함됩니다.

## 폰트 재생성

```bash
cd simulator/assets
python3 generate_cjk_codepoints.py    # fonts/cjk-codepoints.json 재생성
python3 generate_ui_fonts.py           # ui_font_*.c 재생성 (Pillow + fontTools 필요)
```

### CJK 코드포인트 목록

`fonts/cjk-codepoints.json` 은 `ui_font_14_cjk` 가 어떤 글자를 그릴 수 있는지 정합니다. **직접 편집하지 말고 스크립트로 만드세요.**

- `fonts/cjk-codepoints.base.json` — 출발점. 한자와 일본어를 제거하기 전의 원본 목록입니다. 이 파일을 보존해야 기호·화살표·상자그림 글리프가 유지됩니다.
- `generate_cjk_codepoints.py` — base 목록에서 한자(`HAN_BLOCKS`)와 일본어(`KANA_BLOCKS`)를 빼고, 한글 음절·자모 전체를 넣습니다.

현재 목록에는 **한글 완성형 음절 11,172개가 모두 들어 있습니다.** 한자와 일본어를 뺀 이유는 용량입니다. Unifont 16px 에서 한자·한글·일본어 글리프의 크기가 모두 32 bytes 로 같아, 한자·일본어를 빼고 그 자리를 한글로 채우면 크기가 거의 상쇄됩니다.

한자나 일본어가 다시 필요하면 `HAN_BLOCKS` / `KANA_BLOCKS` 를 고쳐 스크립트를 다시 돌리고, 이어서 `generate_ui_fonts.py` 를 실행하세요. 그 다음 `simulator/src/assets/` 와 `xiaozhi/overlay/main/boards/waveshare/esp32-s3-rlcd-4.2/` 양쪽의 `ui_font_14_cjk.c` 가 같은 내용인지 확인해야 합니다.

### 한글 렌더 확인

```bash
cd simulator
AI_PANEL_MEDIA_DEMO=ko AI_PANEL_KOREAN_DEMO=1 AI_PANEL_START_PAGE=syna \
  AI_PANEL_SCREENSHOT_PATH=/tmp/korean.png ./build/bin/ai_panel_simulator
```

`AI_PANEL_MEDIA_DEMO=ko` 는 음악 영역에, `AI_PANEL_KOREAN_DEMO=1` 은 Syna 말풍선에 한글을 넣습니다.

