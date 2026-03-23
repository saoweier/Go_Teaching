# 前端状态树与交互流

## 1. 目标

这份文档回答三个问题：

- 哪些状态属于后端真相源
- 哪些状态只属于前端界面
- 用户操作后，数据和界面如何流动

## 2. 状态树

建议前端状态树如下：

```text
appState
├─ sessionState
│  ├─ gameSession
│  ├─ analysisHistory
│  ├─ teachingHistory
│  └─ finalReview
├─ boardUiState
│  ├─ viewMode
│  ├─ hoveredPoint
│  ├─ selectedPoint
│  ├─ highlightedVariation
│  ├─ ownershipVisible
│  └─ focusDraftRegion
├─ analysisUiState
│  ├─ currentAnalysis
│  ├─ currentTeachingNote
│  ├─ selectedCandidateIndex
│  ├─ activeDetailTab
│  └─ isAnalyzing
├─ commandState
│  ├─ isCreatingGame
│  ├─ isPlayingAiMove
│  ├─ isGeneratingFinalReview
│  └─ lastError
└─ layoutState
   ├─ bottomTab
   ├─ sidebarCollapsed
   └─ isMobileLayout
```

## 3. 状态归属

### sessionState

这是“有业务含义”的状态。

应该来源于后端或由后端结果驱动：

- `gameSession`
- `analysisHistory`
- `teachingHistory`
- `finalReview`

不要把它们只存前端本地，否则刷新后容易丢。

### boardUiState

这是纯棋盘交互状态。

包括：

- 当前是全盘还是局部视图
- 鼠标悬停点
- 当前选中的候选点
- 当前预览哪条变化
- ownership 图层是否展开
- 正在框选但尚未提交的聚焦区域

这些不必写回后端，除了真正确认后的 `focus_region`。

### analysisUiState

这是分析面板的展示状态。

包括：

- 当前正在展示哪一次分析结果
- 当前教学说明
- 当前选中的候选点
- 当前打开的详情 tab
- 当前是否正在发起分析请求

### commandState

这是异步操作状态。

用于控制按钮 loading、禁用态和错误提示。

### layoutState

这是纯布局状态。

例如：

- 底部当前 tab
- 右侧边栏是否折叠
- 当前是否进入移动端布局

## 4. 后端映射关系

### gameSession

来自：

- `POST /api/games`
- `GET /api/games/{id}`
- `POST /api/games/{id}/moves`
- `POST /api/games/{id}/moves/ai`
- `POST /api/games/{id}/focus`

### analysisHistory + teachingHistory

来自：

- `GET /api/games/{id}/analysis`

### currentAnalysis + currentTeachingNote

来自：

- `POST /api/games/{id}/analysis/current`
- `POST /api/games/{id}/analysis/last-move`

### finalReview

来自：

- `POST /api/games/{id}/final-review`

## 5. 核心交互流

### 5.1 新建棋局

```text
点击新对局
-> 打开 NewGameDialog
-> 提交 POST /api/games
-> 写入 sessionState.gameSession
-> 清空 analysisUiState / history / finalReview
-> 棋盘进入初始状态
```

前端要做的重点：

- 清空旧分析
- 清空旧聚焦草稿
- 重置底部 tab 到“着手历史”

### 5.2 用户落子

```text
点击棋盘空点
-> 生成 MoveRequest
-> 提交 POST /api/games/{id}/moves
-> 更新 sessionState.gameSession
-> 清空当前候选点高亮
-> 保留历史分析，但当前分析面板标记为“已过期”
```

这里建议前端做一个明确状态：

- `analysisUiState.currentAnalysisStale = true`

因为落子后旧分析不一定还能代表当前局面。

### 5.3 分析当前局面

```text
点击“分析当前局面”
-> analysisUiState.isAnalyzing = true
-> 提交 POST /api/games/{id}/analysis/current
-> 更新 currentAnalysis
-> 更新 currentTeachingNote
-> 追加/刷新 analysisHistory 与 teachingHistory
-> analysisUiState.isAnalyzing = false
```

界面联动：

- 右侧摘要卡刷新
- 候选点列表刷新
- 底部分析历史增加一条记录

### 5.4 分析上一手

```text
点击“分析上一手”
-> 提交 POST /api/games/{id}/analysis/last-move
-> 更新 currentAnalysis
-> 更新 currentTeachingNote
-> 自动切换底部 tab 到“教学说明”或“分析历史”
```

这个动作更偏教学复盘，不是单纯计算。

### 5.5 AI 应手

```text
点击“AI应手”
-> commandState.isPlayingAiMove = true
-> 提交 POST /api/games/{id}/moves/ai
-> 更新 sessionState.gameSession
-> commandState.isPlayingAiMove = false
-> 当前分析标记为过期
```

建议不要自动再触发一次分析，否则会让用户感觉按钮太重。

如果后面需要自动分析，单独做成设置项。

### 5.6 点击候选点

```text
点击 CandidateMovesPanel 某一项
-> 更新 selectedCandidateIndex
-> 更新 boardUiState.selectedPoint
-> 更新 highlightedVariation
-> 棋盘高亮该点与主变化
-> 右侧细节 tab 切换到“主变化”
```

这是纯前端联动，不需要重新请求后端。

### 5.7 设置局部聚焦

```text
进入聚焦模式
-> 在棋盘拖拽框选
-> 写入 boardUiState.focusDraftRegion
-> 用户确认
-> 提交 POST /api/games/{id}/focus
-> 更新 sessionState.gameSession.focus_region
-> boardUiState.viewMode = focused
```

注意：

- 拖拽中的框选区域是前端临时状态
- 只有确认后才进入后端持久状态

### 5.8 页面刷新恢复

```text
页面加载
-> 读取 gameId
-> 请求 GET /api/games/{id}
-> 请求 GET /api/games/{id}/analysis
-> 恢复 gameSession / analysisHistory / teachingHistory
-> 默认展示最近一次分析
```

这是 `GET /analysis` 存在的核心意义。

### 5.9 终局复盘

```text
点击“终局复盘”
-> commandState.isGeneratingFinalReview = true
-> 提交 POST /api/games/{id}/final-review
-> 更新 finalReview
-> 底部 tab 自动切换到“终局总结”
-> commandState.isGeneratingFinalReview = false
```

## 6. 建议新增的前端派生状态

这些状态不需要后端直接返回，但前端非常值得自己算：

- `isMyTurn`
- `canAnalyze`
- `canPlayAiMove`
- `isAnalysisStale`
- `hasFocusRegion`
- `latestMoveNumber`
- `latestAnalysisMoveNumber`

其中 `isAnalysisStale` 很重要，因为它能明显改善用户对分析结果是否过期的理解。

## 7. 状态管理建议

如果用 Vue，我建议：

- 会话级状态放 `Pinia`
- 页面局部交互状态放页面级 `composables`
- 重绘频繁的棋盘 hover 状态尽量就近管理，不要全塞进全局 store

如果用 React，我建议：

- 会话级状态放 `Zustand` 或 React Query + 局部 store
- 异步请求和缓存交给请求层
- 棋盘 hover / drag 状态留在棋盘组件附近

## 8. 下一步开发顺序

前端正式开工时，建议顺序：

1. 先实现 `sessionState` 的数据接入
2. 再实现 `GoBoardCanvas`
3. 再实现 `AnalysisSidebar`
4. 最后补 `BottomInspector`

原因很简单：

- 没有稳定状态树，棋盘和面板很快会互相污染
- 没有棋盘，其他组件无法验证真实交互
