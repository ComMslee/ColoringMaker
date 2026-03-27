# ColoringMaker (색칠도안 메이커)

이미지를 색칠도안(선화)으로 변환하여 A4 크기 PDF로 생성하는 프로그램입니다.

## 기능

- 폴더 내 이미지 일괄 변환 (JPG, PNG, WEBP, BMP, TIFF)
- 선 굵기 조절 (1~5단계)
- A4 크기 자동 맞춤 (300DPI, 비율 유지)
- 다중 페이지 PDF 생성

## 사용법

1. [Releases](https://github.com/ComMslee/ColoringMaker/releases)에서 최신 `ColoringMaker.exe` 다운로드
2. 실행 후 원본 이미지 폴더 선택
3. 선 굵기 설정
4. **시작** 클릭 → PDF 자동 생성

## 빌드

### 로컬 빌드
```
scripts\build.bat
```
Python, PyInstaller, opencv-python-headless, numpy, Pillow 필요

### 릴리즈 (GitHub Actions 자동 빌드)
```
scripts\release.bat
```
버전 입력 → 커밋 → 태그 → 푸시 → Actions가 exe 빌드 + Release 생성

## 프로젝트 구조

```
├── src/
│   ├── coloring_maker.py   # 메인 GUI 프로그램
│   ├── convert_coloring.py # CLI 변환 스크립트
│   └── res/
│       └── icon.ico        # 앱 아이콘
├── scripts/
│   ├── build.bat           # 로컬 빌드 스크립트
│   └── release.bat         # 릴리즈 스크립트
├── VERSION                 # 버전 파일
├── requirements.txt        # 의존성
└── .github/workflows/
    └── release.yml         # GitHub Actions 빌드+릴리즈
```

## 기술 스택

- Python, tkinter (GUI)
- OpenCV (이미지 처리)
- Pillow (A4 맞춤, PDF 생성)
- PyInstaller (exe 패키징)
