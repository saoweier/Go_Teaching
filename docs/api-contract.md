# API 契约

## 1. 目标

这份契约只覆盖当前 MVP 主链路：

- 创建棋局
- 落子与 AI 应手
- 请求分析与读取历史分析
- 设置局部聚焦区域
- 生成终局复盘摘要

所有接口统一返回 `application/json`。

## 2. 约定

### 坐标

前后端统一使用 0 基坐标：

- `row`: 从上到下，顶部为 `0`
- `col`: 从左到右，左侧为 `0`

例如 19 路棋盘左上角是：

```json
{ "row": 0, "col": 0 }
```

### 棋盘表示

`board.grid` 为二维数组：

- `"."` 空点
- `"B"` 黑子
- `"W"` 白子

### 颜色枚举

- `black`
- `white`

### 着手类型

- `play`
- `pass`
- `resign`

## 3. 核心数据结构

### Point

```json
{
  "row": 15,
  "col": 3
}
```

### FocusRegion

```json
{
  "top": 6,
  "left": 6,
  "height": 9,
  "width": 9
}
```

### CandidateMove

```json
{
  "move": { "row": 3, "col": 15 },
  "move_gtp": "Q16",
  "visits": 320,
  "winrate": 0.54,
  "score_lead": 1.7,
  "prior": 0.16,
  "order": 0,
  "pv": ["Q16", "D4", "C3"]
}
```

### AnalysisSnapshot

只保存分析层结果，不包含教学解释。

```json
{
  "request_type": "current",
  "target_move_number": 12,
  "winrate": 0.54,
  "score_lead": 1.7,
  "ownership_map": [],
  "top_moves": []
}
```

### TeachingNote

只保存教学层输出。

```json
{
  "request_type": "current",
  "target_move_number": 12,
  "summary": {
    "headline": "当前建议优先考虑上方右侧",
    "key_points": [
      "当前局面胜率参考值约为 54.0%",
      "建议先比较前两手变化，不要只看单一胜率数字。"
    ],
    "recommended_direction": "上方右侧"
  }
}
```

### GameSession

前端应将它视为当前对局的主状态对象。

关键字段：

- `id`
- `board_size`
- `user_color`
- `ai_color`
- `status`
- `komi`
- `rules`
- `board`
- `focus_region`
- `move_history`
- `analysis_snapshots`
- `teaching_notes`

## 4. 接口

### 4.1 创建棋局

`POST /api/games`

请求：

```json
{
  "board_size": 19,
  "user_color": "black",
  "komi": 7.5,
  "rules": "tromp-taylor"
}
```

响应：

- 返回完整 `GameSession`

### 4.2 获取棋局

`GET /api/games/{id}`

响应：

- 返回完整 `GameSession`

用途：

- 页面首次进入
- 页面刷新后恢复对局

### 4.3 用户落子

`POST /api/games/{id}/moves`

请求：

```json
{
  "kind": "play",
  "point": { "row": 15, "col": 3 }
}
```

停一手：

```json
{
  "kind": "pass"
}
```

认输：

```json
{
  "kind": "resign"
}
```

响应：

- 返回更新后的 `GameSession`

### 4.4 AI 应手

`POST /api/games/{id}/moves/ai`

请求：

```json
{
  "max_visits": 400,
  "include_ownership": true,
  "include_pv": true
}
```

响应：

- 返回 AI 落子后的 `GameSession`

说明：

- 当前版本 AI 应手默认取 KataGo 第一推荐手

### 4.5 分析当前局面

`POST /api/games/{id}/analysis/current`

请求：

```json
{
  "max_visits": 400,
  "include_ownership": true,
  "include_pv": true
}
```

响应：

```json
{
  "analysis": {},
  "teaching_note": {}
}
```

### 4.6 分析上一手

`POST /api/games/{id}/analysis/last-move`

请求与上相同。

响应：

```json
{
  "analysis": {},
  "teaching_note": {}
}
```

### 4.7 读取历史分析

`GET /api/games/{id}/analysis`

响应：

```json
{
  "analysis_snapshots": [],
  "teaching_notes": []
}
```

用途：

- 页面刷新恢复分析面板
- 复盘模式按历史快照查看分析

### 4.8 设置聚焦区域

`POST /api/games/{id}/focus`

请求：

```json
{
  "top": 6,
  "left": 6,
  "height": 9,
  "width": 9
}
```

响应：

- 返回更新后的 `GameSession`

语义：

- `focus_region` 是 `GameSession` 的一部分
- 会跟随当前对局一起保存
- 只影响前端主观察窗口，不改变分析默认仍以全局盘面为主的原则

### 4.9 读取聚焦区域

`GET /api/games/{id}/focus`

响应：

```json
{
  "focus_region": {
    "top": 6,
    "left": 6,
    "height": 9,
    "width": 9
  }
}
```

### 4.10 终局复盘

`POST /api/games/{id}/final-review`

响应：

```json
{
  "status": "estimated",
  "territory_estimate_black": 72.0,
  "territory_estimate_white": 68.5,
  "capture_count_black": 3,
  "capture_count_white": 1,
  "key_moments": [],
  "teaching_summary": "这是估算式终局总结，适合教学回看，但不替代严格点目和完整死活判定。"
}
```

语义：

- 当前版本把它定义为幂等式重算接口
- 同一局面重复调用，前端应视为刷新当前复盘结果，而不是新建一个历史版本

## 5. 前端状态建议

前端建议拆成四个状态区：

- `gameSession`: 当前对局主状态
- `analysisPanel`: 当前正在展示的分析结果
- `analysisHistory`: 历史分析快照与教学说明
- `uiViewState`: 纯前端临时状态，例如当前 tab、弹窗、悬浮候选手

其中：

- `focus_region` 属于 `gameSession`
- 面板展开收起不属于后端状态

## 6. 错误处理

推荐前端按以下方式处理：

- `400`: 非法落子、超出聚焦区域等用户输入错误
- `404`: 对局不存在
- `503`: KataGo 不可用，前端应提示“分析暂时不可用，可继续对局”
