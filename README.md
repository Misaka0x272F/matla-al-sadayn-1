# matla-al-sadayn-1 —— 《مطلع سعدین و مجمع بحرین》第一卷（波斯语）

## 源

| 项 | 值 |
|---|---|
| 交付原名 | `阿卜杜·拉扎卡·撒马尔罕迪《两颗星座升起与两海汇合之时》第一卷 波斯语.pdf` |
| 工作区源件 | `source/matla-al-sadayn-1.pdf` |
| sha256 | `86a45a75fc832e41e3da18074ab6100f9fcac0acaf5388fb683d3a19d9907f92` |
| 送审副本 | `sources/matla-al-sadayn-1.pdf`（同 sha256；收件箱原件保留至交付后按 sha256 移除） |
| 原始书目 | 书名 **مطلع سعدین و مجمع بحرین（جلد اول）**；作者 کمال الدین عبد الرزاق سمرقندی（1413–1482）；به اهتمام عبد الحسین نوایی；ناشر پژوهشگاه علوم انسانی و مطالعات فرهنگی（چاپ اول 1353/1974，ISBN 964-426-042-23100）；数字版 مرکز تحقیقات رایانه‌ای قائمیه اصفهان（2013） |
| 覆盖年代 | 回历 717–771（公元 1317–1370） |

## 交付状态（2026-09-29 完成）

**全书翻译完成并通过质检放行**：17/17 单元 `built`，`qa` 判定 **G5 放行：是**。

| 项 | 值 |
|---|---|
| 成品 | `output/matla-al-sadayn-1.epub`（约 405 KB） |
| 单元 | 17 个全部 `built`（cover + front×4 + ch01–ch10 + back×2） |
| 质检 | G4 审计 pass；epubcheck errors 0 / warnings 0；术语命中 0；结构违例 0；术语冲突 0；provenance 覆盖率 1.0 |
| 对照表 | `translation/align/*.jsonl`（段级，与译文 md 一致） |
| 审校记录 | `reviews/review-<ts>/result.json`（逐单元 g0 硬缺陷 0） |

本轮完成的工作：
- **ch01（318 块）**、**ch02（394 块）**、**ch03（327 块）** 全文首译（此前未译）。
- **ch04（350 块）** 译文与源文页断残片错位，用 DP（术语命中+数字+块类型）重建 1:1，并为保对齐把 37 处页断残片并入相邻源块（源文仅少空行，文本不损）。
- ch02 13 条、ch03 11 条术语命中逐条清零（`preprocessing/tools/fix_ch02.py`、`fix_ch03.py`）。
- 修正标题跳级（h1→h3）与 `**` 标记残留；补齐 cover 译文。
- **交付后修复（2026-09-29，CLI commit `5488397`）**：注文编号保真——校异/脚注 `N)` 原先被
  `<ol>` 自动编号整体改写（全书 1013 处全部显示为 1）；修复后按原编号输出（`p.fnlist`），
  重建 EPUB 并 `qa` 复查（G5 放行、epubcheck 0 error）。
- 可复现工具：`tools/assemble_ch01..ch03.py`、`rebuild_ch04_align.py`、`fix_ch02/03.py`。

质量说明：ch01–ch03 为忠实意译，事件/世系/年表/脚注（校勘异文与出处）完整保留；
诗句为押韵或直译+括注；advisory 的长度比告警集中于脚注残句与诗句块（原文断片特性）。

## 当前状态（2026-09-29）

**预处理完成**：`preprocessing_complete=true`、`stale=[]`、`catalog` 11 项（included_bound）。

- 结构：17 单元（cover / front×4 / ch01–ch10 / back×2），`restructure` 已登记。
- 整备：`tools/normalize_structured.py`（去 249 数字页眉 / 420 印刷页眉 / 11336 分隔线；
  标题 142、编者注释 1012、拼段 1917）+ `tools/verify_structured.py`（7334/7334 行守恒 0 缺失）。
- 理解层：`preprocessing/{capabilities,plan,global,todo,units/*,terms.csv,risks,report,catalog}.md`。
- 术语：`analysis/glossary.csv` 现为 **31 条 confirmed**（g0 强制逐条命中；`import --terms` 后经翻译期清洗，删去歧义词并剔除误报别名）。
  `preprocessing/terms.csv` 另有 97 条候选/seed（其中 70 条未纳入强制表，仅作参考）。
- 元数据：`meta` 已写回 title/creator/translator(CodeBuddy)/publisher/date/rights。

## 关键技术说明

- **RTL 抽取**：本机 CLI 已补 RTL 支持（`auto-epublizer` 分支 `feat/rtl-extraction`，
  commit `693e175` + `d3a15f7`；`src/auto_epublizer/ingest/rtl.py`）。
  PyMuPDF 原生对 RTL 输出词序颠倒，修复后与 `pdftotext` oracle 词序一致率 **95.7%**；
  386 tests 全绿，LTR 零回归。校验脚本 `auto-epublizer/scripts/verify_rtl_pdf.py`。
- **编者注释**：1974 校勘本的现代编辑层（异文 ك/س/ع/ف + 书名页眉引用）内联在正文流中，
  本工作区**保留原位、随文翻译**（用户决定全量译），不拆分。
- **译注约定**：高难度段落译文后加【译注】（说明 + 波斯语原文），同步写入 `align.tgt`。

## 交付后精修：被分页/注释打断段落的合并（2026-09-29）

- 证据：`preprocessing/tools/trace_breaks.py` → `breaks.jsonl`（12005 条被删版式标记）、`fragments.csv`（候选边界）。
- 逐条语义裁定（`merge_plan.jsonl` + `merge_plan_round2.jsonl`），共**合并 19 处**真断句（源译成对并块，只并块不改字）；正文块 2551 → **2532**。
- 校验：文本守恒通过；`g0` 硬缺陷 0（advisory 404→397）；`qa released=true`、epubcheck 0 error/0 warning、`align_md_drift=0`、`epub_coverage=1.0`。
- 记录：`reviews/交付后精修-20260929.md`；`preprocessing/repairs.jsonl` 追加 9 条 `line_join`。
- 遗留：源块「混装多类内容」的配对粒度问题（非交付缺陷）、跨单元残片 9 处、ch10 页眉残留——见精修记录 §5。

## 待办 / 下一步

- 翻译：按 `preprocessing/todo.md` §1 逐单元进行（17 单元，估 ≈220 批）。
- 定稿后 `knowledge import` 回写统一术语库；`build`/`qa` 后写交付记录。

## 溯源

- `publication.json.meta.source_sha256` 绑定源件身份；`events.jsonl` 为行为账本。
- 整备留痕：`preprocessing/repairs.jsonl`；结构清单：`preprocessing/structure.csv`。
- 权属：仅原著正文（作者卒于 1482 年）属公有领域；1974/1993–96 校勘本的**编辑层、版式、2013 年数字再版层、封面图及 back-about 第三方引文均未进入公有领域**，本译本仅作内部学习研究副本，不公开分发。逐项审查见 `reviews/版权审查-20260929.md`。
