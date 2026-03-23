# Go Teaching BS Platform

一个面向围棋教学的 B/S 架构 Web 应用。

它不是单纯的“人机对弈网页”，而是把 `对弈`、`局部聚焦`、`盘面分析`、`候选变化演化`、`教学说明`、`终局复盘` 放在同一个工作台里，目标用户是围棋初学者、陪练场景和教学场景。

## 项目目标

- 让初学者可以边下边学，而不是只看到一个冷冰冰的胜率数字。
- 用专业围棋引擎做盘面计算，用教学层做可读解释。
- 同时支持全盘对弈和局部观察，不把“局部训练”和“完整对局”拆成两套割裂系统。

## 当前已经能做什么

- 用户选择先后手，与 AI 进行完整对局。
- 支持 `陪练 / 教学 / 认真下` 三档 AI 风格。
- 支持自动 AI 应手和自动分析。
- 支持局部聚焦，观察某一块区域的攻防。
- 支持查看候选点，并通过演化图观察未来数手到十几手的变化。
- 教学说明会给出大局方向建议，也会在局部摩擦时提示是否继续应战或考虑脱先。
- 支持认输后自动复盘。
- 支持强制终止对局，并在终止后做估算点目和复盘。
- 支持挂起对局、继续挂起对局。
- 支持查看历史对局记录。
- 已结束的对局可以查看：
  - 棋谱历史
  - 终局复盘
  - 局部亮点
  - 做得不好的地方
  - SGF 棋谱文本

## 核心设计思路

- `KataGo` 负责计算、候选点、盘面趋势和变化图基础数据。
- 前端不是只展示推荐手，而是把变化过程可视化。
- 教学说明层负责把引擎结果转成更适合初学者理解的语言。
- AI 不同档位不是简单调 visits，而是有不同的选点策略和控强度逻辑。

## 当前技术栈

- 前端：`Vue 3` + `TypeScript` + `Pinia` + `Vite`
- 后端：`FastAPI`
- 围棋分析引擎：`KataGo`
- 运行方式：局域网可访问的 B/S 结构

## 目录结构

```text
go-teaching-bs/
  backend/        FastAPI 后端
  frontend/       Vue 前端
  docs/           产品、架构、API、前端设计文档
  config/         KataGo 配置
  scripts/        启动脚本
```

## 快速启动

### 1. 启动后端

在 `backend` 目录：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

在 `frontend` 目录：

```powershell
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

### 3. 访问

- 本机：`http://127.0.0.1:5173`
- 局域网设备：`http://你的局域网IP:5173`

## 适合什么场景

- 围棋启蒙教学
- 低段位陪练
- 教师课堂演示
- 自学用户的局后复盘

## 当前已知限制

- 当前对局存储仍然是内存版，后端重启后会清空内存中的对局。
- 点目和终局总结目前是教学向估算，不是严格比赛级裁判结果。
- 教学说明目前以规则化生成和引擎结果整理为主，还不是完整的 LLM 教练系统。
- 历史对局目前保存在服务运行期内，尚未接数据库持久化。

## 后续方向

- 数据库存档和正式历史棋局管理
- SGF 下载与独立复盘页
- 更强的局部死活教学
- 更细粒度的候选变化对比
- LLM 教学解释增强
- 登录、账号体系、局域网多人等外围能力

## 文档

- `docs/product-plan.md`
- `docs/architecture.md`
- `docs/backend-core-design.md`
- `docs/api-contract.md`
- `docs/frontend-wireframes.md`
- `docs/frontend-component-tree.md`
- `docs/frontend-state-and-flow.md`
- `docs/katago-setup.md`

## 项目定位

这是一个以“教学价值”为中心的围棋软件原型，不追求先把外围功能做全，而是优先把：

- 对弈体验
- 分析能力
- 讲解能力
- 复盘能力

这四件事做扎实。
