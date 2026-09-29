# report.md —— 预处理汇总（翻译前输入锚点）

## 一、一句话

15 世纪帖木儿朝史官 Samarqandī 的波斯语编年史《مطلع سعدین و مجمع بحرین》**第一卷**
（回历 717–771 / 公元 1317–1370，伊儿汗衰亡至帖木儿即位），据 1974 年 نوایی 校勘本
数字再版，全量译为中文（含现代编者前言与校勘注），高难度段落附说明与原文。

## 二、方案（详见 `plan.md`）

| 项 | 结论 |
|---|---|
| 路由 | pymupdf 按页切片（有文字层；无需 OCR/MinerU） |
| RTL | CLI 已补 RTL 抽取（`feat/rtl-extraction`），词序 oracle 一致率 95.7% |
| 整备 | `tools/normalize_structured.py` + `verify_structured.py`（7334/7334 行守恒） |
| 结构 | 17 单元（cover / front×4 / ch01–ch10 / back×2），`restructure` 已登记 |
| 翻译 | 全量（正文+诗体+阿拉伯引文+编者层）；纯译文；zh-CN |
| 译注 | 高难度段：译文后【译注】说明 + 波斯语原文（同步入 `align.tgt`） |

## 三、规模

| 项 | 值 |
|---|---|
| 页数 / 图 | 267 页 / 4 图（封面×2、logo、封底） |
| 字符 / 词 | 约 65.3 万字符 / 约 13.2 万波斯语词 |
| 单元 / 段 | 17 单元 / 约 1917 段 |
| 估算批数 | ≈220 批（按 3k 字符/批） |
| 术语 | `terms.csv` 97 条候选（42 person / 29 place / 12 term / 6 org / work…）；经翻译期清洗后 `analysis/glossary.csv` **31 条 confirmed**（g0 强制） |

## 四、结构与内容

| 单元 | 内容 |
|---|---|
| cover / front-titlepage / front-copyright | 封面、书名页、著录页 |
| front-preface | 编者前言、作者生平、刊本与抄本述略 |
| front-dibache | 作者骈体序文（**最难**） |
| ch01–ch10 | 编年正文：717–771 各年，伊儿汗诸汗 → 楚潘/因朱/穆扎法尔/萨尔巴达尔/克尔特/贾拉伊尔 → 帖木儿崛起与即位 |
| back-appendix | حواشی نسخ 异文汇编 |
| back-about | 数字出版方说明 + 封底 |

## 五、风险（详见 `risks.md`）

- **高**：骈体古文（R1）、阿拉伯语引文（R2）、诗体（R3）、RTL 残差 4.3%（R8）、
  正文被编者注释打断（R10）。
- **中**：专名海量异写与同形异人（R5/R7）、回历换算（R4）、注码守恒（R16）。
- 阻断项：**无**。

## 六、术语与知识库

- 播种：`knowledge export --workspace . --src-lang fa`（本机统一库，跨书复用）。
- `preprocessing/terms.csv` 97 条候选 → 翻译期清洗为 `analysis/glossary.csv` 31 条 confirmed。
- 定稿后 `knowledge import --workspace .` 回写。

## 七、下一步

按 `todo.md` §1 逐单元翻译（建议顺序：front-* → ch01…ch10 → back-*），
每单元 `import --unit` + `g0 --unit`，每 3–5 单元 `build` 校验一次。
