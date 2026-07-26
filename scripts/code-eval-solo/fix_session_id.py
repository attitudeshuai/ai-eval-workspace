import os, re, glob, sys

def extract_session_ids_from_source(text):
    """从原始 .md 文件中提取每轮的 Session ID，返回 [(round_num, session_id), ...]"""
    results = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'模型第([一二三四五六七八九十\d]+)次回答 trae session id\s*[:：]\s*$', line.strip())
        if m:
            round_num_str = m.group(1)
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
                if re.match(r'(?:修改范围|模型第|用户第|修改文件|涉及文件|##)\s*[:：]', next_line.strip()):
                    break
                sid = next_line
                break
            results.append((round_num, sid))
            i = j + 1 if j > i else i + 1
            continue
        i += 1
    return results

def fix_review_file(review_path, source_path):
    """修正评价结果文件中的 Session ID"""
    with open(source_path, 'r', encoding='utf-8') as f:
        source_content = f.read()
    with open(review_path, 'r', encoding='utf-8') as f:
        review_content = f.read()

    source_sids = {r: sid for r, sid in extract_session_ids_from_source(source_content)}
    original_review = review_content

    # 按评价结果块分割
    parts = re.split(r'(?=^# .+ 第\s*\d+\s*次对话评价结果)', review_content, flags=re.MULTILINE)
    new_parts = []

    for part in parts:
        block = part
        if not re.match(r'^# .+ 第\s*\d+\s*次对话评价结果', block.strip()):
            new_parts.append(block)
            continue

        # 提取轮次
        round_match = re.search(r'第\s*(\d+)\s*次对话评价结果', block)
        if not round_match:
            new_parts.append(block)
            continue
        round_num = int(round_match.group(1))
        correct_sid = source_sids.get(round_num)
        if correct_sid is None:
            new_parts.append(block)
            continue

        # 找到并替换 Session ID 块
        sid_pattern = r'(## Session ID\s*\n)(.*?)(?=\n## |\n# |\Z)'
        sid_match = re.search(sid_pattern, block, re.DOTALL)
        if not sid_match:
            new_parts.append(block)
            continue

        # 提取当前实际 Session ID
        current_block = sid_match.group(2)
        current_sid = ''
        for raw_line in current_block.splitlines():
            line = raw_line.rstrip('\r')
            if not line:
                continue
            if line.strip() == '【必须原文逐字复制，禁止改写】':
                continue
            current_sid = line
            break

        if current_sid == correct_sid:
            new_parts.append(block)
            continue

        # 构建新的 Session ID 块
        new_sid_block = '【必须原文逐字复制，禁止改写】\n' + correct_sid
        start = sid_match.start(1) + len(sid_match.group(1))
        end = sid_match.end()
        new_block = block[:start] + new_sid_block + block[end:]
        new_parts.append(new_block)

    new_content = ''.join(new_parts)

    if new_content != original_review:
        with open(review_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main(base_dir):
    review_files = sorted(glob.glob(os.path.join(base_dir, '**', '*-评价结果.md'), recursive=True))
    fixed_count = 0
    checked_count = 0

    for review_path in review_files:
        source_path = review_path.replace('-评价结果.md', '.md')
        if not os.path.exists(source_path):
            continue
        checked_count += 1
        if fix_review_file(review_path, source_path):
            fixed_count += 1
            print(f'已修正: {os.path.relpath(review_path, base_dir)}')

    print(f'\n共检查 {checked_count} 个评价结果文件，修正 {fixed_count} 个')
    return fixed_count

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else r'd:\charles\program\ai\ai-eval-workspace\sessions\code-eval-solo\solo-demo\ai-model-result'
    main(base)
