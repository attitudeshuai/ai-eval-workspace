# {{title}}

## 背景与目标

[描述任务的业务背景、用户场景和 agent 需要完成的核心目标。]

## 功能要求

### 模块 A

- [功能点 1]
- [功能点 2]

### 模块 B

- [功能点 3]
- [功能点 4]

## 交互要求

- [交互状态 1：如 hover、点击、输入反馈]
- [交互状态 2]
- [动画/过渡要求]

## 视觉要求

### 参考截图

- `assets/reference_desktop.png`：桌面端完整页面参考
- `assets/reference_mobile.png`：移动端完整页面参考
- `assets/interaction_state.png`：关键交互状态参考

### 设计规范

- 色彩：[主色、背景色、文字色]
- 字体：[字体族、字号层级]
- 间距：[页面边距、卡片间距、组件内边距]
- 圆角/阴影：[具体数值]
- 动效：[duration、easing、transform]

## 约束条件

- 技术栈：[React/Vue、TypeScript、Vite、Tailwind CSS 等]
- Node.js 版本：[>=18 或 >=20]
- 包管理器：[npm/pnpm/yarn]
- 禁止行为：[如禁止引入新路由、禁止使用外部图片 CDN]

## 交付标准

- [ ] 项目能 `npm install && npm run dev` 启动
- [ ] 覆盖至少 4 类关键状态（加载、空、错误、完成等）
- [ ] 桌面端与移动端均正常显示
- [ ] 通过 `tests/playwright.spec.ts` 中的核心测试
- [ ] 关键状态截图保存到 `screenshots/`

## 参考资料

- [截图说明：哪些部分高保真、哪些仅风格对齐]
