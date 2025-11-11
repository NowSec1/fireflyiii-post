# Firefly III 记账助手

一个基于 Flask 的轻量级前后端分离应用，用于快速将交易提交到 Firefly III。

## 功能特性

- 🔐 后端代理 Firefly III 接口，统一处理认证和错误信息
- 🧾 表单支持描述、来源账户、目标账户、日期、金额、预算、分类、标签、备注等字段
- 🪄 美观易用的响应式前端界面，支持快速加载数据与提交交易
- ⚙️ 通过环境变量配置 Firefly III 访问地址和访问令牌

## 快速开始

1. **准备配置文件**

   在项目根目录创建 `config.json`（可参考 `config.example.json`），写入 Firefly III 的访问信息：

   ```json
   {
     "firefly": {
       "base_url": "https://your-firefly-instance",
       "access_token": "your-personal-access-token"
     }
   }
   ```

   > 如果仍希望通过环境变量配置，可设置 `FIREFLY_BASE_URL` 和 `FIREFLY_ACCESS_TOKEN` 作为备用方案。

2. **安装依赖**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **运行开发服务器**

   ```bash
   python wsgi.py
   ```

   访问 `http://localhost:8000`，即可看到记账页面。

   首次访问时，后端会向 Firefly III 拉取账户、预算、分类、标签等信息并缓存在 `config.json` 中。之后会优先使用缓存，且每 12 小时自动向接口拉取数据进行对比，若数据有变更会更新配置文件。

## 项目结构

```
.
├── app/                # Flask 应用与 Firefly III API 代理
│   ├── __init__.py
│   └── firefly.py
├── frontend/           # 静态前端资源
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── requirements.txt
└── wsgi.py             # 入口脚本
```

## 接口说明

- `GET /api/accounts`：获取 Firefly III 中的账户列表（默认拉取资产账户，可通过 `type` 参数调整）
- `GET /api/budgets`：获取预算列表
- `GET /api/categories`：获取分类列表
- `GET /api/tags`：获取标签列表
- `POST /api/transactions`：提交交易。请求体需包含表单字段对应的数据，后端会转换为 Firefly III API 所需结构

## 部署建议

- 在生产环境中请使用 WSGI 服务器（如 Gunicorn、uWSGI）启动 `app:create_app()`
- 根据需要在反向代理层处理 HTTPS 与访问控制
- 可通过前端部署到 CDN，并配置后端为独立 API 服务

## 许可证

MIT
