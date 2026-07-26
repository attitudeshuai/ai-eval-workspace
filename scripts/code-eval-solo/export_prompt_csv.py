import csv, os, re, glob

# ===== 配置区：修改这两个路径即可 =====
BASE = r'd:\charles\program\ai\ai-eval-workspace\sessions\code-eval-solo\solo-demo\ai-model-result'
OUTPUT = r'd:\charles\program\ai\ai-eval-workspace\deliverables\code-eval-solo\solo-demo\csv-prompt-export.csv'
PROJECT_NAME = ''   # 留空时自动从 BASE 最后一级目录名推断，如 app-01
# =======================================

HEADERS = ['Repo ID', 'Trae Session ID', 'User Prompt']

def extract_rounds_from_prompt_file(file_path):
    """
    从单个提示词文件中提取所有带有 trae session id 的轮次。
    返回列表，每项为 (round_num, session_id, prompt_text)。
    """
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    prompt_lines = {}
    session_lines = {}
    answer_lines = {}

    # 同时支持阿拉伯数字和中文数字
    cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
               '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

    def parse_round(m):
        val = m.group(1)
        if val in cn_nums:
            return cn_nums[val]
        return int(val)

    for i, line in enumerate(lines):
        m = re.match(r'^用户第?(\d+|一|二|三|四|五|六|七|八|九|十)次提示词', line)
        if m:
            prompt_lines[parse_round(m)] = i
        m = re.match(r'^模型第?(\d+|一|二|三|四|五|六|七|八|九|十)次回答 trae session id', line)
        if m:
            session_lines[parse_round(m)] = i
        m = re.match(r'^模型第?(\d+|一|二|三|四|五|六|七|八|九|十)次回答内容', line)
        if m:
            answer_lines[parse_round(m)] = i

    all_marks = sorted(set(
        list(prompt_lines.values()) + list(session_lines.values()) + list(answer_lines.values())
    ))

    def get_block_text(start_line):
        next_marks = [x for x in all_marks if x > start_line]
        end = next_marks[0] if next_marks else len(lines)
        return ''.join(lines[start_line + 1:end]).strip()

    results = []
    for n in sorted(session_lines.keys()):
        # 提取 trae session id（同一行或下一行）
        line_idx = session_lines[n]
        sid_inline = re.sub(
            r'^模型第?(?:\d+|一|二|三|四|五|六|七|八|九|十)次回答 trae session id[：:]?\s*',
            '',
            lines[line_idx]
        ).strip()
        if sid_inline:
            session_id = sid_inline
        else:
            block_text = get_block_text(line_idx)
            session_id = ''
            for line in block_text.splitlines():
                stripped = line.strip()
                if stripped:
                    session_id = stripped
                    break

        # 只导出存在 trae session id 的轮次。
        # 通过是否包含 20 位以上连续十六进制字符来区分真正的 session id 与
        # 像 "修改范围:" 这样的误提取内容。
        if not session_id or not re.search(r'[0-9a-fA-F]{20,}', session_id):
            continue

        prompt_text = ''
        if n in prompt_lines:
            line_idx = prompt_lines[n]
            # 先尝试行内提取
            prompt_inline = re.sub(
                r'^用户第?(?:\d+|一|二|三|四|五|六|七|八|九|十)次提示词[：:]?\s*',
                '',
                lines[line_idx]
            ).strip()
            if prompt_inline:
                prompt_text = prompt_inline
            else:
                prompt_text = get_block_text(line_idx)

        results.append((n, session_id, prompt_text))

    return results

def get_repo_id_from_file(fpath):
    """从文件第一行或文件名提取 Repo ID 基础名。"""
    # 优先读取第一行
    try:
        with open(fpath, encoding='utf-8') as f:
            first_line = f.readline().strip()
        if first_line:
            return first_line
    except Exception:
        pass
    # 回退到文件名（去掉 .md）
    return os.path.splitext(os.path.basename(fpath))[0]


def process_project(project_base, project_name, rows, warnings):
    """处理单个项目目录，将结果追加到 rows 和 warnings。"""
    pattern = os.path.join(project_base, '**', '*.md')
    all_files = sorted(glob.glob(pattern, recursive=True))
    prompt_files = [p for p in all_files if not p.endswith('-评价结果.md')]

    for fpath in prompt_files:
        fname = os.path.basename(fpath)
        try:
            rounds = extract_rounds_from_prompt_file(fpath)
        except Exception as e:
            warnings.append(f'[{project_name}] {fname}: 解析失败: {e}')
            continue

        if not rounds:
            warnings.append(f'[{project_name}] {fname}: 无带 trae session id 的轮次')
            continue

        # Repo ID 直接取文件第一行（即标识串），不重新构造
        repo_id = get_repo_id_from_file(fpath)

        for round_num, session_id, prompt_text in rounds:

            if not prompt_text:
                warnings.append(f'[{project_name}] {fname} 第{round_num}次 ({repo_id}): 提示词为空')

            prompt_flat = ' '.join(prompt_text.split())
            rows.append([repo_id, session_id, prompt_flat])


def main():
    global PROJECT_NAME
    rows = []
    warnings = []

    # 如果 BASE 下有直接子目录且包含 .md 文件，将每个子目录视为独立项目
    subdirs = []
    for entry in sorted(os.listdir(BASE)):
        entry_path = os.path.join(BASE, entry)
        if os.path.isdir(entry_path):
            # 检查该子目录下是否有 .md 文件
            if glob.glob(os.path.join(entry_path, '**', '*.md'), recursive=True):
                subdirs.append((entry_path, entry))

    if subdirs:
        # 一批项目目录模式
        for project_base, project_name in subdirs:
            process_project(project_base, project_name, rows, warnings)
    else:
        # 单个项目目录模式
        if not PROJECT_NAME:
            PROJECT_NAME = os.path.basename(os.path.normpath(BASE))
        process_project(BASE, PROJECT_NAME, rows, warnings)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(HEADERS)
        writer.writerows(rows)

    print(f'CSV exported: {OUTPUT}')
    print(f'Total rows: {len(rows)}')
    if warnings:
        print(f'\nWarnings ({len(warnings)}):')
        for w in warnings:
            print(f'  - {w}')

if __name__ == '__main__':
    main()
