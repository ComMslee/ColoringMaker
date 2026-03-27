#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
색칠도안 변환기 v6 (Coloring Page Converter)
=============================================
Divide-by-blur 기법으로 조명/그라데이션을 정규화한 후
Bilateral Filter + Adaptive Threshold로 깨끗한 선화를 추출합니다.

사용법:
  py convert_coloring.py                        # 작업중 폴더 전체 변환
  py convert_coloring.py image1.jpg image2.png   # 특정 파일만 변환
  py convert_coloring.py --input_dir ./폴더      # 입력 폴더 지정
  py convert_coloring.py --output_dir ./결과      # 출력 폴더 지정
  py convert_coloring.py --line_thickness 2      # 선 굵기 조절 (1~5, 기본 2)

필요 라이브러리: opencv-python-headless, Pillow, numpy
"""

import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image


def load_image(path):
    """이미지를 로드합니다. WEBP/JPG/PNG 등 다양한 포맷 지원."""
    pil_img = Image.open(path).convert('RGB')
    return np.array(pil_img)


def save_image(img, path):
    """이미지를 저장합니다. 한글 경로도 지원."""
    Image.fromarray(img).save(path)


def resize_if_needed(img, max_size=2000):
    """큰 이미지는 리사이즈합니다."""
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def analyze_image(gray):
    """이미지 특성(밝기, 대비, 복잡도)을 분석합니다."""
    return {
        'brightness': float(np.mean(gray)),
        'contrast': float(np.std(gray)),
        'complexity': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
    }


def divide_by_blur(gray, blur_size=21):
    """이미지를 블러 버전으로 나눠서 조명/그라데이션을 정규화합니다."""
    blur = cv2.GaussianBlur(gray, (blur_size, blur_size), 0).astype(np.float32)
    blur[blur == 0] = 1
    divided = (gray.astype(np.float32) / blur * 255).clip(0, 255).astype(np.uint8)
    return divided


def remove_small_components(binary, min_area=50):
    """작은 연결 컴포넌트(노이즈 점)를 제거합니다."""
    inv = cv2.bitwise_not(binary)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    clean = np.zeros_like(inv)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            clean[labels == i] = 255
    return cv2.bitwise_not(clean)


def extract_lines(img_rgb, line_thickness=2):
    """
    이미지에서 선화를 추출합니다.

    Parameters:
        img_rgb: RGB 이미지 (numpy array)
        line_thickness: 1~5
    Returns:
        흑백 선화 이미지 (numpy array, uint8, 0 or 255)
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    stats = analyze_image(gray)
    B, C, X = stats['brightness'], stats['contrast'], stats['complexity']

    # Step 1: Divide-by-blur로 정규화 (조명/그라데이션 제거)
    if B < 140:
        # 어두운 이미지: 밝기 보정 후 정규화
        gamma = 1.5
        table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                          for i in range(256)]).astype(np.uint8)
        normalized = divide_by_blur(cv2.LUT(gray, table), blur_size=21)
    else:
        normalized = divide_by_blur(gray, blur_size=21)

    # Step 2: Bilateral filter
    filtered = normalized
    passes = 2 if (X > 1500 or B < 140) else 1
    for _ in range(passes):
        filtered = cv2.bilateralFilter(filtered, 5, 50, 50)

    # Step 3: Adaptive threshold
    result = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 9, 2
    )

    # Step 4: Morphology cleanup
    result = cv2.morphologyEx(result, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    # Step 5: Line thickness
    if line_thickness >= 2:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (line_thickness, line_thickness))
        result = cv2.erode(result, kernel, iterations=1)

    # Step 6: Final cleanup
    result = cv2.medianBlur(result, 3)
    _, result = cv2.threshold(result, 128, 255, cv2.THRESH_BINARY)
    mca = 80 if (X > 1500 or B < 140) else 50
    result = remove_small_components(result, min_area=mca)

    return result


def to_coloring_page(input_path, output_path, line_thickness=2):
    """이미지를 색칠도안으로 변환하여 저장합니다."""
    img = load_image(input_path)
    img = resize_if_needed(img)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    stats = analyze_image(gray)
    print("[B:{:.0f} C:{:.0f} X:{:.0f}] ".format(
        stats['brightness'], stats['contrast'], stats['complexity']), end='')

    result = extract_lines(img, line_thickness=line_thickness)
    border = 30
    result = cv2.copyMakeBorder(result, border, border, border, border,
                                cv2.BORDER_CONSTANT, value=255)
    save_image(result, output_path)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='원본 이미지를 색칠도안(선화)으로 변환합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  py convert_coloring.py                          # 작업중 폴더 전체 변환
  py convert_coloring.py image.jpg                # 특정 파일 변환
  py convert_coloring.py --line_thickness 3       # 굵은 선
  py convert_coloring.py --input_dir ./원본       # 입력 폴더 지정
  py convert_coloring.py --output_dir ./결과      # 출력 폴더 지정
        """
    )
    parser.add_argument('files', nargs='*', help='변환할 이미지 파일 (지정하지 않으면 폴더 전체)')
    parser.add_argument('--input_dir', default=None, help='입력 폴더 (기본: 스크립트 옆 작업중 폴더)')
    parser.add_argument('--output_dir', default=None, help='출력 폴더 (기본: 입력 폴더와 동일)')
    parser.add_argument('--line_thickness', type=int, default=2, choices=[1, 2, 3, 4, 5],
                        help='선 굵기 (기본: 2)')
    parser.add_argument('--suffix', default='_coloring', help='출력 파일 접미사 (기본: _coloring)')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

    if args.files:
        files_to_convert = []
        for f in args.files:
            if os.path.isfile(f):
                files_to_convert.append(os.path.abspath(f))
            else:
                print("  [!] 파일을 찾을 수 없습니다: {}".format(f))
        output_dir = args.output_dir or (os.path.dirname(files_to_convert[0]) if files_to_convert else '.')
    else:
        input_dir = args.input_dir or os.path.join(base_dir, u'\uc791\uc5c5\uc911')
        if not os.path.isdir(input_dir):
            print("입력 폴더가 없습니다: {}".format(input_dir))
            print("--input_dir 옵션으로 폴더를 지정하거나, 변환할 파일을 직접 지정하세요.")
            sys.exit(1)

        files_to_convert = []
        for f in sorted(os.listdir(input_dir)):
            _, ext = os.path.splitext(f)
            if ext.lower() in supported_ext and args.suffix not in f:
                files_to_convert.append(os.path.join(input_dir, f))
        output_dir = args.output_dir or input_dir

    if not files_to_convert:
        print("변환할 이미지가 없습니다.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("=== 색칠도안 변환기 ===")
    print("  이미지: {}개 | 선 굵기: {} | 출력: {}".format(
        len(files_to_convert), args.line_thickness, output_dir))
    print()

    success = 0
    fail = 0
    for filepath in files_to_convert:
        filename = os.path.basename(filepath)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, "{}{}.png".format(name, args.suffix))

        print("  {} ".format(filename), end='', flush=True)
        try:
            to_coloring_page(filepath, output_path, line_thickness=args.line_thickness)
            print("-> 완료!")
            success += 1
        except Exception as e:
            print("-> 실패! ({})".format(e))
            fail += 1

    print()
    print("=== {}개 성공 / {}개 실패 ===".format(success, fail))


if __name__ == '__main__':
    main()
