---
name: test-convert
description: "ColoringMaker 이미지 변환 테스트. 원본 이미지 폴더에서 이미지를 찾아 색칠도안 변환을 실행하고 결과를 확인한다. 사용자가 '테스트', 'test', '변환 테스트', '변환 확인', '색칠도안 테스트', '결과 확인' 등을 언급할 때 이 스킬을 사용한다."
---

# Test Convert - 색칠도안 변환 테스트

이 스킬은 원본 이미지를 색칠도안으로 변환하는 테스트를 수행한다.

## 테스트 절차

### 1. 테스트 이미지 찾기

다음 폴더 순서로 이미지를 찾는다:
1. `원본/`
2. `원본이미지/`
3. 사용자가 지정한 폴더

지원 확장자: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif`

찾은 이미지 목록과 개수를 보고한다.

### 2. 출력 폴더 준비

```bash
mkdir -p test_output
```

### 3. 변환 실행

Python 스크립트를 작성하여 실행한다. `src/coloring_maker.py`의 함수들을 직접 임포트해서 사용한다:

```python
import sys, os
sys.path.insert(0, '.')
from src.coloring_maker import _ensure_libs, find_images, process_one

_ensure_libs()
from src.coloring_maker import Image

input_dir = '원본'  # or '원본이미지'
images = find_images(input_dir)

success = 0
failed = 0
for img_path in images:
    name = os.path.splitext(os.path.basename(img_path))[0]
    try:
        page = process_one(img_path, line_thickness=2)
        page.save(f'test_output/{name}_coloring.png')
        success += 1
    except Exception as e:
        print(f'FAILED: {name} - {e}')
        failed += 1

print(f'Done: {success} success, {failed} failed, {success+failed} total')
```

타임아웃은 5분(300000ms)으로 설정한다 (이미지가 많을 수 있음).

### 4. 결과 보고

- 성공/실패 개수
- 실패한 파일명과 에러 메시지
- `test_output/` 폴더에 결과 파일이 생성되었음을 알린다
- 선택적으로 PDF로도 묶을 수 있음을 안내한다

## 주의사항

- `test_output/` 폴더는 `.gitignore`에 없으므로, 테스트 후 정리가 필요할 수 있다.
- Python 3.6 환경에서는 f-string 대신 `.format()` 사용을 권장한다.
- 이미지가 많으면 시간이 오래 걸릴 수 있으므로 진행 상황을 표시한다.
