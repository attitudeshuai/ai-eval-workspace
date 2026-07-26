import os, re, glob, sys

def extract_session_id_from_review(text):
    """从评价结果文件中提取每轮的 Session ID，返回 [(round_num, session_id), ...]"""
    pattern = r'## Session ID\s*\n(.*?)(?=\n## |\n# |\Z)'
    blocks = re.split(r'(?=^# .+ 第\s*\d+\s*次对话评价结果)', text, flags=re.MULTILINE)
    results = []
    for block in blocks:
        block = block.strip()
        if not block or not re.match(r'^# .+ 第\s*\d+\s*次对话评价结果', block):
            continue
        round_match = re.search(r'第\s*(\d+)\s*次对话评价结果', block)
        round_num = int(round_match.group(1)) if round_match else 0
        m = re.search(pattern, block, re.DOTALL)
        if m:
            content = m.group(1)
            for raw_line in content.splitlines():
                line = raw_line.rstrip('\r')
                if not line:
                    continue
                if line.strip() == '【必须原文逐字复制，禁止改写】':
                    continue
                results.append((round_num, line))
                break
            else:
                results.append((round_num, ''))
        else:
            results.append((round_num, ''))
    return results

def extract_session_ids_from_source(text):
    """从原始 .md 文件中提取每轮的 Session ID，返回 [(round_num, session_id), ...]"""
    results = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # 匹配中文数字或阿拉伯数字的轮次
        m = re.match(r'模型第([一二三四五六七八九十\d]+)次回答 trae session id\s*[:：]\s*$', line.strip())
        if m:
            round_num_str = m.group(1)
            # 转换中文数字为阿拉伯数字
            cn_to_arabic = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                           '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
            if round_num_str.isdigit():
                round_num = int(round_num_str)
            else:
                round_num = cn_to_arabic.get(round_num_str, 0)
            sid = ''
            j = i + 1
            while j < len(lines):
                next_line = lines[j].rstrip('\r')
                if next_line.strip() == '':
                    j += 1
                    continue
                # 如果下一行是已知标签，说明 session id 为空
                if re.match(r'(?:修改范围|模型第|用户第|修改文件|涉及文件|##)\s*[:：]', next_line.strip()):
                    break
                sid = next_line
                break
            results.append((round_num, sid))
            i = j + 1 if j > i else i + 1
            continue
        i += 1
    return results

def main(base_dir):
    review_files = sorted(glob.glob(os.path.join(base_dir, '**', '*-评价结果.md'), recursive=True))
    issues = []
    checked = 0
    matched_pairs = 0

    for review_path in review_files:
        source_path = review_path.replace('-评价结果.md', '.md')
        if not os.path.exists(source_path):
            continue

        with open(review_path, 'r', encoding='utf-8') as f:
            review_content = f.read()
        with open(source_path, 'r', encoding='utf-8') as f:
            source_content = f.read()

        review_sids = extract_session_id_from_review(review_content)
        source_sids = extract_session_ids_from_source(source_content)

        # 建立 source 的 round -> sid 映射
        source_map = {r: sid for r, sid in source_sids}

        for round_num, review_sid in review_sids:
            checked += 1
            source_sid = source_map.get(round_num)
            if source_sid is None:
                continue
            matched_pairs += 1
            if review_sid != source_sid:
                rel_review = os.path.relpath(review_path, base_dir)
                issues.append({
                    'file': rel_review,
                    'round': round_num,
                    'source': source_sid,
                    'review': review_sid,
                    'diff_pos': None
                })
                min_len = min(len(source_sid), len(review_sid))
                for idx in range(min_len):
                    if source_sid[idx] != review_sid[idx]:
                        issues[-1]['diff_pos'] = idx
                        break
                if issues[-1]['diff_pos'] is None and len(source_sid) != len(review_sid):
                    issues[-1]['diff_pos'] = min_len

    print(f'共检查 {checked} 个 Session ID 条目，成功配对 {matched_pairs} 个')
    print(f'发现 {len(issues)} 处不一致\n')

    for issue in issues:
        print(f"文件: {issue['file']} 第{issue['round']}次")
        print(f"  原始 .md  : {issue['source']}")
        print(f"  评价结果  : {issue['review']}")
        if issue['diff_pos'] is not None:
            pos = issue['diff_pos']
            print(f"  差异位置  : 第 {pos} 位")
            print(f"  原始上下文: ...{repr(issue['source'][max(0,pos-10):pos+10])}...")
            print(f"  评价上下文: ...{repr(issue['review'][max(0,pos-10):pos+10])}...")
        print()

    return len(issues)

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else r'd:\charles\program\ai\ai-eval-workspace\sessions\code-eval-solo\solo-demo\ai-model-result'
    issues_count = main(base)
    sys.exit(1 if issues_count > 0 else 0)
