# 设计参考

## 项目概述

- **项目名称**：宠遇 - 宠物领养平台
- **技术栈**：Vue 3 + Vite + Tailwind CSS + Spring Boot + MyBatis + MySQL
- **设计风格**：活泼、卡通、年轻化，采用大圆角、粗描边、阴影卡片等 Neo-Brutalism（新粗野主义）风格元素

## 色彩系统

定义位置：`frontend/tailwind.config.js`、`frontend/src/assets/main.css`

| 颜色       | 色值        | 用途                 |
| ---------- | ----------- | -------------------- |
| Primary    | `#3B82F6` | 主色调，链接、按钮等 |
| Secondary  | `#10B981` | 成功、可领养状态     |
| Warning    | `#F59E0B` | 警告提示             |
| Danger     | `#EF4444` | 错误、删除、退出登录 |
| Background | `#FFF4F4` | 页面背景             |
| Text       | `#4A2D2D` | 主要文字颜色         |
| Pink 400   | `#FF85A2` | 装饰色、粉色按钮     |
| Pink 500   | `#F472B6` | 强调色               |
| Yellow     | `#FFD600` | 装饰色、品牌色点缀   |

## 字体系统

| 字体         | 用途                     |
| ------------ | ------------------------ |
| Noto Sans SC | 正文、界面文字           |
| ZCOOL KuaiLe | 标题、品牌名、装饰性文字 |

详见 `assets/fonts/fonts.md`

## 图标系统

- Font Awesome 6 Free
- 通过 CDN 引入

详见 `assets/icons/icons.md`

## 组件风格

### 卡片（card-playful）

- 白色背景
- 4px 黑色描边
- 2rem 大圆角
- `box-shadow: 6px 6px 0px black`

### 按钮（btn-main / btn-playful）

- 绿色背景 `#4ADE80`
- 黑色描边
- 按压效果：向右下移动 2-3px，阴影缩小

### 输入框（input-playful）

- 白色背景
- 黑色描边
- 聚焦时：向左上移动 2px，出现阴影

## 页面布局

- 移动端优先，PC 端最大宽度 1400px
- 响应式断点：640px / 768px / 1024px / 1280px
- 导航栏：Logo + 首页/领养列表 + 登录/注册（未登录）或用户头像（已登录）

## 关键页面

| 页面     | 路由                   | 说明                       |
| -------- | ---------------------- | -------------------------- |
| 首页     | `/`                  | 展示分类入口、今日推荐宠物 |
| 宠物列表 | `/pets`              | 全部宠物，支持多维度筛选   |
| 宠物详情 | `/pet/:id`           | 单宠物详情与领养申请入口   |
| 登录     | `/login`             | 账号密码登录               |
| 注册     | `/register`          | 新用户注册                 |
| 申请领养 | `/apply/:petId`      | 填写领养申请（需登录）     |
| 个人中心 | `/user`              | 用户概览（需登录）         |
| 申请记录 | `/user/applications` | 历史申请列表               |
| 个人资料 | `/user/profile`      | 修改用户信息               |

## 参考截图

实际运行截图保存在 `assets/screenshots/` 目录下，可作为设计还原与开发参考：

- `assets/screenshots/01-home.png` — 首页
- `assets/screenshots/02-pet-list.png` — 宠物列表
- `assets/screenshots/03-pet-detail.png` — 宠物详情
- `assets/screenshots/04-login.png` — 登录页
- `assets/screenshots/05-register.png` — 注册页
- `assets/screenshots/06-user-center.png` — 个人中心
- `assets/screenshots/07-user-applications.png` — 申请记录
- `assets/screenshots/08-user-profile.png` — 个人资料

完整说明见 `assets/screenshots/README.md`。
