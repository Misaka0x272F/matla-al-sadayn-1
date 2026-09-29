# todo.md —— 逐细节任务清单

> 开工第一件产物。完成一项勾一项（`- [x]`）。与 `status --json` 状态机配合，杜绝「以为做了其实没做」。
>
> **工作流更正（2026-09-29 实测）**：
> 1. **术语命中不限 confirmed**——`Glossary.entries()` 返回全部词条，g0 强制**每一条**。
>    术语表已收敛为 31 条 confirmed「会逐字使用」的词条（自 97 条候选中清洗；歧义的 بیت/نظم/مصرع/کرت/عراق عجم/ذکر 等已删，另去除误报别名）。
> 2. **必须先导出源块再逐块对译**：`python preprocessing/tools/dump_blocks.py <unit_id>`，
>    按编号逐块翻译；译完 `make_align.py <unit_id>` 生成 align（它只校验块数，不校验语义）。
> 3. 译注写在**同一段落块内**（段末换行 + `【译注】…（原文：…）`），不单独成块。

## 0. 预处理理解（facts 之后）
- [x] capabilities.md：自报五维能力边界
- [x] plan.md：方案决策（RTL 路由 + 结构 + 译注约定）
- [x] global.md：全局理解
- [x] units/*.md：逐单元理解（17 份）
- [x] terms.csv：术语预提取 + `import --terms`
- [x] risks.md + report.md
- [x] catalog.csv：源内容去向盘点
- [x] `knowledge export --src-lang fa` 播种：**统一库尚不存在（0 条）**，无同语对术语可播种；
      术语以本工作区 `terms.csv` 为准，定稿后 `knowledge import` 建库回写

## 0.5 语义整备（RTL 修复 + 版式清洗）
- [x] CLI 补 RTL 抽取（`feat/rtl-extraction`，386 tests 全绿、oracle 95.7%）
- [x] `tools/normalize_structured.py`：去 249 数字页眉 / 420 印刷页眉 / 11336 分隔线，拼段、标标题、分离注释
- [x] `tools/verify_structured.py`：7334/7334 行守恒，0 缺失
- [x] `repairs.jsonl` 逐单元留痕；`structure.csv` + `restructure` 登记 17 单元

## 1. 单元翻译
> 每单元：读 `structured/<rel>` → 写 `translation/<rel>` + `translation/align/<id>.jsonl`
> → `import --unit <id>` → `g0 --unit <id>`。高难度段按约定加【译注】。
- [x] cover（封面：书名/作者/编者/版本）
- [x] front-titlepage（书名页）
- [x] front-copyright（版权/著录页：سرشناسه…موضوع…ردهبندی）
- [x] front-preface（编者前言 + 作者生平 + 刊本与抄本述略 + 抄本著录）
- [x] front-dibache（作者序文 دیباچه，骈体最难）
- [x] ch01 717–727（Abu Saʿīd 即位、针对楚潘家族的斗争开端）
- [x] ch02 728–736（楚潘覆亡、帖木儿出生与早年、萨尔巴达尔兴起）
- [x] ch03 737–744（萨尔巴达尔、穆扎法尔家族起家、ملک اشرف）
- [x] ch04 745–753（法尔斯/伊拉克诸雄、克尔曼、ماوراء النهر）
- [x] ch05 754–757（شاه ابو اسحق 覆灭、مبارز الدین محمد）
- [x] ch06 758–763（تغلق تیمور 入河中、帖木儿与侯赛因被囚与脱身）
- [x] ch07 764–766（شاه شجاع/شاه محمود、كرمان、帖木儿—侯赛因对抗）
- [x] ch08 767–768（阿塞拜疆/伊拉克/法尔斯、帖木儿与侯赛因和解）
- [x] ch09 769–770（帖木儿—侯赛因冲突、بلخ）
- [x] ch10 771 及帖木儿即位（含 جلوس 相关纪事）
- [x] back-appendix（حواشی نسخ 异文汇编）
- [x] back-about（数字出版方说明）

## 2. 过程校验（每译 3–5 单元一次）
- [x] `build` 验证格式契约（诗体行 / 注码 / 标题层级 / 图片 ref）
- [x] 解包抽查：目录层级、注释、封面
- [x] 术语命中/注码守恒/表格形状 `g0` 抽检

## 3. 审校（G1–G3）
- [x] 审校登记：`reviews/review-20260929-174343/result.json` 已写（g0 硬缺陷逐单元清零）；
      `{issues,patches,summary}` 未单独成文——本轮为「静态校验 + 主试抽样对读」，非逐条盲审（见 reviews/审查报告-20260929.md 【高】1 与 delivery-20260929.md §6-1）
- [x] 术语冲突外置 `glossary_conflicts.jsonl` 逐条裁决写回 `glossary.csv`
- [x] 裁决后对**全部已译单元**重跑 `g0`
- [ ] 双语版 `build --bilingual` 抽查（重点：译注块与诗段）　←未做；当前仅单语版交付

## 4. 封装与质检（G4–G5）
- [x] `build` 全量 EPUB（`output/matla-al-sadayn-1.epub`）
- [x] `qa`：epubcheck 0 error + 解包审计 pass + 溯源覆盖 ≈1.0
- [x] `import --reviewed` → `status --json` 无 stale
- [x] `knowledge import --workspace .` 回写统一术语库
- [x] `README.md` 交付说明 + 交付审计 + 更新根 `工作计划.md` 批次 3
