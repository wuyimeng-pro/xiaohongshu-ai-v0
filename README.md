# AI 文案工坊 · 图片小红书文案生成平台

上传一张图片，AI 自动识别图片内容，生成一篇小红书风格种草文案（标题 + 正文 + 话题标签）。支持自定义产品名称、目标人群与语气风格，生成记录按用户保存到本地 MySQL，可随时回溯历史。

## 功能特性

- 图片上传（支持 JPEG / PNG / GIF / WebP / BMP，最大 20MB）
- 阿里云 Qwen-VL 多模态大模型识图与文案生成
- 用户可选输入：产品名称、目标人群、语气风格（影响生成结果）
- 小红书笔记卡片样式展示结果，支持一键复制
- 用户注册 / 登录 / 退出（JWT 鉴权，密码加盐哈希存储）
- 历史记录：按用户展示图片、输入参数、文案与生成时间
- 完整的异常处理：图片格式、大小、接口超时、模型失败均有明确提示

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite + Vue Router + Axios |
| 后端 | Python + FastAPI + Uvicorn + PyMySQL + PyJWT |
| 大模型 | 阿里云百炼 DashScope（qwen-vl-plus） |
| 数据库 | 本地 MySQL 8.x |

## 项目结构

```text
xiaohongshu-ai-v0/
├── backend/
│   ├── main.py            # FastAPI 后端入口（鉴权、上传生成、历史查询）
│   ├── requirements.txt   # Python 依赖清单
│   ├── schema.sql         # 数据库初始化脚本
│   └── .env               # 环境变量（密钥，不入库）
├── frontend/
│   ├── src/
│   │   ├── router/        # 页面路由与登录守卫
│   │   ├── views/         # 工作台 / 历史记录 / 登录注册 / 管理台
│   │   ├── components/    # 导航栏 / 上传区 / 笔记卡片
│   │   └── api.ts         # Axios 封装（自动携带 token）
│   └── package.json
└── README.md
```

## 环境要求

- Python 3.12+（本项目开发环境为 3.14）
- Node.js 18+
- MySQL 8.x（本机安装）
- 阿里云百炼 API Key（[获取地址](https://bailian.console.aliyun.com/)）

## 快速开始

### 1. 初始化数据库

确保本机 MySQL 已启动，在 `backend` 目录执行：

```bash
mysql -uroot -p < schema.sql
```

### 2. 配置环境变量

复制 `backend/.env` 模板（或手动创建），填写以下内容：

```ini
ALIYUN_API_KEY=你的阿里云百炼APIKey
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=xiaohongshu_ai
JWT_SECRET=任意随机字符串
```

### 3. 启动后端

```bash
cd backend
python -m venv venv                # 首次
venv\Scripts\activate              # Windows
pip install -r requirements.txt    # 首次
python main.py                     # 启动，监听 127.0.0.1:8000
```

### 4. 启动前端

```bash
cd frontend
npm install        # 首次
npm run dev        # 启动，访问 http://localhost:5173
```

> 注意：前端请使用 `localhost` 访问（Vite 默认监听 localhost），不要用 `127.0.0.1:5173`。

## 环境变量清单

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `ALIYUN_API_KEY` | 阿里云百炼模型 API Key | `sk-xxxx` |
| `DB_HOST` | MySQL 地址 | `localhost` |
| `DB_USER` | MySQL 用户名 | `root` |
| `DB_PASSWORD` | MySQL 密码 | `123456` |
| `DB_NAME` | 数据库名 | `xiaohongshu_ai` |
| `JWT_SECRET` | JWT 签名密钥（任意随机字符串） | `a1b2c3...` |

## 主要接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/register` | 注册 |
| POST | `/api/login` | 登录，返回 JWT |
| POST | `/api/logout` | 退出 |
| GET | `/api/me` | 当前用户信息 |
| GET | `/api/records` | 当前用户的历史记录 |
| POST | `/upload` | 上传图片生成文案（需登录） |

## 小组成员与分工

> 待填写：请补充三位成员的名字与分工（如前端 / 后端 / 数据库与联调）。

## 演示流程建议

1. 注册账号并登录
2. 上传一张图片（可选填写产品名称、目标人群、语气风格）
3. 点击“生成小红书文案”，查看笔记卡片结果
4. 一键复制文案
5. 进入历史记录页查看刚才的生成记录

## 常见问题

- **前端打不开**：确认使用 `http://localhost:5173`，且后端已启动
- **npm 命令报错**（PowerShell 执行策略）：改用 `npm.cmd run dev`
- **生成报“未登录”**：先注册/登录，token 过期后重新登录即可
- **数据库连接失败**：确认 MySQL 已启动，且 `.env` 中数据库密码正确
