FROM public.ecr.aws/x8v8d7g8/mars-base:latest
WORKDIR /app

# ↓↓↓ 时间旅行段：整段照抄，只填下面两个 ARG ↓↓↓
# BASE_SHA 必须与 task.toml 的 base_commit 完全一致（40 位完整 SHA）
ARG REPO_URL=
ARG BASE_SHA=
RUN git clone "$REPO_URL" . \
 && DEFAULT="$(git remote show origin | sed -n 's/.*HEAD branch: //p')" \
 && git checkout -B "$DEFAULT" "$BASE_SHA" \
 && git remote remove origin \
 && for b in $(git for-each-ref --format='%(refname:short)' refs/heads | grep -vx "$DEFAULT"); do git branch -D "$b" || true; done \
 && for t in $(git tag); do git merge-base --is-ancestor "$t" HEAD 2>/dev/null || git tag -d "$t"; done \
 && git reflog expire --expire=now --all \
 && git gc --prune=now \
 && (git submodule update --init --recursive || true) \
 && git config core.hooksPath /dev/null
# ↑↑↑ 时间旅行段结束 ↑↑↑

# 装这个仓库自己的依赖，包括因为本题需求而新增的依赖。能钉版本就钉，避免上游漂移让老题构建失败。
# Python:     RUN pip install --no-cache-dir -e ".[all]"
# Go:         RUN go mod download
RUN echo "把这一行换成本仓库的依赖安装命令" && false

# 缺系统库就在这里加，不要换上面的 FROM
# RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

CMD ["bash"]
