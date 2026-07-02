const docx = require("docx");
const fs = require("fs");

const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, BorderStyle, ShadingType, PageBreak,
  Bookmark, InternalHyperlink,
} = docx;

const FONT = "Microsoft YaHei";
const FONT_SIZE = 21;

function t(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: FONT_SIZE, ...opts });
}
function p(...children) {
  return new Paragraph({ spacing: { after: 120, line: 360 }, children });
}
function empty() {
  return new Paragraph({ spacing: { after: 80 }, children: [] });
}
function bl(...children) {
  return new Paragraph({ bullet: { level: 0 }, spacing: { after: 60, line: 340 }, children });
}
function bp(text) {
  return p(t(text, { bold: true }));
}
function hp(text) {
  return p(t(text, { shading: { type: ShadingType.CLEAR, fill: "FFF3CD" } }));
}

let bid = 1;
function nextId() { return bid++; }

function bookmarkHeading(id, level, text) {
  const size = level === 1 ? 36 : 30;
  const before = level === 1 ? 400 : 240;
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before, after: 200 },
    children: [
      new Bookmark({ id: nextId(), name: id, children: [] }),
      t(text, { bold: true, size }),
    ],
  });
}

function tocEntry(anchorId, text, indent) {
  return new Paragraph({
    spacing: { after: 80, line: 300 },
    indent: indent ? { left: 360 } : undefined,
    children: [
      new InternalHyperlink({
        anchor: anchorId,
        children: [
          new TextRun({
            text: "  " + text,
            font: FONT,
            size: 22,
            color: "0563C1",
            underline: { type: "single" },
          }),
        ],
      }),
    ],
  });
}

function tocItem(anchorId, text, indent) {
  return tocEntry(anchorId, text, indent);
}

function sectionDivider() {
  return new Paragraph({
    spacing: { before: 100, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" } },
    children: [],
  });
}

// ====== CONTENT ======

const cover = [
  new Paragraph({ spacing: { before: 3000 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t("H2 Architecture Design Group", { size: 36, bold: true, color: "1F4E79" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [t("面试 Q&A 升级版 + ComfyUI 学习路径规划", { size: 28, color: "2E75B6" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("方案建筑师（偏AI设计）岗位", { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("候选人：陈政堡", { size: 24, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("2026年6月26日（周五）面试", { size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("版本 V2.0 | 2026.06.24 | 基于实战模拟面试", { size: 20, color: "808080" })] }),
  new Paragraph({ children: [], spacing: { before: 800 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    border: { top: { style: BorderStyle.SINGLE, size: 6, color: "1F4E79" }, bottom: { style: BorderStyle.SINGLE, size: 6, color: "1F4E79" } },
    spacing: { before: 200, after: 200, line: 360 },
    children: [t("本手册在 V1.0 基础上，增补以下内容：", { bold: true })],
  }),
  p(t("① 模拟面试实战 Q&A——洪总实际问出的6个问题 + 你的回答 + 洪总逐题反馈 + 得分")),
  p(t("② 第二版核心追问——你反问工作中AI与设计比例后，洪总的直接回答（70%设计+30%AI）")),
  p(t("③ 两周 ComfyUI 学习路径——每天任务拆解，目标：入职第二周完成工作流演示")),
];

// ====== TOC ======
function buildTOC() {
  return [
    new Paragraph({ spacing: { before: 2000 }, children: [] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [t("目  录", { size: 36, bold: true, color: "1F4E79" })] }),
    sectionDivider(),
    tocItem("ch1", "第一章  模拟面试实战 Q&A"),
    tocItem("ch1-s1", "  1.1  模拟面试概况", true),
    tocItem("ch1-s2", "  1.2  洪总问题复盘与你的回答", true),
    tocItem("ch1-q1", "    Q1: 酒店设计 vs 公建的本质区别", true),
    tocItem("ch1-q2", "    Q2: ComfyUI 经验与 AI 辅助设计", true),
    tocItem("ch1-q3", "    Q3: 两周工作流搭建路径", true),
    tocItem("ch1-q4", "    Q4: 开罗酒店设计气候与文化追问", true),
    tocItem("ch1-q5", "    Q5: AI 与设计的工作比例", true),
    tocItem("ch1-exam", "    终极考题: 大理精品酒店从何开始", true),
    tocItem("ch1-s3", "  1.3  洪总最终评价与你的得分", true),
    tocItem("ch2", "第二章  第二版核心追问"),
    tocItem("ch2-s1", "  2.1  你问的问题 & 2.2 洪总的直接回答", true),
    tocItem("ch3", "第三章  两周 ComfyUI 学习路径"),
    tocItem("ch3-s1", "  3.1  第一阶段: 理解节点逻辑 (Day 1-3)", true),
    tocItem("ch3-s2", "  3.2  第二阶段: 搭建立面工作流 (Day 4-7)", true),
    tocItem("ch3-s3", "  3.3  第三阶段: 进阶与扩展 (Day 8-12)", true),
    tocItem("ch3-s4", "  3.4  第四阶段: 内部培训准备 (Day 13-14)", true),
    tocItem("ch3-s5", "  3.5  面试加分 Checklist", true),
    tocItem("ch4", "第四章  面试 Key Words 速记卡"),
    tocItem("ch5", "第五章  面试携带清单"),
    tocItem("ch6", "第六章  薪资谈判策略"),
    tocItem("ch7", "第七章  英文素材"),
  ];
}

const ch1Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch1", 1, "第一章 模拟面试实战 Q&A"),
  bookmarkHeading("ch1-s1", 2, "1.1 模拟面试概况"),
  p(t("面试角色：H2 Architecture Design Group 创始人 洪宇（Yu Hong）")),
  p(t("面试岗位：方案建筑师（偏AI设计工作流）")),
  p(t("面试日期：2026年6月26日（周五）")),
  p(t("面试时长：模拟约45分钟，涵盖5个核心问题+1个现场考题")),
  empty(),

  bookmarkHeading("ch1-s2", 2, "1.2 洪总实际问出的问题与你的回答复盘"),
  empty(),

  bookmarkHeading("ch1-q1", 2, "Q1：高端酒店设计和普通公建的本质区别？"),
  p(t("【你的回答】")),
  p(t("公建：标准化完成设计到落地，体块变换、平面功能单一、幕墙材质和入口缺乏新意。")),
  p(t("高端酒店：经得起时间检验的设计概念、空间布局功能合理性、立面造型与场地解读，让酒店成为当地地标或目的地。")),
  empty(),
  p(t("【洪总反馈】", { bold: true })),
  p(t("“说得不错。你抓住了核心——高端酒店设计不是在造一栋房子，而是在创造一段体验、一个目的地。”")),
  empty(),
  p(t("【评分】✅ 合格", { bold: true })),
  empty(),
  sectionDivider(),
  empty(),

  bookmarkHeading("ch1-q2", 2, "Q2：用过 ComfyUI 吗？AI 如何辅助设计决策？"),
  p(t("【你的回答】")),
  p(t("坦诚说没用过 ComfyUI，但理解底层逻辑与 Stable Diffusion 相通。目前在用 NanoBananaPro 做白膜快速渲染，AI 后期深化效果图质感。")),
  empty(),
  p(t("【洪总反馈】", { bold: true })),
  p(t("“诚实，是好事。但你这套流程里 AI 是放在末端做美化，不是放在前端做决策。我们需要的是能让 AI 参与方案生成和设计决策的人。”")),
  empty(),
  p(t("【评分】✅ 诚实过关，但需补齐 ComfyUI 实战", { bold: true })),
  empty(),
  sectionDivider(),
  empty(),

  bookmarkHeading("ch1-q3", 2, "Q3：两周时间学会 ComfyUI 并搭建工作流，怎么入手？"),
  p(t("【你的回答】")),
  p(t("尽快上手 ComfyUI，理解所有电池的使用逻辑和组合原理，让公司每个人都能沟通后快速上手；不同设计节点对应不同电池使用方法，在后续项目中迭代优化。")),
  empty(),
  p(t("【洪总反馈】", { bold: true })),
  p(t("“这个回答我很满意。你不是在学一个软件，你是在学一种思维方式。而且你想到要让团队用起来——能做工作流还能教给别人，就能带一个组。”")),
  empty(),
  p(t("【评分】⭐ 全场高分回答", { bold: true })),
  empty(),
  sectionDivider(),
  empty(),

  bookmarkHeading("ch1-q4", 2, "Q4（追问）：开罗五星酒店的场地条件与设计策略？"),
  p(t("【你的回答】")),
  p(t("开罗金字塔景区旅游度假区内，周边旅游酒店密集。外立面横条纹大理石纹理与金字塔千年风化纹理呼应，平面锐角与三角概念统一。")),
  empty(),
  p(t("【洪总反馈】", { bold: true })),
  p(t("“说到了两个关键点。但沙漠气候下的遮阳与通风才是关键挑战。如果横条纹肌理同时承担了自遮阳功能，设计就从好看变成了好用。”")),
  empty(),
  p(t("【评分】✅ 基础扎实，需要补充运营思维", { bold: true })),
  empty(),
  sectionDivider(),
  empty(),

  bookmarkHeading("ch1-q5", 2, "Q5（附加）：工作中 AI 和设计的比例怎么分？"),
  p(t("【你的回答：反问环节】")),
  p(t("问：工作中主要内容是什么？以 AI 工作流搭建为主、设计为辅，还是反过来？")),
  empty(),
  p(t("【洪总回答】", { bold: true })),
  p(t("“设计为主（70%），AI 为器（30%）。AI 工作流搭建好之后，你的角色会从搭建者变成迭代者。”")),
  empty(),
  p(t("【重要启示】", { bold: true })),
  p(t("这个回答揭示了岗位真实定位：先做一个方案建筑师，同时做 AI 工作流的内部教练。")),
  empty(),
  sectionDivider(),
  empty(),

  bookmarkHeading("ch1-exam", 2, "终极现场考题：大理精品酒店怎么开始？"),
  p(t("情景：云南大理苍山脚下精品酒店，50间客房，业主不要网红风。")),
  empty(),
  p(t("【你的回答】")),
  p(t("这个问题本质是商业问题。去网红化的核心是做长久的设计而非流行材料拼凑。第一步通过问卷或调研解读项目需求。")),
  empty(),
  p(t("【洪总反馈】", { bold: true })),
  p(t("“全场最佳回答。你说‘这个问题本质是商业问题’让我确定你不是一个只会画图的设计师。你在我这看到了一个懂商业的建筑师的影子。”")),
  empty(),
  p(t("【评分】⭐ 全场最佳，核心记忆点", { bold: true })),
  empty(),
  sectionDivider(),
  empty(),

  p(t("—— 你的五个得分 ——", { bold: true, size: 24 })),
  p(t("设计判断力：✅ 成熟，有谈判思维")),
  p(t("AI 落地策略：✅ 思路对，执行路径需要补几刀")),
  p(t("专业深度：✅ 诚实有基础，入职后可补")),
  p(t("职业规划：✅ 有野心，需要调整节奏")),
  p(t("现场考题：⭐ 全场最佳——懂商业的建筑师影子")),
  empty(),

  bookmarkHeading("ch1-s3", 2, "1.3 洪总对你的最终评价"),
  p(t("“你最大的优势不是 AI，也不是方案能力，而是你才 27 岁就已经知道设计不是一个造型问题，而是一个决策问题。这个认知很多人混到 35 岁才明白。珍惜它。”")),
  empty(),
  p(t("“欢迎你来 H2 跟我们一起探索这条路。”")),
];

const ch2Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch2", 1, "第二章 第二版核心追问"),
  bookmarkHeading("ch2-s1", 2, "2.1 你问的问题 & 2.2 洪总的直接回答"),
  p(t("你问：工作中主要内容是什么？以 AI 工作流搭建为主、设计为辅，还是反过来？")),
  empty(),
  p(t("洪总回答：", { bold: true })),
  p(t("“设计为主，AI 为器。”", { bold: true, size: 24 })),
  empty(),
  p(t("“我不会招一个专职搞AI但不懂设计的人来H2。核心永远是设计的判断力——什么是好的比例、好的空间体验、好的材料组合。AI 不懂这些，它只是个工具。”")),
  empty(),

  bp("主线（70%时间）：方案设计师"),
  bl(t("参与项目前期概念设计、立面推敲、方案比选、汇报材料")),
  bl(t("跟项目走，从概念到方案深化完整过一遍")),
  bl(t("你之前的酒店项目经验完全用得上")),
  empty(),

  bp("辅线（30%时间）：AI 工作流搭建 + 团队推广"),
  bl(t("定位：内部专家 + 教练")),
  bl(t("先学会 → 搭出可用的工作流 → 教会组里人用")),
  bl(t("大家用起来后，角色从搭建者变成迭代者")),
  empty(),

  p(t("核心价值：懂设计的人来告诉我AI该怎么用在设计上。", { bold: true })),
];

const ch3Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch3", 1, "第三章 两周 ComfyUI 学习路径规划"),

  p(t("目标：从零到入职第二周跑通「草图 → 多方案立面生成 → 团队演示」完整工作流", { bold: true })),
  p(t("总投入：约 14天 x 2-3小时/天 = 28-42小时")),
  p(t("面试加分：完成前5天即可在面试时说“我已经开始搭建并跑通了核心链路”")),
  empty(),

  bookmarkHeading("ch3-s1", 2, "3.1 第一阶段：理解节点逻辑 (Day 1-3)"),
  bp("Day 1：安装与环境搭建 (2小时)"),
  p(t("1. github.com/comfyanonymous/ComfyUI/releases 下载 Windows portable 版")),
  p(t("2. 解压到 D:\\ComfyUI，双击 run_nvidia_gpu.bat 启动")),
  p(t("3. 浏览器访问 http://127.0.0.1:8188，确认界面正常加载")),
  p(t("4. 通过 ComfyUI Manager 安装自定义节点包")),
  p(t("5. 下载基座模型：Realistic Vision V6 或 DreamShaper，放到 models/checkpoints/")),
  empty(),

  bp("Day 2：理解节点式工作流 (2小时)"),
  p(t("1. 核心逻辑：节点=功能模块，连线=数据流动")),
  p(t("2. 最小节点链：Load Checkpoint → CLIP Text Encode → KSampler → VAE Decode → Save Image")),
  p(t("3. 练习调整 Prompt / CFG Scale / 采样步数，观察输出变化")),
  p(t("4. 关键认知：白盒 vs 黑盒——你知道每个环节在做什么")),
  empty(),

  bp("Day 3：ControlNet 核心理解 (2小时)"),
  p(t("1. 下载 Canny / Depth / Lineart 三种 ControlNet 模型，放到 models/controlnet/")),
  p(t("2. 作用：让 AI 严格遵循输入图的轮廓生成立面")),
  p(t("3. 三种模式区别：Canny(轮廓线) / Depth(深度图) / Lineart(线稿)")),
  p(t("4. 调整 strength 0.6-1.0，观察控制力度变化")),
  empty(),

  bookmarkHeading("ch3-s2", 2, "3.2 第二阶段：搭建立面工作流 (Day 4-7)"),
  bp("Day 4：准备建筑输入素材 (1.5小时)"),
  p(t("1. 从 Rhino 导出体块线稿（白底黑线，PNG）")),
  p(t("2. 试验不同出图角度对结果的影响")),
  p(t("3. 也准备灰度体块图（带阴影关系）作为对比输入")),
  empty(),

  bp("Day 5：跑通第一个完整立面工作流 (2小时)"),
  p(t("1. 节点链：Load Image → ControlNet(Canny) → Checkpoint → Prompt → KSampler → VAE Decode → Save Image")),
  p(t("2. 用 Rhino 线稿作为输入，Prompt 示例：modern hotel facade, glass curtain wall, horizontal lines, luxury")),
  p(t("3. 从 10-20 张结果中筛选 2-3 个方向")),
  p(t("4. 保存工作流为 json 格式（可复用）")),
  empty(),
  hp("🎯 Day 5 里程碑：跑通了从 Rhino → ComfyUI → 立面生成的完整链路！"),

  bp("Day 6：迭代与优化 (2小时)"),
  p(t("1. 换 ControlNet 模式：Canny→Depth→Lineart，对比差异")),
  p(t("2. 尝试不同 Prompt 方向：石材 vs 玻璃 vs 金属；现代 vs 新中式 vs 度假风")),
  p(t("3. 调整 KSampler：步数 20-30，CFG 7-8")),
  p(t("4. 调整 ControlNet strength 1.0→0.6，给 AI 更多发挥空间")),
  empty(),

  bp("Day 7：建立工作流模板 (2小时)"),
  p(t("1. 保存验证有效的节点链为可复用模板")),
  p(t("2. 整理 Prompt 词库（按风格分类）")),
  p(t("3. 建立文件命名规范，方便批量管理")),
  p(t("4. 记录对比数据：传统方法 vs AI 方法的效率差距")),
  empty(),

  bookmarkHeading("ch3-s3", 2, "3.3 第三阶段：进阶与扩展 (Day 8-12)"),
  bp("Day 8：LoRA 与风格控制 (2小时)"),
  p(t("1. LoRA = 小型微调模型，控制特定风格或元素")),
  p(t("2. 下载已训练好的建筑风格 LoRA（现代主义/新中式/度假村风格）")),
  p(t("3. 在工作流中加入 LoRA 节点")),
  p(t("4. 思考：训练 H2 品牌 LoRA 需要什么素材？")),
  empty(),

  bp("Day 9：多方案比选工作流 (2小时)"),
  p(t("1. 单输入多输出批量方案生成")),
  p(t("2. 对比模板：左侧原始线稿→中间ControlNet→右侧输出")),
  p(t("3. 理解 seed 值的意义")),
  empty(),

  bp("Day 10：AI→Rhino 回环 (2小时)"),
  p(t("1. AI 选定的立面方向导回 Rhino 验证结构合理性")),
  p(t("2. Rhino 微调比例尺度，重新导出更新线稿")),
  p(t("3. 迭代 2-3 轮，形成闭环")),
  empty(),

  bp("Day 11：材质与氛围迁移 (1.5小时)"),
  p(t("1. 材质替换实验：同一体块换不同材质风格")),
  p(t("2. 环境氛围迁移：日景→黄昏→夜景")),
  p(t("3. IP-Adapter 节点做风格迁移")),
  empty(),

  bp("Day 12：工作流文档化 (2小时)"),
  p(t("1. 操作手册（图文版）含 Troubleshooting")),
  p(t("2. 3 分钟演示脚本")),
  p(t("3. 传统 vs AI 效率对比案例")),
  p(t("4. 预判追问：老员工质疑怎么办？")),
  empty(),

  bookmarkHeading("ch3-s4", 2, "3.4 第四阶段：内部培训准备 (Day 13-14)"),
  bp("Day 13：模拟团队培训 (2小时)"),
  p(t("1. 培训内容结构：为什么(痛点)→是什么(概念)→演示(20分钟)→Q&A")),
  p(t("2. 准备应对话术：被质疑质量/控制力/学习成本时怎么回答")),
  empty(),

  bp("Day 14：收尾与面试应用 (1.5小时)"),
  p(t("1. 确保 ComfyUI 环境可现场演示或录屏展示")),
  p(t("2. 整理成果清单：跑了多少组、筛了多少方向、最佳案例")),
  p(t("3. 面试话术准备：")),
  bl(t("“最近搭建了从 Rhino 到 ComfyUI 再到 Rhino 深化的闭环工作流”")),
  bl(t("“核心是 ControlNet Canny 锁形——让 AI 严格遵循体块轮廓生成立面方向”")),
  bl(t("“概念发散阶段效率提升了 5-10 倍”")),
  empty(),

  bookmarkHeading("ch3-s5", 2, "3.5 面试加分 Checklist"),
  bl(t("☐ ComfyUI 已安装并稳定运行（localhost:8188 打开正常）")),
  bl(t("☐ 至少跑通一组从 Rhino 线稿到 AI 立面的完整工作流")),
  bl(t("☐ 能现场展示 3-5 组 AI 生成立面方向")),
  bl(t("☐ 准备了工作流截图（传统 vs AI 工作流对比）")),
  bl(t("☐ 能用 10 句话讲清 ComfyUI+ControlNet 的建筑设计价值")),
  bl(t("☐ 能提起 LoRA + “以后可以训练 H2 风格 LoRA”")),
  empty(),
  hp("🏆 终极目标：面试时说“我已经跑通了第一版工作流”比任何理论回答都强。"),
];

const ch4Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch4", 1, "第四章 面试 Key Words 速记卡"),
  empty(),
  bp("关键词①：白盒 vs 黑盒"),
  p(t("“ComfyUI 跟 Midjourney 的本质区别是白盒 vs 黑盒。在建筑设计中，我需要精确控制生成的轮廓、比例和风格。”")),
  empty(),
  bp("关键词②：ControlNet 锁形"),
  p(t("“ControlNet 让 AI 严格遵循我的体块轮廓生成立面方向，保证设计意图不丢失。”")),
  empty(),
  bp("关键词③：发散→收敛闭环"),
  p(t("“AI 负责快速发散，设计师负责筛选收敛。”")),
  empty(),
  bp("关键词④：LoRA 微调"),
  p(t("“以后可以训练 H2 自己的风格 LoRA，让 AI 更贴合事务所设计语言。”")),
  empty(),
  bp("关键词⑤：Canny / Depth / Lineart"),
  p(t("“Canny 提取轮廓，Depth 控制空间层次，Lineart 适合细线条稿。”")),
  empty(),
  bp("关键词⑥：CFG Scale + Sampler"),
  p(t("“KSampler 参数组合决定了风格探索的范围和精度。”")),
];

const ch5Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch5", 1, "第五章 面试携带清单"),
  p(t("☐ 笔记本电脑（展示作品集，装了 ComfyUI 可现场演示）")),
  p(t("☐ 打印版简历（3份）")),
  p(t("☐ 笔记本和笔")),
  p(t("☐ 准备反问的问题清单（手写版）")),
  p(t("☐ 手机存好 H2 官网3个代表项目截图")),
  p(t("☐ 浦东民生路118号万科中心，预留30分钟")),
  p(t("☐ Smart Casual 深色系着装")),
];

const ch6Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch6", 1, "第六章 薪资谈判策略"),
  p(t("JD 写 20-25K。厦门到上海生活成本高一截。")),
  empty(),
  bp("推荐策略"),
  p(t("1. 不要主动报价，先让对方出价")),
  p(t("2. 被问期望：“我对平台成长性更看重。根据市场水平期望22-26K。24K以上可以很快到岗。”")),
  p(t("3. 对方给20-22K：“如果试用期后根据表现可调整，我可以接受。”")),
  empty(),
  bp("薪资之外要问的"),
  bl(t("AI 工具预算：GPU 算力 / 软件授权 / 培训资源")),
  bl(t("试用期长度和转正标准")),
  bl(t("出差频率和补贴")),
];

const ch7Content = [
  new Paragraph({ children: [new PageBreak()] }),
  bookmarkHeading("ch7", 1, "第七章 英文素材"),
  bp("3-Minute Self-Introduction"),
  p(t("Hi, I'm Chen Zhenbao. I'm an architect with three years of full-cycle project experience at Synthesis Design+Architecture in Xiamen. I've worked on hospitality projects including a five-star resort in Cairo and the KAFD master plan in Riyadh with Brooks+Scapa and SWA. What brings me here is my interest in AI and architecture. I've been exploring AI-assisted design workflows and am building a ComfyUI-based facade generation pipeline. My goal is to help the studio integrate AI into the early design phase.")),
  empty(),
  bp("Cairo 5-Star Hotel - Key Points"),
  bl(t("Context: A five-star resort in Cairo's pyramid tourist district.")),
  bl(t("Approach: Horizontal stone textures echoing weathered pyramid blocks; triangular geometry from plan to facade.")),
  bl(t("My role: From concept design through facade development, two rounds of iterations.")),
  bl(t("AI angle: With today's tools, I'd use ComfyUI + ControlNet for 10-15 facade options in week one.")),
];

const finale = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { before: 3000 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t("面试不在乎你答得有多完美", { size: 28, bold: true, color: "1F4E79" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [t("在乎你的思考过程是不是一个真正的建筑师的思考过程", { size: 24, color: "2E75B6" })] }),
  empty(),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("诚实 · 有逻辑 · 有自己的判断", { size: 24, bold: true })] }),
  empty(),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [t("洪总最后对你说的话：", { size: 22, italics: true, color: "808080" })] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100, line: 360 },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: "1F4E79" }, bottom: { style: BorderStyle.SINGLE, size: 2, color: "1F4E79" } },
    children: [t("“欢迎你来 H2 跟我们一起探索这条路。”", { size: 24, bold: true, color: "1F4E79" })],
  }),
];

// ====== ASSEMBLE ======
async function main() {
  const doc = new Document({
    title: "H2 Arch 面试Q&A升级版+学习路径规划",
    description: "陈政堡 H2 面试准备手册 V2.0",
    sections: [{
      properties: {
        page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      children: [
        ...cover,
        new Paragraph({ children: [new PageBreak()] }),
        ...buildTOC(),
        ...ch1Content,
        ...ch2Content,
        ...ch3Content,
        ...ch4Content,
        ...ch5Content,
        ...ch6Content,
        ...ch7Content,
        ...finale,
      ],
    }],
  });

  const outPath = "C:/Users/23791/Documents/Codex/2026-06-24/https-www-h2arch-com/outputs/H2_Arch_面试Q&A升级版_学习路径规划_陈政堡.docx";
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outPath, buffer);
  console.log("Done: " + outPath);
}

main().catch(console.error);
