### 📁 원하는 경로 만들기 및 폴더 트리

<aside>
<img src="notion://custom_emoji/be63ac5b-4886-448b-8129-bb134d9b3f0c/1fc73fc3-dccb-806e-b68b-007a34a7ac64" alt="notion://custom_emoji/be63ac5b-4886-448b-8129-bb134d9b3f0c/1fc73fc3-dccb-806e-b68b-007a34a7ac64" width="40px" />

아래 명령어 한 줄로 요청하신 라즈베리파이 프로젝트 폴더 구조를 한 번에 만들 수 있어요:

```bash
mkdir -p ~/autocarz/{data/{images,videos},src,models,notebooks} && touch ~/autocarz/src/{__init__.py,main.py,camera.py,motor.py} && touch ~/autocarz/{config.ini,README.md}

```

```bash

📁 원하는 경로 만들기

mkdir -p ~/autocarz/image
~/는 현재 사용자 홈 디렉토리 (/home/pi)를 의미합니다.

autocarz/image는 폴더를 중첩 생성합니다.

📷 사진 촬영 (지정한 경로)

libcamera-still -o ~/autocarz/image/test.jpg
🎥 영상 녹화 (지정한 경로, 10초 녹화)

libcamera-vid -t 10000 -o ~/autocarz/image/test.h264
📂 저장 위치 확인

ls ~/autocarz/image
이 명령으로 폴더 내에 촬영한 test.jpg, test.h264 파일이 나옵니다.

📦 참고: 절대경로로 하고 싶다면?
/home/pi/autocarz/image/test.jpg
```

실행 결과는 다음과 같은 구조가 됩니다:

```
/home/pi/autocarz/
├── 📁 models/               # YOLO 모델 가중치 저장 (예: best.pt)
│   └── best.pt
├── 📁 pi_detected_images/   # 감지된 이미지 자동 저장 폴더
├── 📁 src/                  # 모든 실행/모듈 코드가 여기에 있음
│   ├── main.py             # 💡 메인 실행 파일 (여기만 실행하면 OK!)
│   ├── yolo_detector.py    # YOLO 감지만 담당 (detector 모듈)
│   ├── yolo_visualizer.py  # 감지 결과 이미지에 시각화
│   ├── pi_camera.py        # Picamera2 단독 테스트
│   ├── hardware_controller.py  # 부저/LED 제어
│   ├── 8_web_streamer.py   # Flask + YOLO 웹 스트리밍
│   └── __init__.py
├── config.ini              # 설정값 정의
├── .gitignore
├── README.md
└── venv/                   # Python 가상환경

```

---

## ✅ 라즈베리파이 초기 환경 세팅

### 폴더 생성 명령어

```bash
mkdir -p ~/autocarz/{data/{images,videos},src,models,notebooks} && touch ~/autocarz/src/{__init__.py,main.py,camera.py,motor.py} && touch ~/autocarz/{config.ini,README.md}
```
/home/pi/autocarz/
# ✅ autocarz 디렉토리 구조 (YOLO 감지 중심 기반)

# ─────────────────────────────────────────────
# 📂 src/ ── 실제 코드 파일 (YOLO + 하드웨어 제어)

📂 src
├── main.py                  # 💼 전체 시스템 조정 (entry point)
├── yolo_detector.py         # 🕵️ YOLO 모델 로딩 및 탐지 기능
├── yolo_visualizer.py       # 🎨 YOLO 탐지 결과 시각화
├── yolo_camera.py           # 📸 카메라 캡처 및 에러 처리
├── hardware_controller.py   # 🧭 아두이노, 부저, LED 제어
├── alert_sender.py          # 🌐 Flask 서버 POST 전송 등 외부 연동
├── utils.py                 # 🛠️ 공통 유틸 함수 (타임스탬프, 파일 저장 등)
└── __init__.py


# ─────────────────────────────────────────────
# 📂 models/ ── 학습된 모델 보관 폴더 (깃허브에는 올리지 않음)

📂 models
└── best.pt                 # 🎯 훈련된 YOLOv8 모델


# ─────────────────────────────────────────────
# 📂 pi_detected_images/ ── 고라니 탐지 시 저장되는 결과 이미지

📂 pi_detected_images        # 💾 감지된 프레임 저장 위치
└── capture_20250715_0930.jpg  # 예시 결과 이미지


# ─────────────────────────────────────────────
# 📜 기타 루트 파일

📜 .gitignore                # 📁 훈련 결과, 이미지 저장 제외
📜 config.ini                # ⚙️ 모델 경로, 임계값 등 설정파일
📜 README.md                 # 📘 프로젝트 개요 설명


# ─────────────────────────────────────────────
# ✅ 기타 규칙

# • 카메라 테스트만 할 땐: `yolo_camera.py` 단독 실행 가능
# • 추론만 빠르게 테스트할 땐: `yolo_detector.py` + `cv2.imread()`
# • 실제 전체 시스템: `main.py` 실행


# 원한다면 `test/` 폴더, `notebooks/` 폴더도 추가 가능


```

</aside>

### 카메라 명령어

```bash
vcgencmd get_camera      # → supported=1 detected=1 이면 OK
libcamera-hello          
```

### 사진/영상 저장 예시

```bash
# 사진 저장
libcamera-still -o ~/autocarz/image/test.jpg

# 영상 저장 (10초)
libcamera-vid -t 10000 -o ~/autocarz/image/test.h264

# 자동 타임스탬프 포함 저장
libcamera-still -o /home/pi/autocarz/data/images/photo_$(date +%Y%m%d_%H%M%S).jpg
💡 자동으로 타임스탬프가 파일 이름에 붙습니다.
예: photo_20250709_143025.jpg

🎥 영상 녹화 (10초, H.264 형식)

libcamera-vid -t 10000 -o /home/pi/autocarz/data/videos/video_$(date +%Y%m%d_%H%M%S).h264
-t 10000: 10초 녹화 (단위 ms)

-o: 저장 경로 지정

# 사진 촬영
libcamera-jpeg -o my_photo.jpg

# 미리보기 없이 사진 촬영
libcamera-jpeg -n -o silent_photo.jpg

# 영상 촬영 (5초)
libcamera-vid -t 5000 -o my_video.h264
```

### 파일 및 폴더 목록 보기 라이브러리

```bash

ls -al
시스템 최신 상태로 업데이트하기 (추천)

# 패키지 목록을 최신화하고, 설치된 패키지를 업그레이드합니다.
sudo apt update && sudo apt upgrade -y
시스템 정보 예쁘게 보기 (설치 필요할 수 있음)

# neofetch가 없다면 'sudo apt install neofetch'로 설치하세요.
neofetch
```

---

### ✅ best.pt 모델 파일을 라즈베리파이로 전송하는 방법 (SCP 사용)

💻 명령어 구조

```bash
scp [보낼_파일_경로] pi@[라즈베리파이_IP주소]:[받을_폴더_경로]
```

🔧 상황에 맞춘 실제 명령어 예시

```bash
scp "C:\Users\Admin\Desktop\LYSS_LGU\aihub_gorani\after_train\goral_yolov8_run2\weights\best.pt" pi@192.168.14.63:/home/pi/autocarz/
```

### ※ 192.168.14.63은 예시 IP이므로, 실제 IP는 라즈베리파이에서 아래 명령어로 확인해 주세요:

```bash
hostname -I
```

### 📌 주의사항

scp는 WSL 또는 Git Bash, MINGW64, PowerShell에서도 동작합니다.

Windows 기본 명령 프롬프트(cmd)는 scp가 없을 수도 있습니다.

안 된다면 VSCode 터미널이나 Git Bash에서 실행하세요.

전송 완료 후, 라즈베리파이에서 파일이 잘 왔는지 확인:

```bash

ls /home/pi/autocarz/
```
## 🛠️ YOLOv8 + Flask 웹 스트리밍 구축

### 필수 빌드 도구 설치

```bash
sudo apt update
sudo apt install -y build-essential python3-dev libjpeg-dev
```

### 가상환경 생성 및 의존 패키지 설치

```bash
cd ~/autocarz
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install ultralytics opencv-python flask
pip install --ignore-installed --no-binary :all: simplejpeg
```

---

## 🚀 실행 방법

```bash
source ~/autocarz/venv/bin/activate
python src/8_web_streamer.py
```

웹 브라우저에서 접속:  
```
http://<라즈베리파이 IP>:5000/
```

> IP 확인: `hostname -I`

---

## 💾 best.pt 모델 전송 (SCP)

```bash
scp /local/path/best.pt pi@<라즈베리파이_IP>:/home/pi/autocarz/models/
```

예시:
```bash
scp "C:\Users\Admin\Desktop\best.pt" pi@192.168.0.41:/home/pi/autocarz/models/
```

> IP 주소는 `hostname -I`로 확인 가능

---

## 🧭 유틸 명령어 모음

```bash
ls -al                                 # 폴더 내용 보기
sudo apt update && sudo apt upgrade   # 시스템 최신화
neofetch                               # 시스템 정보 출력
```

---

## 📌 기타 실행 가이드

| 목적 | 파일 |
|------|------|
| 전체 시스템 실행 | `main.py` |
| YOLO 추론 단독 | `yolo_detector.py` |
| 카메라 단독 테스트 | `pi_camera.py` |
| 웹 스트리밍 서버 | `8_web_streamer.py` |

---