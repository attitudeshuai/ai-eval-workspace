"""
一键初始化 GSB 标注 session。

完成动作：
1. 创建 sessions/pairwise-gsb/<session>/<date>/ 目录
2. 备份原始 Excel 为 original.xlsx
3. 切分批次
4. 生成 metadata
5. 提取所有批次图片

用法:
    python init_session.py <session> <date> <original.xlsx>
    python init_session.py 0724 2026-07-27 /path/to/data.xlsx
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _config import (
    session_date_dir,
    get_original_file,
    get_batch_prefix,
    get_batch_num_width,
    get_batch_size,
    get_batch_input_dir,
    find_batch_input_file,
    get_batch_images_dir,
)


def run_cmd(cmd, description):
    print(f"\n▶ {description}")
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 失败:\n{result.stderr}")
        sys.exit(1)
    if result.stdout:
        print(result.stdout)
    return result


def main():
    if len(sys.argv) != 4:
        print("用法: python init_session.py <session> <date> <original.xlsx>")
        print("示例: python init_session.py 0724 2026-07-27 /path/to/data.xlsx")
        sys.exit(1)

    session = sys.argv[1]
    date = sys.argv[2]
    src_excel = sys.argv[3]

    if not os.path.exists(src_excel):
        print(f"❌ 源 Excel 不存在: {src_excel}")
        sys.exit(1)

    session_dir = session_date_dir(session, date)
    original_path = session_dir / get_original_file()

    print(f"🚀 初始化 session: {session} / {date}")
    print(f"   源文件: {src_excel}")
    print(f"   目标目录: {session_dir}")

    # 1. 创建目录并备份
    session_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_excel, original_path)
    print(f"✅ 已备份原始 Excel → {original_path}")

    # 2. 切分批次
    split_script = Path(__file__).parent / "split_batches.py"
    run_cmd(
        [sys.executable, str(split_script), str(original_path), str(session_dir)],
        "切分 Excel 为批次",
    )

    # 3. 提取所有批次图片
    # 注意：切分后的 items.xlsx 不含嵌入图片（openpyxl 复制单元格时丢失），
    # 因此必须从 original.xlsx 按批次行范围提取，并重映射为批次内行号。
    extract_script = Path(__file__).parent / "extract_images.py"
    batch_dirs = sorted(
        [d for d in session_dir.iterdir() if d.is_dir() and d.name.startswith(get_batch_prefix())]
    )

    try:
        import openpyxl
    except ImportError:
        print("需要 openpyxl: pip install openpyxl")
        sys.exit(1)

    batch_size = get_batch_size()
    num_width = get_batch_num_width()
    for batch_dir in batch_dirs:
        input_xlsx = find_batch_input_file(batch_dir)
        images_dir = batch_dir / get_batch_images_dir()
        if not input_xlsx:
            continue

        # 从批次名解析序号，计算该批在原始 Excel 中的行范围
        batch_idx = int(batch_dir.name[len(get_batch_prefix()):]) - 1
        wb = openpyxl.load_workbook(input_xlsx)
        count = max(0, wb.active.max_row - 1)
        wb.close()
        start_row = 2 + batch_idx * batch_size
        end_row = start_row + count - 1
        row_offset = start_row - 2

        run_cmd(
            [
                sys.executable, str(extract_script),
                str(original_path), str(images_dir),
                "--min-row", str(start_row),
                "--max-row", str(end_row),
                "--row-offset", str(row_offset),
            ],
            f"提取 {batch_dir.name} 图片（原始行 {start_row}~{end_row}）",
        )

    print(f"\n{'='*60}")
    print(f"✅ Session 初始化完成: {session_dir}")
    print(f"\n批次列表:")
    for batch_dir in batch_dirs:
        print(f"  - {batch_dir.name}")
    print(f"\n下一步：按 skills/annotate-batch/SKILL.md 逐批标注")


if __name__ == "__main__":
    main()
