---
name: build
description: "ColoringMaker 로컬 exe 빌드. PyInstaller로 src/coloring_maker.py를 단일 exe로 빌드하고, 실행 확인까지 수행한다. 사용자가 '빌드', 'build', 'exe 만들어', '실행파일', '패키징' 등을 언급할 때 이 스킬을 사용한다."
---

# Build - ColoringMaker 로컬 빌드

이 스킬은 PyInstaller로 ColoringMaker.exe를 빌드하고 실행 확인까지 수행한다.

## 빌드 절차

### 1. 아이콘 준비

한글 경로에서 PyInstaller 아이콘 로딩이 실패할 수 있으므로, 아이콘을 ASCII 경로로 복사한다:

```bash
cp src/res/icon.ico /tmp/coloring_icon.ico
```

### 2. PyInstaller 빌드

```bash
py -m PyInstaller --onefile --windowed \
  --name "ColoringMaker" \
  --icon "/tmp/coloring_icon.ico" \
  "src/coloring_maker.py" \
  --distpath "build" \
  --workpath "build/temp" \
  --specpath "build/temp" \
  -y
```

빌드 타임아웃은 5분(300000ms)으로 설정한다.

### 3. 정리

```bash
rm -rf build/temp
rm -f /tmp/coloring_icon.ico
```

### 4. 릴리즈 복사

```bash
cp build/ColoringMaker.exe ColoringMaker.exe
```

### 5. 실행 확인

exe를 백그라운드로 실행하고 3초 후 tasklist로 프로세스가 떠 있는지 확인한다:

```bash
./ColoringMaker.exe &
sleep 3
tasklist | grep -i ColoringMaker
```

프로세스가 확인되면 성공. 확인 후 프로세스를 종료한다:

```bash
taskkill //f //im ColoringMaker.exe
```

### 6. 결과 보고

- 빌드 성공/실패 여부
- exe 파일 크기
- 실행 확인 결과

## 주의사항

- Python 3.6 환경이므로 PyInstaller 4.x를 사용한다.
- `opencv-python-headless`, `numpy`, `Pillow`이 설치되어 있어야 한다.
- 빌드 실패 시 에러 로그를 사용자에게 보여주고 원인을 분석한다.
