# 关键状态验收清单

本文件列出任务必须验收的关键状态。SOTA Agent 应提供对应截图或测试证据。

## 状态列表

| 编号 | 状态名称 | 触发方式 | 验收标准 | 证据位置 |
|---|---|---|---|---|
| s001 | 加载态 | 首次进入页面 / 刷新 | 显示骨架屏或 loading，无白屏 | `screenshots/state_loading.png` |
| s002 | 空态 | 清空数据 / 无结果 | 显示空状态插画与提示文案 | `screenshots/state_empty.png` |
| s003 | 错误态 | 模拟网络失败 / 异常输入 | 显示错误提示，不影响其他功能 | `screenshots/state_error.png` |
| s004 | 完成态 | 完成核心操作流程 | 显示成功反馈，状态可恢复 | `screenshots/state_success.png` |
| s005 | hover/focus 态 | 鼠标悬停 / 键盘聚焦 | 视觉反馈明显，符合可访问性 | `screenshots/state_hover.png` |
| s006 | 移动端菜单 | 视口宽度 < 768px | 汉堡菜单可展开/收起 | `screenshots/state_mobile_menu.png` |

## 截图要求

- 桌面端截图宽度：1920px
- 平板端截图宽度：768px
- 移动端截图宽度：390px
- 每张截图需包含浏览器地址栏与完整页面
