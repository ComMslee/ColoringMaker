#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
색칠도안 메이커 (Coloring Page Maker) - GUI
============================================
원본 이미지 폴더 -> 색칠도안 변환 -> A4 크기 맞춤 -> PDF 생성
"""

import os
import sys
import threading
import cv2
import numpy as np
from PIL import Image
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ============================================================
# [1] 색칠도안 변환 엔진 (업그레이드 가능 영역)
# ============================================================

def _divide_by_blur(gray, blur_size=21):
    blur = cv2.GaussianBlur(gray, (blur_size, blur_size), 0).astype(np.float32)
    blur[blur == 0] = 1
    return (gray.astype(np.float32) / blur * 255).clip(0, 255).astype(np.uint8)


def _remove_small(binary, min_area=50):
    inv = cv2.bitwise_not(binary)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    clean = np.zeros_like(inv)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            clean[labels == i] = 255
    return cv2.bitwise_not(clean)


def convert_to_lineart(img_rgb, line_thickness=2):
    """
    [업그레이드 가능] 이미지를 선화로 변환합니다.
    입력: RGB numpy array / 출력: 흑백 numpy array (uint8)
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    B = float(np.mean(gray))
    X = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if B < 140:
        gamma = 1.5
        table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                          for i in range(256)]).astype(np.uint8)
        normalized = _divide_by_blur(cv2.LUT(gray, table), 21)
    else:
        normalized = _divide_by_blur(gray, 21)

    filtered = normalized
    for _ in range(2 if (X > 1500 or B < 140) else 1):
        filtered = cv2.bilateralFilter(filtered, 5, 50, 50)

    result = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 9, 2
    )

    result = cv2.morphologyEx(result, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    if line_thickness >= 2:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (line_thickness, line_thickness))
        result = cv2.erode(result, kernel, iterations=1)

    result = cv2.medianBlur(result, 3)
    _, result = cv2.threshold(result, 128, 255, cv2.THRESH_BINARY)
    result = _remove_small(result, min_area=80 if (X > 1500 or B < 140) else 50)

    return result


# ============================================================
# [2] A4 맞춤
# ============================================================

A4_W, A4_H, A4_DPI, A4_MARGIN = 2480, 3508, 300, 60


def fit_to_a4(lineart):
    img = Image.fromarray(lineart).convert('L')
    ow, oh = img.size
    uw, uh = A4_W - A4_MARGIN * 2, A4_H - A4_MARGIN * 2

    if ow / oh > uw / uh:
        nw, nh = uw, int(uw / (ow / oh))
    else:
        nh, nw = uh, int(uh * (ow / oh))

    resized = img.resize((nw, nh), Image.LANCZOS)
    resized = resized.point(lambda x: 255 if x > 128 else 0, 'L')

    canvas = Image.new('L', (A4_W, A4_H), 255)
    canvas.paste(resized, ((A4_W - nw) // 2, (A4_H - nh) // 2))
    return canvas


# ============================================================
# [3] PDF 생성
# ============================================================

def create_pdf(pages, output_path):
    rgb_pages = [p.convert('RGB') for p in pages]
    first = rgb_pages[0]
    rest = rgb_pages[1:] if len(rgb_pages) > 1 else []
    first.save(output_path, 'PDF', resolution=A4_DPI, save_all=True, append_images=rest)
    return True


# ============================================================
# [4] 이미지 처리
# ============================================================

SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}


def find_images(folder):
    files = []
    for f in sorted(os.listdir(folder)):
        _, ext = os.path.splitext(f)
        if ext.lower() in SUPPORTED_EXT:
            files.append(os.path.join(folder, f))
    return files


def process_one(img_path, line_thickness=2):
    pil_img = Image.open(img_path).convert('RGB')
    img_rgb = np.array(pil_img)
    h, w = img_rgb.shape[:2]
    if max(h, w) > 2000:
        s = 2000.0 / max(h, w)
        img_rgb = cv2.resize(img_rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    lineart = convert_to_lineart(img_rgb, line_thickness=line_thickness)
    return fit_to_a4(lineart)


# ============================================================
# GUI
# ============================================================

class ColoringMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("색칠도안 메이커")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')

        # 윈도우 크기 & 중앙 배치
        win_w, win_h = 500, 400
        sx = (self.root.winfo_screenwidth() - win_w) // 2
        sy = (self.root.winfo_screenheight() - win_h) // 2
        self.root.geometry("{}x{}+{}+{}".format(win_w, win_h, sx, sy))

        self.input_dir = tk.StringVar()
        self.output_path = tk.StringVar()
        self.line_thickness = tk.IntVar(value=2)
        self.processing = False

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.configure('Title.TLabel', font=('맑은 고딕', 16, 'bold'), background='#f0f0f0')
        style.configure('Info.TLabel', font=('맑은 고딕', 9), background='#f0f0f0')

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill='both', expand=True)

        # 제목
        ttk.Label(main, text="색칠도안 메이커", style='Title.TLabel').pack(pady=(0, 15))

        # ── 입력 폴더 ──
        f1 = ttk.LabelFrame(main, text=" 1. 원본 이미지 폴더 ", padding=10)
        f1.pack(fill='x', pady=(0, 10))

        row1 = ttk.Frame(f1)
        row1.pack(fill='x')
        self.input_entry = ttk.Entry(row1, textvariable=self.input_dir, width=45)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(row1, text="찾아보기", command=self._browse_input).pack(side='right')

        self.file_count_label = ttk.Label(f1, text="", style='Info.TLabel')
        self.file_count_label.pack(anchor='w', pady=(5, 0))

        # ── 설정 ──
        f2 = ttk.LabelFrame(main, text=" 2. 설정 ", padding=10)
        f2.pack(fill='x', pady=(0, 10))

        row2 = ttk.Frame(f2)
        row2.pack(fill='x')
        ttk.Label(row2, text="선 굵기:").pack(side='left')
        for i in range(1, 6):
            ttk.Radiobutton(row2, text=str(i), variable=self.line_thickness, value=i).pack(side='left', padx=3)

        # ── 출력 경로 ──
        f3 = ttk.LabelFrame(main, text=" 3. 출력 PDF ", padding=10)
        f3.pack(fill='x', pady=(0, 15))

        row3 = ttk.Frame(f3)
        row3.pack(fill='x')
        self.output_entry = ttk.Entry(row3, textvariable=self.output_path, width=45)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(row3, text="변경", command=self._browse_output).pack(side='right')

        # ── 진행바 & 시작 버튼 ──
        self.progress = ttk.Progressbar(main, mode='determinate', length=460)
        self.progress.pack(fill='x', pady=(0, 5))

        self.status_label = ttk.Label(main, text="폴더를 선택하면 시작할 수 있습니다.", style='Info.TLabel')
        self.status_label.pack(anchor='w')

        self.start_btn = tk.Button(main, text="▶  시작", font=('맑은 고딕', 14, 'bold'),
                                   bg='#6C5CE7', fg='white', activebackground='#5A4BD1',
                                   activeforeground='white', relief='flat', cursor='hand2',
                                   command=self._start)
        self.start_btn.pack(fill='x', pady=(10, 0), ipady=12)

    def _get_app_dir(self):
        """exe 또는 스크립트가 있는 폴더를 반환합니다."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _browse_input(self):
        folder = filedialog.askdirectory(title="원본 이미지 폴더 선택",
                                         initialdir=self._get_app_dir())
        if folder:
            self.input_dir.set(folder)
            images = find_images(folder)
            self.file_count_label.config(
                text="{}개의 이미지를 찾았습니다.".format(len(images)) if images
                else "이미지가 없습니다!"
            )
            # 자동으로 출력 경로 설정
            folder_name = os.path.basename(os.path.normpath(folder))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            parent = os.path.dirname(os.path.abspath(folder))
            self.output_path.set(
                os.path.join(parent, "coloring_{}_{}.pdf".format(folder_name, timestamp))
            )

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="PDF 저장 위치",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=os.path.basename(self.output_path.get()) if self.output_path.get() else "coloring.pdf"
        )
        if path:
            self.output_path.set(path)

    def _start(self):
        if self.processing:
            return

        input_dir = self.input_dir.get().strip()
        output_path = self.output_path.get().strip()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showwarning("경고", "올바른 폴더를 선택해주세요.")
            return
        if not output_path:
            messagebox.showwarning("경고", "출력 PDF 경로를 지정해주세요.")
            return

        images = find_images(input_dir)
        if not images:
            messagebox.showwarning("경고", "선택한 폴더에 이미지가 없습니다.")
            return

        self.processing = True
        self.start_btn.config(state='disabled', bg='#aaaaaa')
        self.progress['value'] = 0
        self.progress['maximum'] = len(images)

        thread = threading.Thread(
            target=self._run_conversion,
            args=(images, output_path, self.line_thickness.get()),
            daemon=True
        )
        thread.start()

    def _run_conversion(self, images, output_path, line_thickness):
        pages = []
        total = len(images)

        for i, img_path in enumerate(images):
            filename = os.path.basename(img_path)
            self._update_status("변환 중: {} ({}/{})".format(filename, i + 1, total))
            try:
                page = process_one(img_path, line_thickness=line_thickness)
                pages.append(page)
            except Exception as e:
                self._update_status("실패: {} ({})".format(filename, e))
            self._update_progress(i + 1)

        if pages:
            self._update_status("PDF 생성 중...")
            try:
                create_pdf(pages, output_path)
                self._update_status("완료! {} ({} 페이지)".format(
                    os.path.basename(output_path), len(pages)))
                self.root.after(0, lambda: messagebox.showinfo(
                    "완료",
                    "색칠도안 PDF가 생성되었습니다!\n\n"
                    "저장 위치:\n{}\n\n"
                    "총 {} 페이지".format(output_path, len(pages))
                ))
            except Exception as e:
                self._update_status("PDF 생성 실패: {}".format(e))
                self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
        else:
            self._update_status("변환된 이미지가 없습니다.")

        self.processing = False
        self.root.after(0, lambda: self.start_btn.config(state='normal', bg='#6C5CE7'))

    def _update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _update_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))


# ============================================================
# 메인
# ============================================================

def main():
    root = tk.Tk()
    app = ColoringMakerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
