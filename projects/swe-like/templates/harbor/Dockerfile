FROM public.ecr.aws/x8v8d7g8/mars-base:latest
WORKDIR /app

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
 && git gc --prune=now

# 装本仓库依赖，含本题需求新增的依赖；能钉版本就钉。
# Python:  RUN pip install --no-cache-dir -e ".[all]"
# Go:      RUN go mod download

CMD ["bash"]
