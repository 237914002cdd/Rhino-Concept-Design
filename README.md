# Rhino Concept Design

基于 RhinoMCP 的建筑概念设计自动化工具。输入任务书 + 红线图，自动生成三维体块方案。

## 项目结构

```
MassForge/                        # 核心引擎
├── workflow.md                 # 7 步工作流 V4
├── engine/                     # 规则引擎
│   ├── rules.md                # 类型学诊断、母题库
│   └── templates.md            # 生成模板
└── projects/                   # 项目实例
    ├── 商务酒店_V3/            # 塔楼类（Monolith/Terrace/Interlock）
    └── 山地度假酒店/           # 分散类（度假村/别墅）
```

## 快速开始

1. 准备任务书 + 红线图 PDF
2. 按 `MassForge/workflow.md` 的 7 步执行
3. 所有体块计算在 Python 完成，通过 RhinoMCP 生成

## 技术栈

- Rhino 8 + RhinoMCP
- Python 3.12
- 通过 MCP 协议与 Rhino 通信
