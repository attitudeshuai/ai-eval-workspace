"""
GSB Session ID 提取、验证与同步工具
从对话内容文件中提取各轮次 Session ID，与评价结果文件进行交叉验证和同步。
"""

import os
import re
import sys
from config_loader import load_config
from path_resolver import get_dialogue_file_path, get_review_file_path


def extract_session_ids_from_dialogue(text: str) -> list:
    """
    从对话内容文件中提取每轮的 Session ID。
    返回 [(round_num, session_id), ...]
    """
    results = []
    lines = text.splitlines()
    i = 0
    cn_to_arabic = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }
    while i < len(lines):
        line = lines[i]
        # 匹配 "模型第X次回答 trae session id" 或 "模型第X次回答 session id"
        m = re.match(
            r"模型第([一二三四五六七八九十\d]+)次回答\s+trae\s+session\s*id\s*[:：]\s*$",
            line.strip(),
            re.IGNORECASE,
        )
        if not m:
            m = re.match(
                r"模型第([一二三四五六七八九十\d]+)次回答\s+session\s*id\s*[:：]\s*$",
                line.strip(),
                re.IGNORECASE,
            )
        if m:
            round_num_str = m.group(1)
            if round_num_str.isdigit():
                round_num = int(round_num_str)
            else:
                round_num = cn_to_arabic.get(round_num_str, 0)
            sid = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].rstrip("\r")
                if next_line.strip() == "":
                    j += 1
                    continue
                # 如果下一行是已知标签，说明 session id 为空
                if re.match(
                    r"(?:修改范围|模型第|用户第|修改文件|涉及文件|##|约束标签|注)\s*[:：]",
                    next_line.strip(),
                ):
                    break
                # 特别处理：如果下一行是 "模型第X次回答内容" 也停止
                if re.match(r"模型第.*次回答内容", next_line.strip()):
                    break
                sid = next_line
                break
            results.append((round_num, sid))
            i = j + 1 if j > i else i + 1
            continue
        i += 1
    return results


def extract_session_ids_from_review(text: str) -> list:
    """
    从评价结果文件中提取每轮的 Session ID。
    支持格式：
      - ## 第N次对话评价结果（solo 项目格式）
      - ## 第N轮评价（gsb 项目格式）
    返回 [(round_num, session_id), ...]
    """
    pattern = r"##\s*Session\s*ID\s*\n(.*?)(?=\n## |\n# |\Z)"
    # 按评价块分割：支持 "第 N 次对话评价结果" 或 "第 N 轮评价"（N 可以是阿拉伯数字或中文数字）
    blocks = re.split(r"(?=^##\s*第\s*(?:[一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价))", text, flags=re.MULTILINE)
    results = []
    cn_to_arabic = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }
    for block in blocks:
        block = block.strip()
        if not block or not re.match(r"^##\s*第\s*(?:[一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价)", block):
            continue
        round_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价)", block)
        if round_match:
            rstr = round_match.group(1)
            round_num = int(rstr) if rstr.isdigit() else cn_to_arabic.get(rstr, 0)
        else:
            round_num = 0
        m = re.search(pattern, block, re.DOTALL)
        if m:
            content = m.group(1)
            for raw_line in content.splitlines():
                line = raw_line.rstrip("\r")
                if not line:
                    continue
                if line.strip() == "【必须原文逐字复制，禁止改写】":
                    continue
                results.append((round_num, line))
                break
            else:
                results.append((round_num, ""))
        else:
            results.append((round_num, ""))
    return results


def verify_session_id_consistency(dialogue_path: str, review_path: str) -> dict:
    """
    验证单个模型的对话内容文件与评价结果文件中的 Session ID 是否完全一致。
    返回 {"ok": bool, "issues": [{file, round, source, review, diff_pos}, ...]}
    """
    issues = []
    with open(dialogue_path, "r", encoding="utf-8") as f:
        dialogue_sids = {r: sid for r, sid in extract_session_ids_from_dialogue(f.read())}
    if not os.path.exists(review_path):
        return {"ok": False, "issues": [{"file": review_path, "error": "评价结果文件不存在"}]}
    with open(review_path, "r", encoding="utf-8") as f:
        review_sids = extract_session_ids_from_review(f.read())

    for round_num, review_sid in review_sids:
        source_sid = dialogue_sids.get(round_num)
        if source_sid is None:
            continue
        if review_sid != source_sid:
            diff_pos = None
            min_len = min(len(source_sid), len(review_sid))
            for idx in range(min_len):
                if source_sid[idx] != review_sid[idx]:
                    diff_pos = idx
                    break
            if diff_pos is None and len(source_sid) != len(review_sid):
                diff_pos = min_len
            issues.append(
                {
                    "file": os.path.basename(review_path),
                    "round": round_num,
                    "source": source_sid,
                    "review": review_sid,
                    "diff_pos": diff_pos,
                }
            )

    return {"ok": len(issues) == 0, "issues": issues}


def verify_all_models(project_name: str, task_type: str, config: dict = None) -> dict:
    """
    验证某项目某类型下所有模型的 Session ID 一致性。
    返回 {"ok": bool, "total_checked": int, "total_issues": int, "details": [...]}
    """
    cfg = config or load_config()
    details = []
    total_checked = 0
    total_issues = 0
    for m in cfg.get("models", []):
        slug = m.get("slug", "")
        if not slug:
            continue
        dialogue_path = get_dialogue_file_path(project_name, task_type, slug, cfg)
        review_path = get_review_file_path(project_name, task_type, slug, cfg)
        if not os.path.exists(dialogue_path):
            continue
        if not os.path.exists(review_path):
            continue
        result = verify_session_id_consistency(dialogue_path, review_path)
        total_checked += len(
            [r for r, _ in extract_session_ids_from_dialogue(open(dialogue_path, "r", encoding="utf-8").read())]
        )
        if result["issues"]:
            total_issues += len(result["issues"])
            details.extend(result["issues"])
    return {
        "ok": total_issues == 0,
        "total_checked": total_checked,
        "total_issues": total_issues,
        "details": details,
    }


def sync_session_ids(dialogue_path: str, review_path: str) -> bool:
    """
    将对话内容文件中的 Session ID 同步到评价结果文件中。
    返回是否进行了修改。
    """
    with open(dialogue_path, "r", encoding="utf-8") as f:
        dialogue_sids = {r: sid for r, sid in extract_session_ids_from_dialogue(f.read())}

    if not os.path.exists(review_path):
        return False

    with open(review_path, "r", encoding="utf-8") as f:
        review_content = f.read()
    original = review_content

    parts = re.split(r"(?=^##\s*第\s*(?:[一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价))", review_content, flags=re.MULTILINE)
    new_parts = []
    cn_to_arabic = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }

    for part in parts:
        block = part
        if not re.match(r"^##\s*第\s*(?:[一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价)", block.strip()):
            new_parts.append(block)
            continue

        round_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*(?:次对话评价结果|轮评价)", block)
        if not round_match:
            new_parts.append(block)
            continue
        rstr = round_match.group(1)
        round_num = int(rstr) if rstr.isdigit() else cn_to_arabic.get(rstr, 0)
        correct_sid = dialogue_sids.get(round_num)
        if correct_sid is None:
            new_parts.append(block)
            continue

        sid_pattern = r"(##\s*Session\s*ID\s*\n)(.*?)(?=\n## |\n# |\Z)"
        sid_match = re.search(sid_pattern, block, re.DOTALL)
        if not sid_match:
            new_parts.append(block)
            continue

        current_block = sid_match.group(2)
        current_sid = ""
        for raw_line in current_block.splitlines():
            line = raw_line.rstrip("\r")
            if not line:
                continue
            if line.strip() == "【必须原文逐字复制，禁止改写】":
                continue
            current_sid = line
            break

        if current_sid == correct_sid:
            new_parts.append(block)
            continue

        new_sid_block = "【必须原文逐字复制，禁止改写】\n" + correct_sid
        start = sid_match.start(1) + len(sid_match.group(1))
        end = sid_match.end()
        new_block = block[:start] + new_sid_block + block[end:]
        new_parts.append(new_block)

    new_content = "".join(new_parts)
    if new_content != original:
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def sync_all_models(project_name: str, task_type: str, config: dict = None) -> dict:
    """
    同步某项目某类型下所有模型的 Session ID。
    返回 {"fixed": int, "checked": int, "details": [str]}
    """
    cfg = config or load_config()
    fixed = 0
    checked = 0
    details = []
    for m in cfg.get("models", []):
        slug = m.get("slug", "")
        if not slug:
            continue
        dialogue_path = get_dialogue_file_path(project_name, task_type, slug, cfg)
        review_path = get_review_file_path(project_name, task_type, slug, cfg)
        if not os.path.exists(dialogue_path) or not os.path.exists(review_path):
            continue
        checked += 1
        if sync_session_ids(dialogue_path, review_path):
            fixed += 1
            details.append(f"已修正: {os.path.basename(review_path)}")
    return {"fixed": fixed, "checked": checked, "details": details}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GSB Session ID 工具")
    parser.add_argument("command", choices=["verify", "sync"], help="verify=验证, sync=同步")
    parser.add_argument("project_name", help="项目名（可不带前缀）")
    parser.add_argument("task_type", help="任务类型")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    cfg = load_config(args.config) if args.config else None
    pname = args.project_name

    if args.command == "verify":
        result = verify_all_models(pname, args.task_type, cfg)
        print(f"共检查 {result['total_checked']} 个 Session ID 条目")
        print(f"发现 {result['total_issues']} 处不一致")
        for issue in result["details"]:
            print(f"  文件: {issue['file']} 第{issue['round']}次")
            print(f"    对话内容: {issue['source']}")
            print(f"    评价结果: {issue['review']}")
        sys.exit(0 if result["ok"] else 1)
    elif args.command == "sync":
        result = sync_all_models(pname, args.task_type, cfg)
        print(f"共检查 {result['checked']} 个评价结果文件，修正 {result['fixed']} 个")
        for d in result["details"]:
            print(f"  {d}")
