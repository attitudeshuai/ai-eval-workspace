import sys, re

def parse_prompt_file(file_path, round_n=0):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    # 定位所有轮次的各段起始行（0-based）
    prompt_lines = {}   # round -> line index
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

    rounds = sorted(prompt_lines.keys())

    if round_n == 0:
        # 列出所有轮次摘要
        print(f"{'轮次':<4} {'有提示词':<8} {'有回答内容':<10} {'SessionID':<40} 提示词摘要")
        print("-" * 90)
        for n in rounds:
            prompt_text = get_block_text(prompt_lines[n])
            has_prompt = bool(prompt_text)
            sid = ''
            if n in session_lines:
                sid_inline = re.sub(r'^模型第?(?:\d+|一|二|三|四|五|六|七|八|九|十)次回答 trae session id[：:]?\s*', '', lines[session_lines[n]]).strip()
                sid = sid_inline if sid_inline else get_block_text(session_lines[n])
            has_answer = False
            if n in answer_lines:
                has_answer = bool(get_block_text(answer_lines[n]))
            summary = prompt_text[:60].replace('\n', ' ') + ('…' if len(prompt_text) > 60 else '')
            print(f"{n:<4} {'是' if has_prompt else '否':<8} {'是' if has_answer else '否':<10} {sid:<40} {summary}")
    else:
        # 输出指定轮次详情
        n = round_n
        prompt_text = get_block_text(prompt_lines[n]) if n in prompt_lines else ''
        sid = ''
        if n in session_lines:
            sid_inline = re.sub(r'^模型第\d+次回答 trae session id[：:]?\s*', '', lines[session_lines[n]]).strip()
            sid = sid_inline if sid_inline else get_block_text(session_lines[n])
        answer_text = get_block_text(answer_lines[n]) if n in answer_lines else ''
        answer_start = (answer_lines[n] + 2) if n in answer_lines else 0  # 1-based
        print(f"=== SESSION_ID ===\n{sid}")
        print(f"=== PROMPT ===\n{prompt_text}")
        print(f"=== ANSWER_START_LINE (1-based) ===\n{answer_start}")
        print(f"=== ANSWER ===\n{answer_text}")

if __name__ == '__main__':
    path = sys.argv[1]
    rnd = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    parse_prompt_file(path, rnd)
