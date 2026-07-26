#!/usr/bin/env python3
"""
对比两个 Excel/CSV 文件的指定列，找出在文件 A 中存在但在文件 B 中不存在的值。
支持通过 JSON 配置文件指定 file_a、file_b、column、output。
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("错误：需要安装 pandas。请运行：pip install pandas openpyxl")
    sys.exit(1)


def read_dataframe(path: str):
    """根据扩展名读取 Excel 或 CSV。"""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(p)
    if suffix == ".csv":
        return pd.read_csv(p)
    raise ValueError(f"不支持的文件格式: {suffix}（仅支持 .xlsx/.xls/.csv）")


def compare_excel(
    file_a: str,
    file_b: str,
    column: str = "Trae Session ID",
    output: str = None,
    verbose: bool = True,
):
    """
    对比两个 Excel/CSV 文件的指定列。

    返回：在 file_a 中存在但在 file_b 中不存在的行（DataFrame）
    """
    file_a = Path(file_a)
    file_b = Path(file_b)

    if not file_a.exists():
        print(f"错误：文件不存在: {file_a}")
        sys.exit(1)
    if not file_b.exists():
        print(f"错误：文件不存在: {file_b}")
        sys.exit(1)

    # 读取数据
    df_a = read_dataframe(file_a)
    df_b = read_dataframe(file_b)

    # 检查列是否存在
    if column not in df_a.columns:
        print(f"错误：'{file_a}' 中不存在列 '{column}'")
        print(f"可用列: {list(df_a.columns)}")
        sys.exit(1)
    if column not in df_b.columns:
        print(f"错误：'{file_b}' 中不存在列 '{column}'")
        print(f"可用列: {list(df_b.columns)}")
        sys.exit(1)

    # 获取集合（去除空值，转字符串）
    set_b = set(df_b[column].dropna().astype(str))

    # 找出在 A 中但不在 B 中的
    missing_mask = ~df_a[column].isin(set_b)
    missing_rows = df_a[missing_mask].copy()

    if verbose:
        print(f"\n{'='*50}")
        print(f"文件 A: {file_a.name}  ({len(df_a)} 行)")
        print(f"文件 B: {file_b.name}  ({len(df_b)} 行)")
        print(f"对比列: {column}")
        print(f"{'='*50}")
        print(f"仅在 '{file_a.name}' 中存在、在 '{file_b.name}' 中缺失的数量: {len(missing_rows)}")

        if len(missing_rows) > 0:
            print(f"\n--- 缺失详情 ---")
            for idx, row in missing_rows.iterrows():
                print(f"\n[第 {idx + 2} 行]")  # +2 因为 Excel 行号从1开始且包含表头
                for col in missing_rows.columns:
                    print(f"  {col}: {row[col]}")
        else:
            print("\n✓ 所有数据都在文件 B 中存在，无缺失。")

    # 导出结果
    if output and len(missing_rows) > 0:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = output_path.suffix.lower()
        if suffix == ".csv":
            missing_rows.to_csv(output_path, index=False, encoding="utf-8-sig")
        else:
            missing_rows.to_excel(output_path, index=False)
        print(f"\n结果已导出: {output}")

    return missing_rows


def load_config(config_path: str):
    """加载 JSON 配置文件。"""
    p = Path(config_path)
    if not p.exists():
        print(f"错误：配置文件不存在: {p}")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="对比两个 Excel/CSV 文件的指定列，找出仅在 A 中存在的数据。"
    )
    parser.add_argument("file_a", nargs="?", help="源文件（可能包含缺失数据的文件）")
    parser.add_argument("file_b", nargs="?", help="目标文件（基准文件）")
    parser.add_argument(
        "-c", "--column", default="Trae Session ID", help="要对比的列名 (默认: Trae Session ID)"
    )
    parser.add_argument("-o", "--output", help="将缺失结果导出到指定文件")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，只输出数量")
    parser.add_argument(
        "--config",
        default=None,
        help="JSON 配置文件路径，包含 file_a/file_b/column/output",
    )

    args = parser.parse_args()

    config = {}
    if args.config:
        config = load_config(args.config)

    # 命令行参数优先级高于配置文件
    file_a = args.file_a or config.get("file_a")
    file_b = args.file_b or config.get("file_b")
    column = args.column if args.column != "Trae Session ID" else config.get("column", "Trae Session ID")
    output = args.output or config.get("output")
    verbose = not args.quiet

    if not file_a or not file_b:
        parser.print_help()
        print("\n错误：必须提供 file_a 和 file_b，或通过 --config 指定配置文件。")
        sys.exit(1)

    compare_excel(
        file_a=file_a,
        file_b=file_b,
        column=column,
        output=output,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
