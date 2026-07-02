# H2_Arch — 概念设计引擎

> 一个 AI 驱动的建筑概念设计系统。
> 输入任务书 + 红线图 -> 按 V4 工作流自动生成 3 个方案的功能块体块模型。

---

## 目录结构

```
H2_Arch/
├── README.md                    # 本文件
├── docs-index.md                # 文件导航索引
├── workflow.md                  # 7 步工作流 V4（唯一流程文档）
├── docs/                        # 引擎文档
│   ├── requirements.md          # 功能需求
│   ├── tech-specs.md            # 技术规格
│   ├── design-guidelines.md     # 设计原则
│   ├── execution-steps.md       # 执行步骤
│   └── file-organization.md     # 文件组织规范
├── engine/                      # 全局引擎规则
│   ├── rules.md                 # 类型学诊断、母题库、色码规范
│   └── templates.md             # 各建筑类型生成模板
├── projects/                    # 项目实例
│   ├── 商务酒店_V3/             # 高密商务酒店（塔楼类）
│   └── 山地度假酒店/            # 低密度度假村（分散类）
├── dev-logs/                    # 开发日志
└── _archive/                    # 旧版本工作流
```

## 快速入口

- [工作流 V4](workflow.md) -- 所有项目的执行流程
- [类型学母题定义](engine/rules.md) -- 诊断规则和色码
- [生成模板](engine/templates.md) -- 各建筑类型策略
- [文档索引](docs-index.md) -- 所有文件导航

## 系统架构

| 层级 | 说明 |
|:----|:------|
| **workflow.md** | 7 步流程 |
| **engine/rules.md** | 类型学诊断、母题库、色码 |
| **engine/templates.md** | 分散类/塔楼类生成模板 |
| **projects/** | 配置文件 + 生成脚本 + 报告 |

## 使用流程

1. 准备任务书 + 红线图
2. 创建项目目录结构
3. 按 `workflow.md` 的 7 步执行
4. 所有排布在 Python 完成，不进 Rhino 计算
5. 重叠/退线/面积/高度 四项预检通过后生成脚本
6. Rhino 执行 + 最终 5 项校验

## 安全规则

- 操作限制在当前 `projects/<项目名>/` 目录
- 连续 2 次失败 -> 停止分析
- 新方案在 X 轴偏移 >=30m 生成，不禁删旧体块
