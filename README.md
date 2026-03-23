# Go Teaching BS Platform

一个面向围棋教学的 B/S 架构软件规划项目，核心目标是把「对局」「局部攻防训练」「盘面分析」「教学解释」整合到同一套 Web 系统里。

当前阶段先沉淀规划，不直接进入编码。

## 目标用户

- 围棋初学者：不擅长长变化计算，需要清楚的好坏解释和后续趋势提示。
- 围棋教师或陪练：需要快速构造局部题、切换全盘、查看候选变化。
- 自学用户：希望边下边复盘，而不是只看胜率数字。

## 核心设计判断

- 局部 1/4 棋盘和 1:1 大棋盘不应是两套独立系统，而应是同一盘棋的两种视图和训练模式。
- 棋力分析优先使用专业围棋引擎，例如 KataGo；通用 LLM 不负责算棋，只负责把引擎结果组织成教学语言。
- 第一阶段不建议把系统强依赖在本地 LM Studio 上。更稳的做法是先做「无 LLM 也可用」的解释模板，再把本地或云端 LLM 作为增强层接入。

## 文档

- [产品规划](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\product-plan.md)
- [技术架构](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\architecture.md)
- [KataGo 环境](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\katago-setup.md)
- [后端核心设计](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\backend-core-design.md)
- [API 契约](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\api-contract.md)
- [前端草图](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\frontend-wireframes.md)
- [组件树](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\frontend-component-tree.md)
- [状态树与交互流](C:\Users\18057\Desktop\npu\go-teaching-bs\docs\frontend-state-and-flow.md)
- [前端工程](C:\Users\18057\Desktop\npu\go-teaching-bs\frontend\README.md)

## 推荐实施顺序

1. 先做规则正确、分析稳定的 MVP。
2. 再做局部教学和变化图展示。
3. 最后叠加自然语言教学解释、收官总结和题库化能力。
