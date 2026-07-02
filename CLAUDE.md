# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# 工作区总指引

## 工作区信息

- **根目录**：`d:\claude code mode\files\`
- **用户身份**：完全不懂代码的初学者，边学边做
- **全局 Git**：`user.name=237914002cdd` / `user.email=237914002cdd@gmail.com`
- **Shell**：bash（Git Bash on Windows）

## 核心工作原则

1. **每一步都先向用户用中文说明要做什么，获得确认后再执行**（见 `anti-loop` 规则：假设先行）
2. **每次只做一个小步骤，不一口气做太多**（见 `anti-loop` 规则：两次失败上限 + 反思停顿）
3. **涉及安装、删除、配置变更等操作，必须先说明并确认**（见 `path-governor` 规则：C 盘协议）
4. **所有文件必须放在项目规定的目录下，不散落根目录**（见 `path-governor` 规则：文件归位）
4. **用通俗语言解释每一步的目的，帮助用户学习**
5. **每次代码改动后使用 `/done` 命令自动完成日志更新、Git 提交、CHANGELOG 记录**
6. **新项目使用 `/new` 命令一键创建标准化文件结构**
7. **重复失败两次必须停止，先分析原因再问用户**（见 `anti-loop` 规则：反思停顿）
8. **新建 skill 后自动三同步**：新建或修改 `.claude/skills/` 下的 skill 后，自动同步到 `C:\Users\23791\.claude\skills\`（全局）和桌面端插件目录（`AppData\Local\Claude-3p\...\skills-plugin\...\skills\`），确保 CLI/VS Code/桌面端三端可用

## 项目生命周期规范

### 一、概念期
- 想法记入 Obsidian `Ideas/`，用 `Templates/t-idea.md` 模板
- 只写三句话：做什么、为什么、怎么做
- status 标 `概念期`，成熟后改为 `已立项` 并链到 Projects/ 笔记

### 二、立项期
- 从 `.claude/templates/` 复制文档模板到 `files/项目名/docs/`
- 初始化 Git 仓库
- 从模板创建 `docs/branch-strategy.md`，创建 `main` 和 `dev` 分支
- 复制 `.gitignore` 模板到项目根目录
- 从模板创建 `docs/file-organization.md`，确定项目目录结构
- 填写 `requirements.md` 和 `tech-specs.md`
- 在 Obsidian `Projects/` 下用 `t-project.md` 模板创建项目主笔记，写立项动机和预期目标
- 更新 Obsidian `项目总览.md`，加入新项目

### 三、开发期
- 按 `execution-steps.md` 逐阶段推进
- 每个功能拉 `feat/` 分支开发，完成后合并回 `dev`，提交格式：`类型: 描述`
- 每天更新 `dev-logs/YYYY-MM-DD.md`
- 常用的重复操作用 Skill 封装
- 重要决策、踩坑经验及时追加到 Obsidian 项目主笔记的"关键决策日志"和"踩坑记录"

### 四、完成期
- 按 `docs/release-process.md` 走发布流程：检查清单 → 合并 main → 更新 CHANGELOG → 打 tag
- 更新 README：完成状态 + 经验总结
- Obsidian：运行 `/archive` 自动完成归档

## 项目文档模板

所有项目必须包含以下文档（从 `.claude/templates/` 复制）：

| 文件 | 用途 |
|------|------|
| `docs/requirements.md` | 功能需求、用户场景、业务规则 |
| `docs/tech-specs.md` | 技术栈、数据模型、架构设计 |
| `docs/design-guidelines.md` | UI/UX 设计原则、配色、布局 |
| `docs/execution-steps.md` | 分阶段开发计划 + 任务清单 |
| `docs/branch-strategy.md` | 分支命名、工作流程、合并规则 |
| `docs/file-organization.md` | 目录结构、自写 vs 外部资源、大文件处理 |
| `.gitignore` | 不提交到 Git 的文件规则 |
| `docs/release-process.md` | 版本号规则、发布检查清单、Tag 规范 |
| `dev-logs/YYYY-MM-DD.md` | 每日开发日志 |

## 当前项目

> 项目状态详情见 Obsidian `Projects/` 笔记。

| 项目 | 位置 | 状态 | 说明 |
|------|------|------|------|
| Aftermath | `aftermath/` | 开发中 | PWA 跨平台应用，React+TS+Vite |
| clawd-on-desk | `clawd-on-desk/` | 开发中 | 桌面应用（补文档中） |
| autovoice | `D:\claude-code-mode\autovoice\` | 运行中 | AutoHotkey 语音输入工具 |
| claude-pet | `claude-pet/` | 孵化中 | Electron 桌面宠物（像素螃蟹） |
| H2_Arch | `H2_Arch/` | 开发中 | RhinoMCP 概念设计工作流（商务酒店案例） |

## 常用路径

| 资源 | 路径 |
|------|------|
| 项目模板 | `.claude/templates/` |
| 自定义 Skill | `.claude/skills/` — `/new`（初始化项目）、`/done`（完成改动提交）、`/archive`（项目归档）、`path-governor`（路径权限）、`anti-loop`（防循环） |
| Obsidian Vault | `D:\obsidian tools\Vault\My Note\` — `Ideas/`（想法）、`Projects/`（项目笔记）、`Archive/`（归档）、`Templates/`（模板） |
| Obsidian 项目总览 | `D:\obsidian tools\Vault\My Note\项目总览.md` |
| Memory 系统 | `C:\Users\23791\.claude\projects\d--claude-code-mode-files\memory\` |
| settings.json | `C:\Users\23791\.claude\settings.json` |
