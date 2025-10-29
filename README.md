# Firefly III 记账助手

一个基于 Flask 的轻量级前后端分离应用，用于快速将交易提交到 Firefly III。

## 功能特性

- 🔐 后端代理 Firefly III 接口，统一处理认证和错误信息
- 🧾 表单支持描述、来源账户、目标账户、日期、金额、预算、分类、标签、备注等字段
- 🪄 美观易用的响应式前端界面，支持快速加载数据与提交交易
- ⚙️ 通过环境变量配置 Firefly III 访问地址和访问令牌

## 快速开始

1. **准备环境变量**

   ```bash
   export FIREFLY_BASE_URL="https://your-firefly-instance"
   export FIREFLY_ACCESS_TOKEN="your-personal-access-token"
   ```

   > 建议使用 [`python-dotenv`](https://pypi.org/project/python-dotenv/) 或其他方式管理本地开发时的环境变量。

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
