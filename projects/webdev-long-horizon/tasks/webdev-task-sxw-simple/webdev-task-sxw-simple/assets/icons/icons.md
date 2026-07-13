# 图标说明

本项目图标统一使用 Font Awesome 6 免费版，通过 CDN 引入，未在仓库中存放图标文件。

## 引入方式

在 `frontend/index.html` 中通过 CDN 引入：

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
```

## 使用方式

在 Vue 模板中通过 `<i>` 标签使用：

```html
<!-- 示例：加载中图标 -->
<i class="fas fa-spinner animate-spin mr-2"></i>

<!-- 示例：搜索图标 -->
<i class="fas fa-search"></i>

<!-- 示例：用户图标 -->
<i class="fas fa-user"></i>
```

## 常用图标类

| 用途 | 类名 |
|---|---|
| 加载中 | `fas fa-spinner` |
| 搜索 | `fas fa-search` |
| 用户 | `fas fa-user` |
| 首页/导航 | 视页面而定 |

## 本地使用建议

如需离线使用，可下载 Font Awesome 6 Free 到本目录，并修改 `index.html` 的引用路径为本地 CSS 文件。
