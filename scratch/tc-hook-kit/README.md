# tc-hook-kit

轻量 Trae Hook 接收端：接收事件、验证 HMAC 签名，并统计有效工具调用次数（TC）。

## 使用

需要 Python 3 和支持 ES 模块、内置 `fetch` 的 Node.js。

```bash
# 启动接收端
bash tc-hook serve --host 127.0.0.1 --port 8765

# 在另一终端安装 Hook
bash tc-hook install --host 127.0.0.1 --port 8765

# 查询统计
bash tc-hook stats
```

安装器会修改本机 Trae Hook 配置，并生成运行时配置。Bridge 和接收端必须使用同一密钥；跨机器部署时请自行安全同步配置。

密钥和运行时配置不随仓库发布。`bridge.runtime.json`、本地配置、事件数据库、日志和 Python 缓存已加入 `.gitignore`。不要提交这些文件。

完整接口与统计规则见 [API.md](API.md)。其中的 `scripts/tc-hook-kit/` 路径表示嵌入其他项目时的布局；在本仓库根目录使用时可省略该前缀。
