# 前端组件树

## 1. 目标

这份组件树只服务 MVP 主工作台，不提前为登录、联机、题库后台做复杂拆分。

目标是三件事：

- 组件职责清楚
- 状态归属稳定
- 后续能直接开始写 Vue 或 React 页面

## 2. 页面层级

```text
App
└─ GameWorkbenchPage
   ├─ TopCommandBar
   ├─ MainWorkspace
   │  ├─ BoardWorkspace
   │  │  ├─ BoardToolbar
   │  │  ├─ GoBoardCanvas
   │  │  ├─ BoardOverlayLayer
   │  │  └─ BoardStatusBadge
   │  └─ AnalysisSidebar
   │     ├─ PositionOverviewCard
   │     ├─ TeachingSummaryCard
   │     ├─ CandidateMovesPanel
   │     └─ AnalysisDetailTabs
   └─ BottomInspector
      ├─ MoveHistoryTab
      ├─ AnalysisHistoryTab
      ├─ TeachingNotesTab
      └─ FinalReviewTab
```

## 3. 组件说明

### App

职责：

- 应用路由壳层
- 主题变量注入
- 全局消息和错误提示入口

当前 MVP 不必放太多业务逻辑。

### GameWorkbenchPage

职责：

- 组装整页布局
- 向子组件分发核心业务状态
- 管理页面级异步动作，例如建局、分析、AI 应手

它是前端主页面容器，但不是所有状态都堆在这里。

## 4. 顶部控制区

### TopCommandBar

子组件建议：

```text
TopCommandBar
├─ NewGameButton
├─ PlayerColorSwitch
├─ AnalyzeButton
├─ AiMoveButton
├─ FocusToggleButton
├─ FinalReviewButton
└─ SessionStatusText
```

职责：

- 提供主操作入口
- 显示当前对局状态

不负责：

- 棋盘渲染
- 分析结果展示

## 5. 棋盘工作区

### BoardWorkspace

职责：

- 承载棋盘相关视觉与交互
- 统一管理全盘 / 局部模式切换

子组件：

```text
BoardWorkspace
├─ BoardToolbar
├─ GoBoardCanvas
├─ BoardOverlayLayer
└─ BoardStatusBadge
```

### BoardToolbar

职责：

- 全盘 / 局部视图切换
- ownership 图层开关
- 推荐点显示开关
- 变化预览开关

### GoBoardCanvas

职责：

- 棋盘底图绘制
- 棋子渲染
- 最后一手标记
- 鼠标落点反馈
- 点击落子

这是核心重组件，后续单独优先开发。

### BoardOverlayLayer

职责：

- 推荐点高亮
- 主变化预览
- 聚焦框选
- ownership 覆盖层

建议不要把这些逻辑直接写进 `GoBoardCanvas`，否则会迅速失控。

### BoardStatusBadge

职责：

- 显示当前行棋方
- 显示当前模式：全盘 / 局部
- 显示最近一次分析状态

## 6. 右侧分析区

### AnalysisSidebar

职责：

- 承载“理解局面”的内容

子组件：

```text
AnalysisSidebar
├─ PositionOverviewCard
├─ TeachingSummaryCard
├─ CandidateMovesPanel
└─ AnalysisDetailTabs
```

### PositionOverviewCard

展示：

- 胜率
- 目差
- 当前分析类型
- 分析时间

### TeachingSummaryCard

展示：

- headline
- key_points
- recommended_direction

数据来源：

- `teaching_note`

### CandidateMovesPanel

展示：

- 前 3 到 5 个候选点
- visits
- 胜率对比
- 点击后高亮对应点和变化

### AnalysisDetailTabs

建议 tab：

- 主变化
- ownership
- 风险提示

其中：

- 主变化 tab 重点服务“看后续”
- ownership tab 服务“看地盘趋势”

## 7. 底部检查区

### BottomInspector

职责：

- 承载历史与复盘内容

子组件：

```text
BottomInspector
├─ MoveHistoryTab
├─ AnalysisHistoryTab
├─ TeachingNotesTab
└─ FinalReviewTab
```

### MoveHistoryTab

展示：

- 着手列表
- 当前着手高亮
- 点击跳转到指定手数

### AnalysisHistoryTab

展示：

- 历史 `analysis_snapshots`
- 区分 `current` / `last_move` / `bot_move`

### TeachingNotesTab

展示：

- 历史 `teaching_notes`
- 与分析快照按手数关联查看

### FinalReviewTab

展示：

- 终局估算结果
- 关键节点总结
- 复盘提示

## 8. 弹层组件

虽然不在主树中，但建议预留：

```text
OverlayComponents
├─ NewGameDialog
├─ FocusRegionDialog
├─ FinalReviewDialog
└─ ToastHost
```

这些组件建议作为页面级子节点，而不是挂在很深的子组件里。

## 9. 组件开发优先级

### P0

- `GameWorkbenchPage`
- `TopCommandBar`
- `GoBoardCanvas`
- `AnalysisSidebar`
- `MoveHistoryTab`

### P1

- `BoardOverlayLayer`
- `AnalysisHistoryTab`
- `TeachingNotesTab`
- `FinalReviewTab`

### P2

- 动画增强
- 更复杂的 ownership 图层
- 更细粒度的局部训练浮层

## 10. 我建议的实现顺序

1. `GameWorkbenchPage`
2. `TopCommandBar`
3. `GoBoardCanvas`
4. `AnalysisSidebar`
5. `BottomInspector`
6. 覆盖层和弹层

这样可以先尽快跑通：

- 建局
- 落子
- 分析
- AI 应手
- 查看历史
