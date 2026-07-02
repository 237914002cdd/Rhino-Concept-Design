# AI 建筑概念顾问 - 项目交付模板

## 目录结构

```
AI_Consultant_Project_Template/
│
├── 01_Brief/                      # 输入：原始任务书和红线图
│   ├── project_brief.txt          # 任务书文本（必填）
│   └── site_plan.png              # 用地红线图（可选）
│
├── 02_Intelligence/               # 数据层：面积配平和推理结果
│   ├── area_balance_report.txt    # 面积配平表（自动生成）
│   └── topology_check.txt         # 拓扑自检结果（自动生成）
│
├── 03_Geometry/                   # 几何层：Rhino 模型
│   ├── scheme_A.3dm               # 方案A：围合内院式
│   ├── scheme_B.3dm               # 方案B：线性退台式
│   └── scheme_C.3dm               # 方案C：集中裙房式
│
├── 04_Report/                     # 输出：交付报告
│   ├── area_balance_report.md     # 面积配平报告（格式化）
│   └── code_compliance_report.md  # 规范校验报告（格式化）
│
├── generate.bat                   # 一键生成脚本
└── project_config.json            # 项目配置参数
```

## 使用流程

1. 将任务书内容粘贴到 `01_Brief/project_brief.txt`
2. 修改 `project_config.json` 中的项目参数
3. 双击运行 `generate.bat`
4. 检查 `04_Report/` 下的报告文件
5. 打开 Rhino，启动 MCP 服务，生成体块

## 交付标准

- 面积配平误差：≤±1%
- 规范校验全部通过
- 体块分层/着色/标注完整
