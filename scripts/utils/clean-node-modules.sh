#!/usr/bin/env bash
#
# clean-node-modules.sh
# 递归删除「目标目录」及其所有子目录下的 node_modules 文件夹。
#
# 适用场景：清理前端项目目录下所有依赖，腾出磁盘空间。
# 路径可改：用第 1 个参数传入目标目录，或直接改下面的 TARGET_DIR 变量。
#
# 用法：
#   ./clean-node-modules.sh [目标目录] [选项]
#
# 选项：
#   -n, --dry-run   试运行：只列出将要删除的目录，不真的删
#   -y, --yes       跳过确认提示，直接删除
#   -s, --sizes     同时统计每个 node_modules 的大小（较慢）
#   -h, --help      显示本帮助
#
# 示例：
#   ./clean-node-modules.sh                            # 用下方 TARGET_DIR 的默认值
#   ./clean-node-modules.sh "/Users/me/前端项目"        # 清理指定目录
#   ./clean-node-modules.sh "/Users/me/前端项目" -n     # 先试运行看看
#   ./clean-node-modules.sh "/Users/me/前端项目" -y     # 不用确认直接删
#
# 说明：
#   - 默认使用 TARGET_DIR 变量；若指定了命令行参数，则优先用命令行参数。
#   - 只删除名字恰好为 node_modules 的目录/符号链接，不误伤其它内容。
#   - 既处理真实目录（rm -rf）也处理符号链接（只删链接本身，安全）。
#   - 支持含空格、中文等特殊字符的路径。

set -euo pipefail

# ---------- 默认目标目录（可在这里改，或用第 1 个参数覆盖） ----------
TARGET_DIR="${TARGET_DIR:-}"

# ---------- 解析参数 ----------
DRY_RUN=0
ASSUME_YES=0
SHOW_SIZES=0
declare -a POSITIONAL=()

for arg in "$@"; do
  case "$arg" in
    -n|--dry-run)  DRY_RUN=1 ;;
    -y|--yes)      ASSUME_YES=1 ;;
    -s|--sizes)    SHOW_SIZES=1 ;;
    -h|--help)     sed -n '2,30p' "$0"; exit 0 ;;
    *)             POSITIONAL+=("$arg") ;;
  esac
done

# 命令行参数优先于 TARGET_DIR 变量
if [[ "${#POSITIONAL[@]}" -gt 0 ]]; then
  TARGET_DIR="${POSITIONAL[0]}"
fi

# ---------- 校验目标目录 ----------
if [[ -z "$TARGET_DIR" ]]; then
  echo "[错误] 没有指定目标目录。" >&2
  echo "用法：$0 [目标目录] [选项]   （或修改脚本里的 TARGET_DIR 变量）" >&2
  exit 1
fi

# 去掉尾部的斜杠，方便后续拼接
TARGET_DIR="${TARGET_DIR%/}"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "[错误] 目标目录不存在或不是目录：$TARGET_DIR" >&2
  exit 1
fi

# 转成绝对路径，打印时更直观
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
echo "目标目录：$TARGET_DIR"
echo

# ---------- 找出所有 node_modules ----------
# 用 \0 分隔，规避文件名中的空格/换行/中文等特殊字符问题
mapfile_dummy=()   # placeholder；实际用 while 循环读取
count=0
items=()

while IFS= read -r -d '' path; do
  items+=("$path")
  count=$((count + 1))
done < <(find "$TARGET_DIR" -mindepth 1 -name node_modules -prune -print0)

if [[ "$count" -eq 0 ]]; then
  echo "没有找到任何 node_modules，无需清理。"
  exit 0
fi

echo "共发现 $count 个 node_modules："
for path in "${items[@]}"; do
  if [[ -L "$path" ]]; then
    echo "  [链接] $path"
  else
    echo "  [目录] $path"
  fi
done

# ---------- 统计总大小（可选） ----------
TOTAL_KB=0
if [[ "$SHOW_SIZES" -eq 1 ]]; then
  echo
  echo "正在统计大小（可能较慢）..."
  for path in "${items[@]}"; do
    if [[ -d "$path" && ! -L "$path" ]]; then
      size_kb=$(du -sk "$path" 2>/dev/null | awk '{print $1}')
      size_kb=${size_kb:-0}
    else
      size_kb=0
    fi
    TOTAL_KB=$((TOTAL_KB + size_kb))
    human=$(awk -v kb="$size_kb" 'BEGIN{printf "%.1fMB", kb/1024}')
    printf "  %10s  %s\n" "$human" "$path"
  done
  total_human=$(awk -v kb="$TOTAL_KB" 'BEGIN{printf "%.2fGB", kb/1024/1024}')
  echo
  echo "预计释放空间：${total_human}（仅统计真实目录）"
fi

# ---------- 确认 ----------
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo
  echo "[试运行] 以上是将会被删除的 node_modules，未做任何删除。"
  exit 0
fi

if [[ "$ASSUME_YES" -eq 0 ]]; then
  echo
  read -r -p "确认删除以上全部 $count 个 node_modules？[y/N] " reply
  case "$reply" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "已取消，未删除任何内容。"; exit 0 ;;
  esac
fi

# ---------- 删除 ----------
echo
echo "开始删除..."
removed=0
for path in "${items[@]}"; do
  if [[ -L "$path" ]]; then
    # 符号链接：只删链接本身，安全
    rm -f "$path"
  else
    rm -rf "$path"
  fi
  removed=$((removed + 1))
  echo "  已删除 $path"
done

echo
echo "完成：共删除 $removed 个 node_modules。"
