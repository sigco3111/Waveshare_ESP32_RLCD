# 음성 출력(스피커) 진단 기록

작성일: 2026-11-03 · 대상 기기: Waveshare ESP32-S3-RLCD-4.2 (16 MB / 8 MB PSRAM)

## 결론 요약

**마이크 입력 경로는 정상이고, 스피커 출력 경로만 소리가 나지 않습니다.**

소프트웨어 파이프라인은 서버까지 정상적으로 동작합니다. 문제는 코덱(DAC) 이후, 즉
ES8311 DAC 출력 → PA 앰프 → 스피커 구간으로 좁혀졌습니다.

## 정상으로 확인된 구간

부팅 로그와 실측으로 확인된 항목입니다.

| 단계 | 확인 내용 | 결과 |
| --- | --- | --- |
| 웨이크워드 | `ni hao xi na` 감지 | 정상 |
| AFE | `AfeAudioEngine: Model 0: mn7_cn`, 게인 34.5 dB | 정상 |
| 마이크 → STT | `오늘 날씨 알려줘?` 로 업링크 | 정상 |
| 서버 응답 | TTS JSON 수신, `speaking → idle` 상태 전이 | 정상 |
| 암호화协商 | `aes-128-ctr` / `aes-gcm`, 포맷 `opus` | 정상 |
| UDP 오디오 | 서버 `47.76.65.170:8801`에서 패킷 수신 | 정상 |
| Opus 디코딩 | 60 ms 프레임 → 1440 samples (24000 Hz) | 정상 |
| 리샘플링 | `Resampling audio from 24000 to 16000` | 정상 |
| 코덱 기록 | `esp_codec_dev_write` 반환 0, 960 samples 기록 | 정상 |
| PA 출력 래치 | GPIO46 출력 래치 = 1 (HIGH) | 정상 |
| DAC 레지스터 | REG31=0x9f (음소거 아님), REG32=0xa8 (볼륨 정상), REG09/REG0A=0x0c (16 bit I2S) | 정상 |

즉 **서버 · 네트워크 · 암호화 · 디코딩 · 리샘플링 · 코덱 API 호출까지는 문제가 없습니다.**

## 정식 빌드에 반영한 수정

factory 펌웨어(소리가 난 기준 구현)와 대조하여 다음을 반영했습니다.

### 1. 재생 채널을 STD → TDM으로 전환

upstream Xiaozhi는 이 보드에서 **TX=STD, RX=TDM** 혼합 모드로 I2S를 구성합니다.
ESP32-S3 풀듀플렉스 I2S는 TX/RX가 클록을 공유하므로, 두 방향의 모드가 어긋납니다.

| | factory (소리 난 기준) | ESPHome (소리 난 설정) | upstream Xiaozhi (수정 전) |
| --- | --- | --- | --- |
| TX 모드 | TDM | STD | STD |
| RX 모드 | TDM | STD | TDM |
| 모드 일치 | 예 | 예 | **아니오** |

두 방향 모두 TDM으로 통일했습니다 (`xiaozhi/overlay/main/audio/codecs/box_audio_codec.cc`).

### 2. 입력 2채널 + channel_mask = 0

- `esp_codec_dev` 1.5.x는 입력과 출력의 채널 수가 같을 때만 peer 모드 확장을 건너뜁니다.
  다르면 **재생** 채널을 16 bit에서 32 bit 슬롯으로 재구성합니다
  (`Peer mode playback need extend bits 32 to 64`). ES8311 DAC은 16 bit I2S로
  설정되어 있으므로(REG09/REG0A=0x0c) 샘플을 래치하지 못합니다.
- `es7210_set_fs()`는 `channel <= 2 && channel_mask == 0`일 때만 샘플 폭을 절반으로
  낮춥니다. 채널 마스크가 남아 있으면 16 bit로 유지되어 ES7210 TDM 스트림과 맞지
  않고, 마이크 인식이 끝나지 않는 문제가 발생했습니다.

factory 기준선(`CodecPort_SetInfo("es8311 & es7210", 1, 16000, 2, 16)`)과 동일하게 맞췄습니다.

### 3. 출력 2채널 + 모노 → 스테레오 복제

코덱을 `channel = 1`로 열면 I2S 슬롯 마스크가 왼쪽 슬롯으로 좁혀져 DAC가 기대하는
프레임이 전달되지 않습니다. `channel = 2`로 열고 `Write()`에서 모노 샘플을 L/R로
복제합니다.

### 4. 샘플레이트 24000 → 16000

factory(`CodecPort_SetInfo(..., 16000, ...)`)와 ESPHome 모두 16000 Hz를 씁니다.
24000 Hz에서는 ES7210/ES8311 클록 디바이더가 기준값에서 벗어나며, AFE 출력도
리샘플링이 필요했습니다.

## 시도했고 되돌린 변경

모두 실측으로 효과가 없어 원복했습니다.

| 변경 | 결과 |
| --- | --- |
| ES8311 REG09/REG0A bit6 = 1 (`0x0c → 0x4c`) | 소리 없음. factory는 set 후 clear로 상쇄하므로 최종 상태와 불일치 → 원복 |
| 3단계 테스트 톤 (1000/1500/2000 Hz, 슬롯 설정 3종) | **3종 모두 무음** → DAC/PA 물리 경로로 확정 |
| 모노 → 스테레오 복제만 적용 | 소리 없음 |
| 16000 Hz만 적용 | 소리 없음 (마이크는 정상화) |

### factory 최종 상태와의 잔여 차이

1.5.11 `esp_codec_dev`는 TDM 분기에서 `left_align = true`를 강제합니다.
factory는 TDM 기본값인 `false`를 유지합니다. 3단계 테스트 톤으로 `left_align`를
false로 바꾼 경우까지 포함해 확인했으나 **어느 조합에서도 소리가 나지 않았습니다.**

## 남은 가설

1. **DAC 아날로그 출력 단계** — 레지스터는 정상으로 보이으나 ES8311의 DAC 전원이
   실제로 살아 있는지(내부 PLL / 아날로그supply) 확인 필요.
2. **PA 앰프 구동 조건** — GPIO46 출력 래치는 HIGH이나, `gpio_get_level()` 은 계속 0을
   반환합니다. ESP32-S3 GPIO46의 입력 버퍼 특성인지, 외부 회로가 LOW로 고정하는지
   구분하지 못했습니다. factory의 GPIO 설정 코드는 Syna와 소스째 동일합니다.
3. **물리적 결함** — 사용자는 스피커가 이전에는 정상 동작했다고 보고했으나, 공식
   factory 펌웨어(`ESP32-S3-RLCD-4.2_FactoryOnly_20260120.bin`)을 플래시한 뒤의
   청각 확인이 남아 있습니다.

## 다음에 할 일

1. 공식 factory 펌웨어를 플래시하고, 부팅 후 기본 화면에서 **KEY 버튼(GPIO18)을 눌러
   내장 음악이 들리는지** 확인합니다. 들린다면 하드웨어는 정상이고 Syna 쪽 포맷
   문제로 범위가 좁혀집니다.
2. 들리지 않는다면 스피커/PA 하드웨어 경로를 의심합니다.
3. factory가 소리를 낸다면, factory의 `CodecPort_PlayWrite`가 모노 PCM을 L/R 복제 없이
   그대로 넘긴다는 점과, Syna의 복제 경로를 비교해 포맷을 맞춥니다.

## 재현 방법

```bash
# 1) 정규화된 upstream 트리 준비 (upstream.lock 의 커밋)
git clone https://github.com/78/xiaozhi-esp32.git
git checkout 5df5b7fb4da2b4d80e2b7f87285ec1f8a9ca565c

# 2) 보드 오버레이 적용 (오디오 코덱 포함)
python3 xiaozhi/apply_ui_overlay.py <tree> --phase source
python3 xiaozhi/apply_ui_overlay.py <tree> --phase components

# 3) 빌드 (ESP-IDF 6.0.2)
cd <tree>
idf.py -DIDF_TARGET=esp32s3 '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;syna.sdkconfig.defaults' \
       -DBOARD_NAME=esp32-s3-rlcd-4.2 build
```

진단용 로그는 정식 빌드에 포함되지 않습니다. 이 문서에 적힌 값들은 별도의 임시
진단 빌드로만 측정했고, 그 로그 코드와 테스트 톤은 모두 제거한 상태입니다.
