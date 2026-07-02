# H2_Arch 概念设计工作流 — 技术规格

## 技术栈

| 层 | 选型 | 版本 | 说明 |
|-----|------|------|------|
| CAD 平台 | Rhino | 8.x | 三维体块建模 |
| MCP 协议 | RhinoMCP | 最新 | Rhino ↔ AI 的 MCP 桥接 |
| 运行时 | uvx (Python) | 最新 | RhinoMCP 服务启动器 |
| 面积计算 | Python | 3.12 | 面积配平、校验脚本 |
| 体块生成 | Python (RhinoScript) | — | 通过 RhinoMCP 创建几何体 |
| 测试连接 | Node.js / Python | — | MCP 连接测试脚本 |
| 配置格式 | JSON | — | `project_config.json` 项目配置 |
| 推理协议 | Markdown | — | `.rhino-rules.md` 类型学推理引擎 |

## 系统架构

```
用户输入 (任务书参数)
       │
       ▼
┌─────────────────────────────┐
│     推理层 (Python)          │
│  ┌─────────────────────┐    │
│  │ 面积配平 balance.py │    │  ← 通用配平公式
│  │ + 报告输出          │    │
│  └─────────────────────┘    │
│  ┌─────────────────────┐    │
│  │ 规范校验 validate.py│    │  ← 逐层校验 + 代码合规
│  │ + 组团体块尺寸推导  │    │
│  └─────────────────────┘    │
└───────────┬─────────────────┘
            │ 尺寸参数
            ▼
┌─────────────────────────────┐
│    执行层 (RhinoMCP)         │
│  ┌─────────────────────┐    │
│  │ Rhino 体块生成      │    │  ← 图层/体块/颜色/标注
│  └─────────────────────┘    │
└───────────┬─────────────────┘
            │ 3dm 模型
            ▼
┌─────────────────────────────┐
│     输出层                   │
│  Rhino .3dm + Markdown 报告  │
└─────────────────────────────┘
```

## 核心模块

### 1. 面积配平 (balance.py)
- 通用公式，适用于任何酒店/综合体项目
- 输入：总建筑面积、客房数、各业态层数
- 输出：酒店/办公/裙房标准层面积 + 核心筒面积
- 内部推导：客房面宽进深 → 标准单元 → 单元数 → 总面积

### 2. 规范校验 (validate.py)
- 从 `project_config.json` 读取逐层面积目标
- 支持标准层段展开（如 6F-15F 自动展开）
- 组团体块尺寸计算（面积 → 长宽推导）
- 规范校验：密度/容积率/高度/核心筒/客房面积
- 输出：终端报告 + Markdown 文件

### 3. 类型学推理 (`.rhino-rules.md`)
- 三层推理引擎：类型学诊断 → 母题选择 → 合规校验
- 支持 4 种建筑类型（商务酒店/高端公寓/度假村/办公/综合体）
- 3 种母题（Monolith/Terrace/Interlock）
- 9 条铁律强制约束

### 4. 连接测试 (test_box.py / test_box.js)
- 验证 RhinoMCP 服务是否正常运行
- 测试流程：初始化 → 工具列表 → 创建体块 → 截图

## 数据模型

### project_config.json 核心结构

| 字段 | 类型 | 说明 |
|------|------|------|
| project_name | string | 项目名称 |
| project_type | string | 建筑类型（hotel/apartment/office/commercial） |
| site.site_area_m2 | number | 用地面积 |
| site.max_far | number | 容积率上限 |
| site.max_coverage_ratio | number | 建筑密度上限 |
| floors[] | array | 独立楼层配置（id, name, target_area, height, z_base, function） |
| standard_floors[] | array | 标准层段配置（floors 列表, per_floor 面积） |

### 面积配平输出

| 字段 | 类型 | 说明 |
|------|------|------|
| hotel.per_floor | number | 酒店标准层面积 |
| office.per_floor | number | 办公标准层面积 |
| podium.per_floor | number | 裙房标准层面积 |
| total | number | 计算总面积 |
| target | number | 任务书目标面积 |
| error_pct | number | 误差百分比 |

## 技术决策

| 决策 | 原因 |
|------|------|
| Python 为主要脚本语言 | RhinoScript 原生支持 Python，且 balance/validate 逻辑用 Python 最简洁 |
| JSON 作为配置格式 | 结构清晰、RhinoScript 和 Node.js 都原生支持、易于版本管理 |
| Markdown 作为推理协议 | 人机可读，不需要额外解析器，CLAUDE.md 体系原生兼容 |
| mm 为单位 | Rhino 默认单位，避免转换错误 |
