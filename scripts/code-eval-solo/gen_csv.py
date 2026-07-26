import csv, os, re, glob

# ===== 配置区：修改这两个路径即可 =====
BASE = r'd:\charles\program\ai\ai-eval-workspace\sessions\code-eval-solo\solo-demo\ai-model-result\demo-hello'
OUTPUT = r'd:\charles\program\ai\ai-eval-workspace\deliverables\code-eval-solo\solo-demo\demo-hello\csv-demo-hello-export.csv'
# =======================================

HEADERS = ['Repo ID','Trae Session ID','User Prompt','Repo URL','Commit ID','任务类型','业务领域','修改范围','任务难度','任务是否完成','过程与产物是否满意','不满意原因']

TASK_TYPE_MAP = {
    # 别名（文件名使用）→ 源类型名（CSV 输出）
    'bugfix': 'Bug修复', 'codegen': '0-1代码生成', 'feature': 'Feature迭代',
    'understand': '代码理解', 'engineering': '工程化', 'refactor': '代码重构', 'test': '代码测试',
    # 兼容旧中文文件名
    'Bug修复': 'Bug修复', '代码生成': '0-1代码生成', 'Feature迭代': 'Feature迭代',
    '代码理解': '代码理解', '代码重构': '代码重构', '工程化': '工程化', '代码测试': '代码测试',
}

def extract_field(text, field_name):
    pattern = rf'## {re.escape(field_name)}\s*\n(.*?)(?=\n## |\n# |\Z)'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return ''
    content = m.group(1)
    # Session ID / Commit ID / Repo URL 必须原文逐字复制，
    # 取第一行非空内容，跳过注释标记行，不做 strip（保留内部所有字符）
    if field_name in ('Session ID', 'Commit ID', 'Repo URL'):
        for raw_line in content.splitlines():
            line = raw_line.rstrip('\r')
            if not line:
                continue
            if line.strip() == '【必须原文逐字复制，禁止改写】':
                continue
            return line
        return ''
    return content.strip()

def extract_blocks(text):
    blocks = re.split(r'(?=^# .+ 第\s*\d+\s*次对话评价结果)', text, flags=re.MULTILINE)
    return [b.strip() for b in blocks if b.strip() and re.match(r'^# .+ 第\s*\d+\s*次对话评价结果', b.strip())]

def infer_task_type(filename, round_num):
    if round_num >= 2:
        return 'Bug修复'
    for key, val in TASK_TYPE_MAP.items():
        if key in filename:
            return val
    return ''

def infer_business_domain(prompt):
    p = prompt.lower()
    if any(k in p for k in ['前端', '页面', '小程序', '组件', 'ui', '界面']):
        return '全栈Web应用' if any(k in p for k in ['后端', '接口', 'api', '数据库']) else 'Web前端'
    if any(k in p for k in ['后端', '接口', 'api', '服务', '数据库', '实体', 'mapper', 'controller']):
        return '纯后端服务'
    return '纯后端服务'

if __name__ == '__main__':
    rows, warnings = [], []

    for fpath in sorted(glob.glob(os.path.join(BASE, '**', '*-评价结果.md'), recursive=True)):
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = extract_blocks(content)
        if not blocks:
            warnings.append(f'{fname}: 无评价结果块，已跳过')
            continue

        for i, block in enumerate(blocks):
            round_num = i + 1
            repo_id = extract_field(block, '标志：') or extract_field(block, '标志')
            if not repo_id:
                m = re.search(r'###\s*标志[：:]\s*\n\s*(\S+)', block)
                if m:
                    repo_id = m.group(1)
            if not repo_id:
                warnings.append(f'{fname} 第{round_num}次: 无标志段，已跳过')
                continue

            session_id = extract_field(block, 'Session ID')
            if not session_id:
                warnings.append(f'{fname} 第{round_num}次 ({repo_id}): Session ID 为空，请人工核查')

            prompt = ' '.join(extract_field(block, '提示词').split())
            repo_url = extract_field(block, 'Repo URL')
            commit_id = extract_field(block, 'Commit ID')
            task_type = infer_task_type(fname, round_num)
            domain = infer_business_domain(prompt)
            scope = extract_field(block, '修改范围') or '跨模块多文件（推断）'
            difficulty = extract_field(block, '任务难度') or '一般'

            completed = extract_field(block, '是否完成')
            if not completed:
                warnings.append(f'{fname} 第{round_num}次 ({repo_id}): 是否完成字段缺失，请人工核查')

            satisfied_raw = extract_field(block, '是否满意')
            satisfied = satisfied_raw
            if satisfied_raw and satisfied_raw not in ('满意', '不满意'):
                warnings.append(f'{fname} 第{round_num}次 ({repo_id}): 是否满意值异常: {satisfied_raw}')

            unsatisfied = extract_field(block, '不满意的点') if satisfied == '不满意' else ''
            if unsatisfied == '无':
                unsatisfied = ''

            rows.append([repo_id, session_id, prompt, repo_url, commit_id, task_type, domain, scope, difficulty, completed, satisfied, unsatisfied])

    rows.sort(key=lambda r: int(m.group(1)) if (m := re.search(r'-(\d+)$', r[0])) else 0)

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
