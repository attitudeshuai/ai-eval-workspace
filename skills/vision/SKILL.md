---
name: vision
description: |
  识图能力：让不具备原生视觉能力的模型也能"看图"。把本地图片或图片 URL 交给
  外部 vision 模型（OpenAI 兼容 API，默认阿里云百炼千问），用文字描述返回。
  当任务涉及分析、描述、识别图片内容时使用。
---

# Vision: 识图

底层模型不具备原生识图能力时，遇到图片**不要用 Read 工具**，改用 `vision.js`：

```bash
node skills/vision/vision.js "<图片路径>" "用中文描述这张图片"
```

支持网络图片：

```bash
node skills/vision/vision.js --url "<图片链接>" "用中文描述这张图片"
```

## 触发场景

- 用户分享图片路径（本地或网络 URL）
- 消息中出现 "Saved attachments:" 并列出图片
- 用户要求分析、描述、识别图片内容

对每张图片依次执行，拿到所有文字描述后再回复。

## 配置

Key 与模型名放在 `skills/vision/.env`（已被 gitignore，勿提交）：

```env
DASHSCOPE_API_KEY=sk-xxx
VISION_MODEL=qwen3-vl-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

- 推荐阿里云百炼千问（新用户有免费额度），Key 在 https://bailian.console.aliyun.com/ 申请
- 用 OpenAI 或其他 OpenAI 兼容服务时，改 `DASHSCOPE_BASE_URL` 和 `VISION_MODEL` 即可

## 手动验证

```bash
node skills/vision/vision.js "<测试图片路径>" "请描述这张图片"
```
