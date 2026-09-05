#!/usr/bin/env python3
"""
把终端输出/文本渲染成 PNG 截图（swe-like 取证用）。

evidence/screenshots/ 至少需 1 张验证结果截图；本脚本把验证命令的文本输出
渲染为等宽字体 PNG，避免手工截图。

用法：
    go test ./... 2>&1 | python text2png.py -o screenshots/verify-passed.png
    python text2png.py verify.log -o screenshots/verify-passed.png [--font-size 16]

依赖：pip install pillow
"""

import argparse
import sys

from PIL import Image, ImageDraw, ImageFont

# 等宽字体候选（Windows / Linux / macOS），含 CJK 回退
FONT_CANDIDATES = [
    "consola.ttf",            # Windows Consolas
    "msyh.ttc",               # Windows 微软雅黑（CJK）
    "DejaVuSansMono.ttf",     # Pillow 自带
    "Menlo.ttf",
    "monospace.ttf",
]

MAX_LINES = 400


def load_font(size):
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description="把文本渲染成 PNG 截图")
    ap.add_argument("input", nargs="?", help="输入文本文件；缺省读 stdin")
    ap.add_argument("-o", "--output", required=True, help="输出 PNG 路径")
    ap.add_argument("--font-size", type=int, default=16)
    ap.add_argument("--padding", type=int, default=16)
    args = ap.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    lines = text.splitlines()[:MAX_LINES]
    if not lines:
        print("错误：输入为空，不生成截图", file=sys.stderr)
        sys.exit(1)

    font = load_font(args.font_size)
    probe = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(probe)
    line_h = int(draw.textbbox((0, 0), "Ag", font=font)[3] * 1.4) or args.font_size + 6
    width = max(draw.textlength(line, font=font) for line in lines)
    w = int(width) + args.padding * 2
    h = line_h * len(lines) + args.padding * 2

    img = Image.new("RGB", (w, h), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    y = args.padding
    for line in lines:
        draw.text((args.padding, y), line, font=font, fill=(220, 220, 220))
        y += line_h
    img.save(args.output)
    print(f"已生成 {args.output}（{w}x{h}，{len(lines)} 行）")


if __name__ == "__main__":
    main()
