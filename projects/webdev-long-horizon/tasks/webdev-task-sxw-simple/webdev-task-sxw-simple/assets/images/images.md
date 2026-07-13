# 图片资源说明

本项目中的宠物图片、用户头像等均为外部链接，未在仓库中存放原始图片文件。

## 图片来源

### 1. 宠物图片
- **来源**：Unsplash（https://unsplash.com/）
- **用途**：宠物列表、宠物详情、首页推荐等
- **示例**：
  ```
  https://images.unsplash.com/photo-1552053831-71594a27632d?w=800&auto=format&fit=crop&q=60
  ```
- **存放位置**：数据库 `pet.images` 字段，以逗号分隔多个 URL

### 2. 用户头像
- **来源**：Unsplash
- **用途**：用户中心、个人资料等
- **示例**：
  ```
  https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200
  ```
- **存放位置**：数据库 `user.avatar` 字段

### 3. 本地图片目录

项目预留了本地图片目录：
- `frontend/public/images/avatars/` — 用于存放本地头像图片
- `frontend/public/images/` — 用于存放其他本地图片

当前这些目录为空，所有展示图片均来自外部 URL。

## favicon

`frontend/index.html` 中引用了：
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

当前 `frontend/public/favicon.svg` 文件不存在，如需使用可补充该 SVG 文件。

## 本地使用建议

如需将图片本地化，可下载 Unsplash 图片到 `frontend/public/images/` 目录下，并修改数据库中的 URL 为相对路径（如 `/images/pets/xxx.jpg`）。
