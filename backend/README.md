# Backend

## 当前定位

这是围棋教学软件的核心后端骨架，当前只覆盖主体业务：

- 棋局状态
- 规则执行
- KataGo 分析
- AI 应手
- 局部聚焦
- 终局复盘摘要

当前实现上，分析结果和教学说明已经拆分：

- `analysis_snapshots` 保存纯引擎分析结果
- `teaching_notes` 保存教学层输出

## 运行

1. 在 `backend` 目录创建 `.env`
2. 安装依赖
3. 启动服务

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 当前限制

- 使用内存存储，重启后棋局丢失
- 终局复盘仍是估算摘要，不是严格点目器
- 教学解释仍为规则化输出，不是完整自然语言讲解器
