# 字体说明

本项目前端使用 Google Fonts 在线字体，未在仓库中存放字体文件。

## 引入方式

在 `frontend/index.html` 中通过 CDN 引入：

```html
<link href="https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
```

## 字体配置

### 1. Noto Sans SC
- **用途**：正文字体，主要用于界面正文、按钮、标签等
- **字重**：400 / 500 / 700 / 900
- **配置位置**：
  - `frontend/src/assets/main.css`：`font-family: 'Noto Sans SC', sans-serif;`
  - `frontend/tailwind.config.js`：`fontFamily.sans: ['Noto Sans SC', 'sans-serif']`

### 2. ZCOOL KuaiLe（站酷快乐体）
- **用途**：标题/装饰字体，用于品牌名称、大标题等活泼场景
- **配置位置**：
  - `frontend/tailwind.config.js`：`fontFamily.playful: ['ZCOOL KuaiLe', 'cursive']`
  - 部分组件内联样式：`style="font-family: 'ZCOOL KuaiLe', cursive;"`

## 本地使用建议

如需离线使用，可从 Google Fonts 下载对应字体文件（.ttf / .woff2），放入本目录，并修改 `index.html` 与 `tailwind.config.js` 的引用路径。
