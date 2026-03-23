# 后端核心设计

## 1. 当前范围

当前阶段只做围棋教学软件的主体业务，不把下列能力纳入一阶段实现：

- 登录、鉴权、权限系统
- 局域网联机、匹配、聊天室
- 支付、课程、运营后台
- 用户画像和长期数据分析

这些能力后续只保留扩展接口，不进入当前核心链路。

## 2. 当前必须稳定的业务主链路

后端第一阶段只围绕这五个能力构建：

1. 棋局状态管理
2. 落子合法性与规则执行
3. KataGo 盘面分析和 AI 应手
4. 局部聚焦视图
5. 终局复盘与教学摘要

## 3. 模块边界

### Game Domain

负责：

- 棋盘状态
- 行棋方
- 提子、禁入点、简单劫
- 停一手、认输、终局状态
- 局部聚焦区域

这是系统的真相源，不能让 KataGo 或前端直接篡改棋局状态。

### Analysis Domain

负责：

- 将当前棋局转成 KataGo 可识别的分析请求
- 获取候选点、变化图、胜率、目差、ownership
- 生成 AI 推荐手或 AI 应手
- 产出纯分析快照，不负责教学文本归档

### Teaching Domain

负责：

- 把分析结果转成教学标签
- 产出当前局面摘要
- 产出终局总结结构

第一阶段只做规则化输出，不做自由生成式解释。

这里特别约束一条：

- `AnalysisSnapshot` 只保存分析层结果
- `TeachingNote` 单独保存教学层输出

这样可以避免后续把教学解释误写进分析层，导致职责混乱。

## 4. 数据模型

### GameSession

- `id`
- `board_size`
- `user_color`
- `ai_color`
- `to_play`
- `status`
- `komi`
- `rules`
- `focus_region`
- `board`
- `move_history`
- `analysis_snapshots`
- `teaching_notes`

### MoveRecord

- `move_number`
- `color`
- `kind`
- `point`
- `captured_points`
- `board_hash`
- `created_at`

### AnalysisSnapshot

- `request_type`
- `target_move_number`
- `top_moves`
- `winrate`
- `score_lead`
- `ownership_map`
- `principal_variations`

### TeachingNote

- `request_type`
- `target_move_number`
- `summary`
- `created_at`

## 5. API 边界

### 棋局

- `POST /api/games`
- `GET /api/games/{id}`
- `POST /api/games/{id}/moves`
- `POST /api/games/{id}/moves/ai`

### 分析

- `POST /api/games/{id}/analysis/current`
- `POST /api/games/{id}/analysis/last-move`
- `GET /api/games/{id}/analysis`
  - 读取已有分析快照和教学说明，供页面刷新或重新进入对局时恢复上下文。

### 局部聚焦

- `POST /api/games/{id}/focus`
- `GET /api/games/{id}/focus`

`focus_region` 的语义在当前版本定义为：

- 它是 `GameSession` 的一部分，不是纯前端临时状态
- 用户设置后会跟随当前对局保存
- 后续落子和分析默认仍基于全局盘面，只是前端以该区域作为主要观察窗口

也就是说，`/focus` 端点只是 `GameSession.focus_region` 的专用读写入口，而不是另一套独立状态。

### 终局复盘

- `POST /api/games/{id}/final-review`

当前版本对 `final-review` 的行为定义为：

- `POST` 是幂等式重算接口
- 如果同一局面重复触发，语义上应返回该时刻重新计算后的结果，而不是制造新的业务分支
- 一阶段先不做“多版本终局复盘历史”管理，等复盘工作流稳定后再决定是否引入 `review_snapshots`

## 6. 为什么这样拆

这样拆的核心好处不是“看起来分层漂亮”，而是为了避免后期三类重构：

- 不会因为接入第二种围棋引擎而重写业务层
- 不会因为把模板解释升级到 LLM 而改动规则层
- 不会因为加入用户系统而破坏当前单机教学流程

## 7. 当前实现策略

当前后端采用：

- `FastAPI` 作为 API 层
- 内存存储作为第一阶段会话存储
- 纯 Python 规则引擎管理棋局
- `KataGo JSON analysis engine` 作为专业分析后端

KataGo 进程模型在这里明确为：

- 使用单一持久分析进程运行
- 后端通过进程间通信复用该进程
- 不允许每次分析请求都重新启动一个 KataGo 实例

原因很直接：重复拉起引擎会让模型加载和 GPU 初始化成本压垮交互延迟。

这意味着当前版本重点是：

- 接口正确
- 分层稳定
- 能跑通主业务链路

而不是一开始就追求数据库、消息队列、分布式部署。
