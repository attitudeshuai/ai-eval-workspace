"""
查看指定 session/date 下所有批次的标注状态。

用法:
    python batch_status.py <session_date_dir>
    python batch_status.py sessions/pairwise-gsb/0724/2026-07-27
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _config import (
    get_batch_prefix,
    get_batch_output_dir,
    find_batch_output_file,
    find_batch_input_file,
    get_batch_error_file,
)


def get_batch_status(batch_dir):
    """返回批次状态：pending / annotated / validated / delivered"""
    output_file = find_batch_output_file(batch_dir)
    errors_file = batch_dir / get_batch_error_file()
    summary_file = batch_dir / "validation-summary.json"

    if not output_file:
        return "pending", "未标注"

    # 优先读 validation-summary.json（校验通过后由校验脚本写入）
    if summary_file.exists():
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
            if summary.get("passed"):
                return "validated", "已校验通过"
            else:
                return "annotated", f"已标注但校验未通过（错误行数 {summary.get('error_rows', '?')}）"
        except Exception:
            pass

    # 兜底：看 errors.txt
    if errors_file.exists():
        return "annotated", "已标注但未通过校验"
    return "annotated", "已标注待校验"


def count_rows(xlsx_path):
    """统计 Excel 数据行数"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(xlsx_path)
        count = max(0, wb.active.max_row - 1)
        wb.close()
        return count
    except Exception:
        return 0


def main():
    if len(sys.argv) != 2:
        print("用法: python batch_status.py <session_date_dir>")
        print("示例: python batch_status.py sessions/pairwise-gsb/0724/2026-07-27")
        sys.exit(1)

    session_dir = Path(sys.argv[1])
    if not session_dir.exists():
        print(f"❌ 目录不存在: {session_dir}")
        sys.exit(1)

    batch_dirs = sorted(
        [d for d in session_dir.iterdir() if d.is_dir() and d.name.startswith(get_batch_prefix())]
    )

    if not batch_dirs:
        print(f"❌ 在 {session_dir} 中未找到任何批次")
        sys.exit(1)

    print(f"📂 Session 目录: {session_dir}")
    print(f"{'='*70}")
    print(f"{'批次':<12} {'状态':<12} {'说明':<24} {'行数':>6}")
    print(f"{'-'*70}")

    status_counts = {}
    total_rows = 0
    for batch_dir in batch_dirs:
        status, desc = get_batch_status(batch_dir)
        input_file = find_batch_input_file(batch_dir)
        rows = count_rows(input_file) if input_file else 0
        total_rows += rows
        status_counts[status] = status_counts.get(status, 0) + 1

        status_emoji = {
            "pending": "⏳",
            "annotated": "📝",
            "validated": "✅",
            "delivered": "🚚",
        }.get(status, "❓")
        print(f"{batch_dir.name:<12} {status_emoji} {status:<10} {desc:<24} {rows:>6}")

    print(f"{'='*70}")
    print(f"总计: {len(batch_dirs)} 个批次, {total_rows} 条数据")
    print(f"状态分布: ", end="")
    parts = []
    for s, c in sorted(status_counts.items()):
        parts.append(f"{s}={c}")
    print(", ".join(parts))

    # 提示下一步
    pending = status_counts.get("pending", 0)
    annotated = status_counts.get("annotated", 0)
    if pending > 0:
        print(f"\n⏳ 还有 {pending} 个批次待标注")
    elif annotated > 0:
        print(f"\n📝 还有 {annotated} 个批次待校验")
    else:
        print(f"\n✅ 所有批次已完成，可执行 merge_batches.py 交付")


if __name__ == "__main__":
    main()
