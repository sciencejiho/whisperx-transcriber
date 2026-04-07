# WhisperX 음성 변환기

[WhisperX](https://github.com/m-bain/whisperX) 기반 음성 파일 텍스트 변환 데스크톱 애플리케이션입니다. 화자 식별 기능을 지원하며, 한국어 기본 설정으로 90개 이상의 언어를 지원합니다.

**[English](../en-us/README.md)**

---

## 주요 기능

- **다국어 음성 인식** — Whisper large-v3 모델 사용 (한국어 기본, 90개 이상 언어 지원)
- **화자 분리** — 여러 화자를 자동으로 식별하고 라벨링
- **단어 단위 타임스탬프** — 정밀한 시간 정렬
- **내보내기** — TXT, SRT(자막), JSON 형식 지원
- **GPU 가속** — CUDA 자동 감지, CPU 자동 전환
- **드래그 앤 드롭** — Electron 기반 UI에서 실시간 진행 상황 표시

## 사전 요구 사항

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — Python 패키지 관리자
- **Node.js 18+** 및 npm
- **FFmpeg** — 오디오 디코딩용 (Linux에 보통 기본 설치됨)
- **(선택) NVIDIA GPU** + CUDA — CPU보다 훨씬 빠름

## 설치

### 1. Python 의존성 설치

```bash
uv sync
```

### 2. Electron 설치

```bash
cd electron
npm install
cd ..
```

### 3. HuggingFace 토큰 설정 (화자 분리용)

화자 분리 기능을 사용하려면 HuggingFace 토큰이 필요합니다. 먼저 아래 모델의 라이선스에 동의해 주세요:

- https://huggingface.co/pyannote/speaker-diarization-community-1

그런 다음 https://huggingface.co/settings/tokens 에서 토큰을 생성(Read 권한)하고 `.env` 파일에 추가하세요:

```bash
echo 'HF_TOKEN=hf_your_token_here' > .env
```

> 토큰이 없어도 음성 변환은 정상 작동합니다. 화자 라벨만 표시되지 않습니다.

## 사용법

### 데스크톱 앱 (Electron)

두 개의 터미널에서 API 서버와 Electron 앱을 각각 실행하세요:

```bash
# 터미널 1 — API 서버
uv run uvicorn api:app --reload

# 터미널 2 — Electron 앱
cd electron && npm start
```

1. 오디오 파일을 드래그하거나 클릭하여 선택 (MP3, WAV, M4A, FLAC, OGG 등)
2. **Transcribe** 버튼 클릭
3. 화자 라벨과 타임스탬프가 포함된 변환 결과 확인
4. TXT, SRT, JSON으로 내보내기

### 명령줄 사용

```bash
# 터미널에 출력 (기본 한국어)
uv run python transcribe.py audio.mp3

# 다른 언어 지정
uv run python transcribe.py audio.mp3 -l en

# 파일로 저장
uv run python transcribe.py audio.mp3 -o transcript.txt

# 화자 분리 없이 실행
uv run python transcribe.py audio.mp3 --no-diarize
```

## 내보내기 형식

| 형식 | 설명 | 용도 |
|------|------|------|
| **TXT** | 타임스탬프와 화자 라벨이 포함된 텍스트 | 읽기, 공유 |
| **SRT** | SubRip 자막 형식 | 동영상 플레이어, 자막 편집기 |
| **JSON** | start, end, text, speaker 구조화 데이터 | 프로그래밍 활용 |

### TXT 예시

```
[0.0s - 3.2s] SPEAKER_00: 안녕하세요 오늘은 날씨가 좋습니다
[3.5s - 6.1s] SPEAKER_01: 네 정말 좋네요
```

### SRT 예시

```
1
00:00:00,000 --> 00:00:03,200
SPEAKER_00: 안녕하세요 오늘은 날씨가 좋습니다

2
00:00:03,500 --> 00:00:06,100
SPEAKER_01: 네 정말 좋네요
```

## 프로젝트 구조

```
ai_notes/
├── transcribe.py       # 핵심 음성 변환 로직
├── api.py              # FastAPI 백엔드 서버
├── .env                # HuggingFace 토큰 (커밋되지 않음)
├── electron/
│   ├── main.js         # Electron 메인 프로세스
│   ├── index.html      # UI
│   └── package.json
└── docs/
    ├── en-us/README.md
    └── ko-kr/README.md
```

## 문제 및 해결 방안

### Linux에서 Electron 샌드박스 에러

SUID 샌드박스 에러가 발생하면 `package.json`에 이미 `--no-sandbox` 옵션이 설정되어 있습니다.

### 모델 다운로드가 느림

첫 실행 시 Whisper 모델(약 3GB)을 다운로드합니다. 이후에는 cache에서 로드되므로 빠르게 시작됩니다.
