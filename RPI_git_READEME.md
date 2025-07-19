# 라즈베리파이 > 안전 Git 업데이트 가이드

## 🔍 현재 상황 파악

라즈베리파이에서 실행:

```bash
cd /home/pi/autocarz
pwd                    # 현재 위치 확인
git status            # Git 상태 확인
git branch            # 현재 브랜치 확인
ls -la                # 파일 목록 확인
```

## 🛡️ 1단계: 중요 파일 백업

```bash
# 혹시 모를 상황 대비 백업
cp README.md README_backup.md
cp requirements.txt requirements_backup.txt
cp .gitignore .gitignore_backup

# 모델 파일 위치 확인 (절대 건드리면 안 됨)
ls -la models/
ls -la pi_detected_images/
```

## 📡 2단계: 원격 저장소 정보 가져오기

```bash
# 원격 저장소에서 최신 정보만 가져오기 (파일 변경 안 함)
git fetch origin raspberrypi

# 어떤 파일이 다른지 미리보기
git diff HEAD origin/raspberrypi --name-only
```

## 📝 3단계: README.md만 선택적 업데이트

```bash
# README.md 파일만 업데이트
git checkout origin/raspberrypi -- README.md

# 확인해보기
head -10 README.md    # 처음 10줄 확인
```

## ✅ 4단계: 문제없으면 커밋

```bash
# 변경사항 확인
git status

# 문제없으면 커밋
git add README.md
git commit -m "📝 README.md 업데이트 - 개선된 가이드 적용"
```

## 🚨 5단계: 혹시 문제 생기면

```bash
# README.md 되돌리기
git checkout HEAD~1 -- README.md

# 또는 백업에서 복원
cp README_backup.md README.md
```

## 🎯 6단계: 최종 확인

```bash
# 중요한 것들이 그대로 있는지 확인
ls -la venv/          # 가상환경 확인
ls -la models/        # 모델 파일 확인
source venv/bin/activate    # 가상환경 테스트
python -c "print('정상 작동!')"   # Python 테스트
```

## 💡 안전 수칙

1. **절대 건드리면 안 되는 것들:**

   - `venv/` 폴더
   - `models/` 폴더
   - `pi_detected_images/` 폴더
   - `config.ini` (개인 설정)
   - `camera_settings.json` (개인 설정)

2. **업데이트해도 되는 것들:**

   - `README.md`
   - `requirements.txt` (주의깊게)
   - `.gitignore`

3. **업데이트 전 항상:**
   - 백업 먼저!
   - `git fetch`로 미리보기
   - 한 번에 하나씩 업데이트

---

### ✅ 템플릿 파일명 변경

- 웹 UI 템플릿 파일이 `templates/index.html` → `templates/yolo_opencv.html`로 변경됨
- Flask 라우트 및 코드에서 모두 반영됨 (render_template('yolo_opencv.html'))

### ✅ requirements.txt 통합 관리

- Windows/라즈베리파이 모두 1개 파일로 관리
- 라즈베리파이에서는 `picamera2`만 별도 설치 필요 (sudo apt-get install python3-picamera2)
- pip freeze > requirements.txt로 버전 동기화 가능

### ✅ system_info.txt 활용

- 카메라, Python, YOLO, OpenCV 등 버전 정보 기록 예시:
  - Python, torch, ultralytics, opencv-python, numpy, pillow 등 주요 버전
  - 연결된 카메라 개수/이름 등도 기록

### ✅ .gitignore 실수 방지

- 대용량/민감/개인 설정 파일은 반드시 .gitignore에 추가
- 각 항목별로 "왜 제외하는지" 주석 설명 추가 (실수 방지)

### ✅ 폴더명 변경 안내

- autocarz(복사본 등) → autocarz로 폴더명 변경해도 코드/실행에 영향 없음
- 경로가 하드코딩된 부분 없음 (import, Flask, 모델 로딩 등 모두 상대경로)

### ✅ 실전 git push 체크리스트

- push 전 반드시 백업 (README.md, requirements.txt, .gitignore 등)
- git status로 변경 파일 확인
- .gitignore/requirements.txt/README.md만 신중하게 업데이트
- system_info.txt 최신화 후 커밋 추천

---