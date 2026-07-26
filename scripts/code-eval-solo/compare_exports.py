#!/usr/bin/env python3
"""
Solo 导出对比工具：对比提示词导出 CSV 与评价结果导出 CSV。
以提示词文件中的 Session ID 为准，找出所有不匹配项。

用法：
  python compare_exports.py <prompt_csv> <eval_csv>
"""

import csv
import sys
from pathlib import Path


def read_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def compare(prompt_csv, eval_csv):
    prompt_rows = read_csv(prompt_csv)
    eval_rows = read_csv(eval_csv)

    # 以 Session ID 为 key 建立索引
    prompt_by_sid = {r['Trae Session ID']: r for r in prompt_rows}
    eval_by_sid = {r['Trae Session ID']: r for r in eval_rows}

    prompt_sids = set(prompt_by_sid.keys())
    eval_sids = set(eval_by_sid.keys())

    common = prompt_sids & eval_sids
    only_prompt = prompt_sids - eval_sids
    only_eval = eval_sids - prompt_sids

    mismatches = []

    for sid in sorted(common):
        pr = prompt_by_sid[sid]
        er = eval_by_sid[sid]

        diffs = []
        # 对比 Repo ID
        if pr.get('Repo ID', '') != er.get('Repo ID', ''):
            diffs.append(('Repo ID', pr.get('Repo ID', ''), er.get('Repo ID', '')))
        # 对比 User Prompt
        pp = ' '.join(pr.get('User Prompt', '').split())
        ep = ' '.join(er.get('User Prompt', '').split())
        if pp != ep:
            diffs.append(('User Prompt', pp[:80], ep[:80]))

        if diffs:
            mismatches.append((sid, diffs))

    # ── 输出 ──
    p_count = len(prompt_rows)
    e_count = len(eval_rows)

    print(f"\n{'='*60}")
    print(f"提示词导出 (权威): {Path(prompt_csv).name}  ({p_count} 行)")
    print(f"评价结果导出        : {Path(eval_csv).name}  ({e_count} 行)")
    print(f"{'='*60}")

    # 行数对比
    if p_count != e_count:
        diff = p_count - e_count
        direction = "多" if diff > 0 else "少"
        print(f"\n🔴 数据量不一致: 提示词导出比评价结果 {direction} {abs(diff)} 行")
    else:
        print(f"\n✅ 数据量一致: 各 {p_count} 行")

    # 匹配行数
    print(f"   匹配的 Session ID: {len(common)} 个")

    # 唯一行
    if only_prompt:
        print(f"\n🔴 仅在提示词导出中存在（评价结果缺失）: {len(only_prompt)} 条")
        for sid in sorted(only_prompt):
            r = prompt_by_sid[sid]
            print(f"   Session ID: {sid}")
            print(f"   Repo ID   : {r.get('Repo ID', '')}")
            print()

    if only_eval:
        print(f"\n🟡 仅在评价结果中存在（提示词未导出）: {len(only_eval)} 条")
        for sid in sorted(only_eval):
            r = eval_by_sid[sid]
            print(f"   Session ID: {sid}")
            print(f"   Repo ID   : {r.get('Repo ID', '')}")
            print()

    # 不匹配
    if mismatches:
        print(f"\n🔴 字段不匹配: {len(mismatches)} 条")
        print(f"   （以提示词导出值为准，→ 右侧为评价结果中的错误值）\n")
        for sid, diffs in mismatches:
            print(f"   Session ID: {sid}")
            for field, prompt_val, eval_val in diffs:
                print(f"     {field}:")
                print(f"       正确 (提示词): {prompt_val}")
                print(f"       错误 (评价)  : {eval_val}")
            print()

    # 总结
    total_issues = len(only_prompt) + len(only_eval) + len(mismatches)
    if total_issues == 0:
        print("\n✅ 完全一致，无任何差异。")
    else:
        print(f"{'='*60}")
        print(f"总结: 仅提示词 {len(only_prompt)} | 仅评价 {len(only_eval)} | 不匹配 {len(mismatches)} | 共 {total_issues} 处差异")
        print(f"规则: Session ID 以提示词文件为准。不匹配字段中，提示词导出值 = 正确值。")

    return total_issues


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python compare_exports.py <prompt_csv> <eval_csv>")
        sys.exit(1)
    issues = compare(sys.argv[1], sys.argv[2])
    sys.exit(0 if issues == 0 else 1)
