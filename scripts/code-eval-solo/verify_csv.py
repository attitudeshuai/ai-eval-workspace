import csv, os, re, glob, sys

# 从 gen_csv 导入核心提取逻辑，确保验证与导出完全一致
try:
    from gen_csv import extract_field, extract_blocks
except ImportError:
    # 若 gen_csv.py 不在同目录，将 scripts 目录加入路径
    _scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _scripts_dir)
    from gen_csv import extract_field, extract_blocks

# ===== 配置区（与 gen_csv.py 对应） =====
# 可在命令行传入参数，也可直接修改下方默认值
DEFAULT_CSV = r'd:\charles\program\ai\apps\03.output-files\csv list\csv-app-03-export.csv'
DEFAULT_BASE = r'd:\charles\program\ai\ai-eval-workspace\sessions\code-eval-solo\solo-demo\ai-model-result'
# ===========================================


def extract_repo_id(block):
    repo_id = extract_field(block, '标志：') or extract_field(block, '标志')
    if not repo_id:
        m = re.search(r'###\s*标志[：:]\s*\n\s*(\S+)', block)
        if m:
            repo_id = m.group(1)
    return repo_id


def collect_md_records(base):
    """从所有 *-评价结果.md 文件中收集 (repo_id, round_num, session_id, commit_id, file_name)"""
    records = []
    for fpath in sorted(glob.glob(os.path.join(base, '**', '*-评价结果.md'), recursive=True)):
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        blocks = extract_blocks(content)
        for i, block in enumerate(blocks):
            round_num = i + 1
            repo_id = extract_repo_id(block)
            if not repo_id:
                continue
            session_id = extract_field(block, 'Session ID')
            commit_id = extract_field(block, 'Commit ID')
            records.append((repo_id, round_num, session_id, commit_id, fname))
    return records


def collect_csv_records(csv_path):
    """从 CSV 中读取 [(repo_id, session_id, commit_id), ...]"""
    records = []
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append((
                row.get('Repo ID', ''),
                row.get('Trae Session ID', ''),
                row.get('Commit ID', '')
            ))
    return records


def sort_key(record):
    """按 Repo ID 末尾数字部分排序（与 gen_csv.py 的 rows.sort 保持一致）"""
    repo_id = record[0]
    m = re.search(r'-(\d+)$', repo_id)
    return int(m.group(1)) if m else 0


def char_diff(a, b):
    """显示两个字符串的字符级差异"""
    if len(a) != len(b):
        return f"长度不同 (md={len(a)}, csv={len(b)})"
    diffs = []
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            diffs.append(f"位置{i}: md={repr(ca)} csv={repr(cb)}")
    if diffs:
        return '; '.join(diffs[:5]) + ('...' if len(diffs) > 5 else '')
    # 内容相同但某处有不可见差异（理论上不应发生，因为 zip 已经比对了每个字符）
    return '（内容相同但某处有不可见差异）'


def verify(csv_path, base):
    print(f'CSV  : {csv_path}')
    print(f'BASE : {base}')
    print()

    md_records = collect_md_records(base)
    csv_records = collect_csv_records(csv_path)

    # 按 gen_csv.py 相同规则排序
    md_sorted = sorted(md_records, key=sort_key)

    issues = []

    # 行数差异
    if len(md_sorted) != len(csv_records):
        issues.append(f"行数不一致: markdown 提取到 {len(md_sorted)} 行, CSV 有 {len(csv_records)} 行")

    md_idx = 0
    csv_idx = 0
    while md_idx < len(md_sorted) and csv_idx < len(csv_records):
        md_repo, md_round, md_sid, md_cid, md_file = md_sorted[md_idx]
        csv_repo, csv_sid, csv_cid = csv_records[csv_idx]

        prefix = f"第 {csv_idx + 1} 行 (Repo ID: {csv_repo})"

        if md_repo != csv_repo:
            issues.append(
                f"{prefix}: Repo ID 不匹配 (md: '{md_repo}' 来自 {md_file} 第{md_round}轮)"
            )
            # 跳过不匹配的行，继续比对后续
            md_idx += 1
            csv_idx += 1
            continue

        # Session ID 比对
        if md_sid != csv_sid:
            diff = char_diff(md_sid, csv_sid)
            issues.append(
                f"{prefix}: Session ID 不一致\n"
                f"    markdown ({md_file} 第{md_round}轮): {repr(md_sid)}\n"
                f"    csv                              : {repr(csv_sid)}\n"
                f"    差异                             : {diff}"
            )

        # Commit ID 比对
        if md_cid != csv_cid:
            diff = char_diff(md_cid, csv_cid)
            issues.append(
                f"{prefix}: Commit ID 不一致\n"
                f"    markdown ({md_file} 第{md_round}轮): {repr(md_cid)}\n"
                f"    csv                              : {repr(csv_cid)}\n"
                f"    差异                             : {diff}"
            )

        md_idx += 1
        csv_idx += 1

    if issues:
        print(f"❌ 验证失败，发现 {len(issues)} 个问题：\n")
        for issue in issues:
            print(issue)
            print()
        return False
    else:
        print(f"✅ 验证通过！共 {len(csv_records)} 行，Session ID 和 Commit ID 全部原文一致。")
        return True


if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    base = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE

    if not os.path.exists(csv_path):
        print(f"错误: CSV 文件不存在: {csv_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(base):
        print(f"错误: 扫描目录不存在: {base}", file=sys.stderr)
        sys.exit(1)

    ok = verify(csv_path, base)
    sys.exit(0 if ok else 1)
