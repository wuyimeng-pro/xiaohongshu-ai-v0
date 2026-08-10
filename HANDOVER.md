# 项目交接文档

> 给新 Codex 窗口（或新接手成员）的完整上下文。开始工作前请先通读本文件。
> 项目路径：`C:\Users\admin\Desktop\xiaohongshu-ai-v0`
> GitHub 仓库：https://github.com/wuyimeng-pro/xiaohongshu-ai-v0 （分支 main，已同步）

## 1. 项目是什么

“AI 文案工坊”：上传一张图片（本地文件或在线 URL），后端调用阿里云百炼 Qwen-VL-Plus 多模态大模型识别图片内容，生成小红书风格种草文案（标题 ≤20 字 + 正文 + 3~5 个 #标签）。支持用户补充产品名称/目标人群/语气风格，支持多轮调优、多版本对比、流式逐字输出，按用户保存历史，含官网首页与后台管理台。

这是新人实战考核项目（3 人一组，一周），需求文档在桌面：`MinerU_markdown_测试题目v4.0-图片小红书文案生成平台_(1)_2085511718157455360.md`。

## 2. 当前状态（2026-08-10）

- ✅ 前后端和 MySQL 都在运行：前端 `http://localhost:5173`（注意用 localhost 不是 127.0.0.1），后端 `http://127.0.0.1:8000`，MySQL 3306
- ✅ 基本功能需求全部完成
- ✅ 加分项全部完成（本地模型部署除外，已放弃；Docker 文件已写好但本机未装 Docker，未实际构建验证）
- ✅ 全链路回归 25/25 通过（脚本 `regression_test.ps1`）
- ✅ Git 已同步 GitHub（最新提交 `f85df2d`）
- ⚠️ README 中“小组成员与分工”仍是占位符，等用户提供 3 人名字与分工后填写

## 3. 已完成功能清单

**核心**
- 本地上传图片生成文案（格式校验 JPEG/PNG/GIF/WebP/BMP，大小上限 20MB）
- 在线图片 URL 输入生成文案（`/api/upload-by-url`，自动下载+校验）
- 可选输入：产品名称、目标人群、语气风格（拼入 prompt）
- 结果小红书笔记卡片展示 + 一键复制
- 异常处理：格式不支持、大小超限、下载/调用超时、模型失败均有明确提示

**加分项**
- 官网首页 `/`（产品介绍/功能/FAQ/入口），工作台移到 `/workbench`
- 注册/登录/退出（JWT 7 天有效期，密码 PBKDF2 加盐哈希）
- 路由守卫：未登录不能进工作台/历史/管理台；非管理员不能进管理台
- 历史记录 `/history`（按用户，含图片/参数/调优意见/时间）
- 后台管理台 `/admin`（用量统计+7 天柱状图、用户列表、全部记录）
- 多轮调优 `/api/refine`（一次生成 1~3 个版本，记录 parent_id + instruction）
- 流式输出：`/api/stream`（URL/记录）与 `/api/stream-upload`（文件），SSE 逐字显示
- Docker 部署文件（Dockerfile x2、nginx.conf、docker-compose.yml、.dockerignore）

## 4. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite 8 + Vue Router + Axios |
| 后端 | Python 3.14 + FastAPI + Uvicorn + PyMySQL + PyJWT |
| 模型 | 阿里云百炼 DashScope（qwen-vl-plus，兼容 OpenAI 接口做流式） |
| 数据库 | 本地 MySQL 8.0.46（库 xiaohongshu_ai） |
| 部署 | Docker 文件已备（未实装），start.bat 一键启动 |

## 5. 项目结构

```text
xiaohongshu-ai-v0/
├── backend/
│   ├── main.py            # 全部后端代码（约 1000 行，单文件，建议拆分）
│   ├── requirements.txt   # Python 依赖
│   ├── schema.sql         # 建库建表脚本
│   ├── Dockerfile         # 后端镜像
│   ├── uploads/           # 上传图片（运行时生成，已 gitignore）
│   └── .env               # 环境变量（含密钥，已 gitignore，不提交）
├── frontend/
│   ├── vite.config.ts     # dev 代理 /api、/uploads -> 127.0.0.1:8000
│   ├── Dockerfile + nginx.conf  # 前端镜像 + Nginx 同源代理
│   └── src/
│       ├── api.ts         # axios 实例 + streamRequest(fetch SSE)
│       ├── auth.ts        # 登录态（localStorage token/user）
│       ├── router/        # 路由 + 守卫（requiresAuth / requiresAdmin）
│       ├── views/         # Home / Workbench / History / Login / Admin
│       ├── components/    # NavBar / UploadDropzone / NoteCard
│       └── style.css      # 全局设计系统（CSS 变量、组件样式）
├── start.bat              # Windows 一键启动
├── docker-compose.yml     # MySQL + 后端 + 前端编排
├── regression_test.ps1    # 25 项全链路回归脚本
├── HANDOVER.md            # 本文件
└── README.md              # 项目说明（分工待填）
```

## 6. 如何启动 / 停止

**一键启动**：双击 `start.bat`（自动检查 MySQL 服务、启动后端、启动前端、打开浏览器）。

**手动启动**：
```powershell
# 后端
cd C:\Users\admin\Desktop\xiaohongshu-ai-v0\backend
..\venv\Scripts\python.exe main.py        # 监听 127.0.0.1:8000

# 前端（另开终端）
cd C:\Users\admin\Desktop\xiaohongshu-ai-v0\frontend
npm.cmd run dev                           # 监听 localhost:5173（注意不是 127.0.0.1）
```

**停止**：关闭对应的两个终端窗口即可；MySQL 是 Windows 服务（MySQL80），不要随意停。

**注意**：
- PowerShell 里 npm 要用 `npm.cmd`（执行策略禁用了 npm.ps1）
- 前端页面地址：`/` 官网、`/workbench` 工作台、`/history` 历史、`/login` 登录、`/admin` 管理台
- 改后端代码后需重启后端进程（用 `Get-NetTCPConnection -LocalPort 8000` 找 PID，Stop-Process 后重新 `python main.py`）

## 7. 数据库

**初始化**（重置/换机时执行）：
```bash
mysql -uroot -p < backend/schema.sql
```

**users 表**：id、username(unique)、password_hash、role(user/admin)、created_at

**generation_records 表**：id、user_id、parent_id（调优版本父记录）、image_name（文件名或 URL）、image_path（uploads/xxx）、product_name、target_audience、tone_style、instruction（调优意见）、title、body、tags（逗号分隔）、created_at

**注意**：
- 旧数据（早期无登录时期）user_id 为 NULL，不会出现在任何用户的历史里
- 管理员账号：注册接口支持 `admin_code` 字段，与 `.env` 的 `ADMIN_CODE` 匹配则 role=admin
- 本机 MySQL root 密码为 `123456`（仅本地开发）

## 8. API 一览（全部经后端，前端不直连模型/数据库）

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| GET | `/` | 无 | 健康检查 |
| POST | `/api/register` | 无 | 注册（admin_code 选填） |
| POST | `/api/login` | 无 | 登录，返回 JWT |
| POST | `/api/logout` | 无 | 退出（前端清 token 即可） |
| GET | `/api/me` | 登录 | 当前用户 |
| GET | `/api/records` | 登录 | 自己的历史记录 |
| POST | `/upload` | 登录 | 文件上传生成（multipart） |
| POST | `/api/upload-by-url` | 登录 | URL 图片生成 |
| POST | `/api/refine` | 登录 | 调优，versions 1~3 |
| POST | `/api/stream` | 登录 | 流式生成（URL 或 record_id，SSE） |
| POST | `/api/stream-upload` | 登录 | 流式生成（文件，SSE） |
| GET | `/api/admin/stats` | 管理员 | 用量统计 |
| GET | `/api/admin/users` | 管理员 | 用户列表 |
| GET | `/api/admin/records` | 管理员 | 全部记录 |

SSE 事件格式：`data: {"type":"delta","content":"..."}` → 结束 `{"type":"done","id":...,"title":...,"body":...,"tags":[...],"db_saved":...}` 或 `{"type":"error","message":"..."}`。

## 9. 环境变量（backend/.env，已 gitignore）

键名：`ALIYUN_API_KEY`、`DB_HOST`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`、`JWT_SECRET`、`ADMIN_CODE`

- 密钥严禁硬编码/提交；`.env` 已被 `.gitignore` 排除
- 换环境/新机器需要自行创建 `.env`
- Docker 部署时 compose 通过 `env_file: ./backend/.env` 读取，容器内 DB 配置被 `environment` 覆盖为 mysql 容器

## 10. 已知问题与注意事项（重要）

1. **后端是单文件 `main.py`**，`upload / upload-by-url / refine / stream` 之间存在大量重复代码（prompt 构造、API 调用、入库逻辑）。下一步建议拆分为 `routes/`、`db.py`、`services.py` 等模块，动之前先跑 `regression_test.ps1` 保底。
2. **前端请求走同源代理**：`api.ts` baseURL 为空；dev 由 Vite 代理 `/api`、`/uploads` 到 8000，生产由 Nginx 代理。改接口地址时不要改回绝对 URL。
3. **uploads 目录无清理机制**，图片会持续累积，可加定期清理或按用户目录组织。
4. **Docker 未实装验证**：文件齐全，但本机未装 Docker Desktop（WSL2 已具备）。如要做 Docker 加分项，先安装 Docker Desktop 再 `docker compose up -d --build`，注意容器 MySQL 端口映射为 3307 避免与本机 3306 冲突。
5. **访问 GitHub 需要梯子**（用户网络环境），推送失败时先确认代理已开。
6. **阿里云调用会产生费用**（Qwen-VL），每次测试生成/调优/流式都会消耗额度。
7. **PowerShell 5.1 读无 BOM 的 UTF-8 ps1 会乱码**，`regression_test.ps1` 因此全用英文输出；新增 ps1 时注意。
8. **历史遗留文件**：`backend/uploaded_111.jpg`、`selenium_test.py`、`test_env.py` 未提交（untracked），可清理或归档，不影响运行。
9. **README 分工未填**：需要用户提供 3 人姓名+分工后补上。
10. **测试账号**（本地库内）：普通用户 `user161653/123456`，管理员 `admin094040/Admin123456`、`regadmin161051/123456`。演示建议重新注册专用账号。

## 11. 回归测试

```powershell
cd C:\Users\admin\Desktop\xiaohongshu-ai-v0
powershell -NoProfile -ExecutionPolicy Bypass -File .\regression_test.ps1
```

覆盖：基础环境、认证、文件/URL 生成、格式拦截、调优 3 版本、历史、管理台权限（403/401）。当前 25/25 通过。注意脚本会真实调用阿里云生成文案（3 次左右）。

## 12. Git 状态与习惯

- 仓库：`https://github.com/wuyimeng-pro/xiaohongshu-ai-v0`，分支 `main`
- 最近提交（11 次）：初始化 → 忽略缓存 → README/依赖/建表 → 一键启动 → 管理台 → 调优 → 官网 → URL 输入 → Docker → 流式 → 回归脚本
- 提交习惯：按功能单元提交，message 用 `feat:/docs:/chore:/test:` 前缀；完成一块就推送
- 推送：`git add . && git commit -m "..." && git push`
- `.env`、`backend/uploads/`、`node_modules`、`venv`、`dist`、`.vite` 已忽略，不要手动提交

## 13. 下一步优化方向（用户意向：UI 更好看）

**UI/UX（用户明确提出的方向）**
- 引入组件库（Element Plus / Ant Design Vue）统一表单、表格、弹窗
- 笔记卡片更真实：头像/昵称可配置、点赞收藏图标、封面比例（3:4）、卡片动效
- 暗色模式（style.css 已有 CSS 变量基础）
- 历史记录加分页/搜索/按日期筛选；管理台图表美化（可引入 ECharts）
- 骨架屏 loading、页面切换过渡动画、移动端适配优化

**功能增强（可选）**
- 记录删除/收藏、文案导出为图片/文本
- 生成参数（温度/风格模板/模型选择 qwen-vl-max）
- 批量生成（一次传多图）
- 管理台按用户查看明细、每日用量折线图

**工程化（建议优先级中等）**
- 后端拆模块 + DB 连接池（目前每请求新建连接）
- 补 requirements 完整性、FastAPI `/docs` 说明
- 安装 Docker 并实际构建验证 `docker compose up`
- 前端单元测试（Vitest）

## 14. 给新窗口的接手建议

1. 先读本文件，再快速浏览 `README.md`、`backend/main.py`、`frontend/src/views/WorkbenchView.vue`
2. 确认三个服务在跑（5173/8000/3306），浏览器打开 `http://localhost:5173`
3. 有疑问先跑 `regression_test.ps1` 确认基线
4. 改动前后端任何一处后，重启对应服务并回归
5. 完成一块后提交并推送（用户要求：每完成一部分直接上传 GitHub 并告知改了什么）
