# MassForge — 文件组织规范

## 目录结构

```
MassForge/
│
├── 1_面试准备/                        # 面试模拟文档（4份 DOCX）
│   ├── MassForge_面试完全准备手册_陈政堡.docx
│   ├── MassForge_面试Q&A升级版_学习路径规划_陈政堡.docx
│   ├── ComfyUI_建筑立面工作流_速通手册.docx
│   └── AIx建筑概念设计助手_可行性产品方案.docx
│
├── 2_生成脚本/                        # 文档生成工具
│   ├── gen_doc_v3.js                  V2.0 文档的 Node.js/docx 生成脚本
│   └── V2.0_面试内容全文.txt          V2.0 文档内容提取
│
├── 3_概念设计工作流/                   # RhinoMCP 概念设计工作流核心文件
│   ├── .rhino-rules.md                建筑类型学推理与几何生成协议 V2.0
│   ├── balance.py                     通用面积配平公式
│   ├── validate.py                    方案设计自动校验与报告生成器
│   ├── workflow-summary.md            概念设计 AI 工作流完整流程
│   ├── .mcp.json                      RhinoMCP MCP 服务器配置
│   ├── test_box.py                    RhinoMCP 连接测试（Python 版）
│   ├── test_box.js                    RhinoMCP 连接测试（Node.js 版）
│   └── 项目模板/
│       └── AI_Consultant_Project_Template/  项目交付模板
│           ├── README.md
│           ├── project_config.json
│           ├── generate.bat
│           ├── 01_Brief/              # 输入：任务书
│           │   └── P2_Project_Brief_Analysis_and_Adjacency_Matrix.md
│           ├── 04_Report/             # 输出：报告
│           │   └── area_balance_report.md
│           └── ...（其他模板目录）
│
├── docs/                               # 项目文档（本规范）
│   ├── requirements.md                产品需求
│   ├── tech-specs.md                  技术规格
│   ├── design-guidelines.md           设计规范（类型学/配色/图层）
│   ├── execution-steps.md             分阶段执行计划
│   └── file-organization.md           本文件
│
├── dev-logs/                           # 开发日志
│   └── 2026-07-01.md                  今日日志
│
└── README.md                           # 项目总览
```

## 目录说明

| 目录/文件 | 用途 | 备注 |
|-----------|------|------|
| `1_面试准备/` | 面试模拟练习输出的 DOCX 文档 | 4 份面试相关文档 |
| `2_生成脚本/` | 生成面试文档的脚本 | gen_doc_v3.js + 文本提取 |
| `3_概念设计工作流/` | 核心工作流代码 + 协议 + 模板 | 持续发展的部分 |
| `docs/` | 项目文档 | 标准 5 件套 |
| `dev-logs/` | 每日开发日志 | 按日期命名 |
| `README.md` | 项目总览 | 含目录结构和状态说明 |

## 核心工作流文件归属

| 文件 | 属于 | 说明 |
|------|------|------|
| `.rhino-rules.md` | 3_概念设计工作流 | 类型学推理协议（隐藏文件，Rhino 规则） |
| `balance.py` | 3_概念设计工作流 | 面积配平计算 |
| `validate.py` | 3_概念设计工作流 | 规范校验 |
| `test_box.py` | 3_概念设计工作流 | RhinoMCP 连接测试 |
| `test_box.js` | 3_概念设计工作流 | RhinoMCP 连接测试（备用） |
| `project_config.json` | 3_概念设计工作流/项目模板 | 项目配置参数 |
| `.mcp.json` | 3_概念设计工作流 | MCP 服务器配置 |

## 自写 vs 外部资源

### 手写文件（提交到 Git）
- `3_概念设计工作流/` 下所有 Python/JS/Markdown/JSON 文件
- `docs/` 和 `dev-logs/` 所有文档
- `README.md`

### 外部资源（大文件，不提交到 Git）
- `1_面试准备/` 下 DOCX 文件（单个 > 10MB 的考虑 Git LFS）
- 从网络下载的素材
