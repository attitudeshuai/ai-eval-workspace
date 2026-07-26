import sys
import re


def extract_session_id(file_path: str, round_n: int) -> str:
    """
    从提示词文件中精确提取指定轮次的 trae session id。
    提取逻辑与 parse_prompt.py 完全一致（含 fallback），
    但只返回 session id 字符串本身，不含任何额外格式或换行。
    """
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    # 定位所有轮次的各段起始行（0-based）
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
        """获取 start_line 之后到下一个标记行之前的文本"""
        next_marks = [x for x in all_marks if x > start_line]
        end = next_marks[0] if next_marks else len(lines)
        return ''.join(lines[start_line + 1:end]).strip()

    if round_n not in session_lines:
        return ''

    line_idx = session_lines[round_n]

    # 先尝试行内提取（同时支持阿拉伯数字和中文数字）
    sid_inline = re.sub(
        r'^模型第?(?:\d+|一|二|三|四|五|六|七|八|九|十)次回答 trae session id[：:]?\s*', '', lines[line_idx]
    ).strip()

    # fallback：行内为空时，读取下一块（与 parse_prompt.py 一致），
    # 但只取第一个非空片段（避免把后续的"修改范围"等内容带进来）
    if sid_inline:
        return sid_inline
    block_text = get_block_text(line_idx)
    for line in block_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ''


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python extract_session_id.py <提示词文件路径> <轮次>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    round_n = int(sys.argv[2])
    sid = extract_session_id(file_path, round_n)
    print(sid, end='')
