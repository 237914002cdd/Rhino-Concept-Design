# CHANGELOG

## v0.1.0 (2026-07-02)

### 新增
- H2_Arch 概念设计引擎首次纳入仓库索引
- 工作流 V4 正式发布：7 步流程
  - 环境准备 -> 读输入 -> 类型学诊断 -> 面积配平 -> 数学排布 -> 图层色码 -> Rhino 生成+校验
- `engine/rules.md`：类型学诊断树、母题库、色码规范
- `engine/templates.md`：分散类/塔楼类生成模板
- `workflow.md`：完整执行指引，Step ⑤~⑦ 展开说明
- `docs/` 文档体系完整化
  - requirements.md / tech-specs.md / design-guidelines.md
  - execution-steps.md / file-organization.md
  - design-context-v3.md / workflow-v4-protocol.md

### 项目实例
- `projects/商务酒店_V3/`：高密商务酒店概念设计
  - 3 种母题方案（Monolith / Terrace / Interlock）
  - 面积配平 -> 体块生成 -> Excel 报告
  - 目录规范化：_rhino_gen.py + src/ + output/ + _archive/
- `projects/山地度假酒店/`：低密度山地度假村概念设计
  - 3 种布局方案（竖向分层 / 左右分区 / 倒置）
  - 所有体块在退线内，跨方案零重叠
  - 每个方案独立场地红线+退线

### 工具/脚本
- `商务酒店_V3/_rhino_gen.py`：Rhino 体块生成脚本
- `商务酒店_V3/src/gen_rhino_json.py`：JSON 数据生成
- `商务酒店_V3/src/gen_everything.py`：全量生成
- `商务酒店_V3/src/gen_report.py`：Excel 报告生成
- `山地度假酒店/_rhino_gen.py`：Rhino 体块生成
- `山地度假酒店/src/gen_report.py`：Excel 报告生成

### 目录结构规范
```
projects/<项目名>/
├── _rhino_gen.py           # 根目录
├── config.json
├── src/
│   └── gen_*.py
├── output/
│   └── Report.xlsx
└── _archive/
```

### 重要修正
- 数学排布必须在 Python 完成，不进 Rhino 计算（Step ⑤ 前置条件）
- 重叠/退线/面积/高度 四项预检通过后生成脚本
- 禁删旧体块，新方案 X 偏移 >=30m
- 图层规范：R{轮次}/{方案字母}/{功能}
- 三个方案的布局逻辑必须不同，不只偏移不同
