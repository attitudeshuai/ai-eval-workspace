import sys
import re
import subprocess
import os


def extract_session_id_from_prompt(file_path: str, round_n: int) -> str:
    """从提示词文件中提取指定轮次的 session id（与 extract_session_id.py 逻辑一致）。"""
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    prompt_lines = {}
    session_lines = {}
    answer_lines = {}

    cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
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

    if round_n not in session_lines:
        return ''

    line_idx = session_lines[round_n]
    sid_inline = re.sub(
        r'^模型第?(?:\d+|一|二|三|四|五|六|七|八|九|十)次回答 trae session id[：:]?\s*', '', lines[line_idx]
    ).strip()

    if sid_inline:
        return sid_inline
    block_text = get_block_text(line_idx)
    for line in block_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ''


def extract_review_fields(file_path: str):
    """从评价结果文件中提取每一轮的 Session ID 和 Commit ID。"""
    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    round_headers = list(re.finditer(
        r'^# .+ 第 (\d+) 次对话评价结果', content, re.MULTILINE))

    results = []
    for i, m in enumerate(round_headers):
        round_n = int(m.group(1))
        start = m.start()
        end = round_headers[i + 1].start() if i + 1 < len(round_headers) else len(content)
        block = content[start:end]

        session_match = re.search(
            r'## Session ID\s*\n\s*(?:【必须原文逐字复制，禁止改写】)?\s*(.*?)\s*(?=\n## |\Z)',
            block, re.DOTALL)
        session_id = session_match.group(1).strip() if session_match else ''
        session_id = re.sub(r'<!--.*?-->', '', session_id).strip()

        commit_match = re.search(
            r'## Commit ID\s*\n\s*(?:【必须原文逐字复制，禁止改写】)?\s*([^\n]*?)\s*(?=\n## |\Z)',
            block)
        commit_id = commit_match.group(1).strip() if commit_match else ''
        commit_id = re.sub(r'<!--.*?-->', '', commit_id).strip()

        results.append((round_n, session_id, commit_id))

    return results


def get_commit_message(repo_path: str, commit_hash: str) -> str:
    """通过 git 获取指定 commit hash 的 message。"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-1', '--format=%B', commit_hash],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ''


def verify_review(review_path: str, prompt_path: str, repo_path: str) -> bool:
    """
    验证评价结果：
    1. Session ID == 提示词原始 session id
    2. Commit ID 是有效的 commit hash，且其 message == Session ID
    """
    review_fields = extract_review_fields(review_path)
    if not review_fields:
        print("未找到任何评价轮次，请检查评价结果文件格式。", file=sys.stderr)
        return False

    all_pass = True

    for round_n, session_id, commit_id in review_fields:
        prompt_sid = extract_session_id_from_prompt(prompt_path, round_n)
        issues = []

        # 校验 1：Session ID 与提示词一致
        if session_id != prompt_sid:
            issues.append(
                f"Session ID 与提示词不一致（评价结果: '{session_id}' vs 提示词: '{prompt_sid}'）"
            )

        # 校验 2：Commit ID 有效性及 message 匹配
        if not commit_id:
            # Commit ID 为空可能是代码理解类型（无代码提交），仅提示不报错
            print(f"  ℹ️ Commit ID 为空（可能为代码理解类型，无代码提交）")
        else:
            commit_msg = get_commit_message(repo_path, commit_id)
            if not commit_msg:
                issues.append(f"Commit ID '{commit_id}' 在仓库中不存在或无效")
            elif commit_msg != session_id:
                issues.append(
                    f"Commit ID '{commit_id}' 的 message 与 Session ID 不一致"
                    f"（commit message: '{commit_msg}' vs Session ID: '{session_id}'）"
                )

        if not issues:
            print(f"轮次 {round_n}: ✅ 通过")
        else:
            print(f"轮次 {round_n}: ❌ 失败")
            for issue in issues:
                print(f"  - {issue}")
            all_pass = False

    return all_pass


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(
            "Usage: python verify_review.py <评价结果文件> <提示词文件> <git仓库路径>",
            file=sys.stderr
        )
        sys.exit(1)

    review_path = sys.argv[1]
    prompt_path = sys.argv[2]
    repo_path = sys.argv[3]
    ok = verify_review(review_path, prompt_path, repo_path)
    sys.exit(0 if ok else 1)
