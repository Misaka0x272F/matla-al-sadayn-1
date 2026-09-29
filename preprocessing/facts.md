# 预处理事实（facts.md）

## 源文件

- 文件：`source/matla-al-sadayn-1.pdf`（pdf，3148522 字节）
- sha256：`86a45a75fc832e41…`
- 元数据：title=motalea-saadin-va-majma-bahren-j1；creator=www.Ghaemiyeh.com；date=D:20131113194546+03'30'；producer=www.Ghaemiyeh.com
- 文字层：有，267 页，空文字层比例 0.015
- 书签 TOC：232 条

## 规模

- 单元 4：字符 688922 / 词 131690 / 句 25064（token 粗估 ≈344461）

## 结构清单

| id | region | kind | 标题 | 字符 | 句数 |
|---|---|---|---|---|---|
| ch01 | body | chapter | matla-al-sadayn-1 | 357 | 31 |
| ch02 | body | chapter | فهرست | 11815 | 265 |
| ch03 | body | chapter | مطلع سعدین و مجمع بحرین  | 668453 | 24589 |
| ch04 | body | chapter | درباره مركز تحقيقات رايا | 8297 | 179 |

## 体检

- 无异常

## 可疑信号（语义整备线索）

- 命中单元 4；全书计数：hard_wrap_lines=14664、hyphen_eol=0、duplicate_paras=240、garbled_marks=0、ascii_punct_cjk=0、long_latin_run=0

| id | 硬换行 | 断词 | 重复段 | 乱码 | 中西标点 | 拉丁长串 |
|---|---|---|---|---|---|---|
| ch01 | 12 | 0 | 0 | 0 | 0 | 0 |
| ch02 | 1 | 0 | 1 | 0 | 0 | 0 |
| ch03 | 14595 | 0 | 239 | 0 | 0 | 0 |
| ch04 | 56 | 0 | 0 | 0 | 0 | 0 |

> 信号 = 值得看一眼的线索，不是缺陷判定；按 `references/repair.md` 对照 raw 证据核对修复，并写 `preprocessing/repairs.jsonl` 留痕。

## 媒体

- 文件 4 个

## 环境能力快照（doctor）

- ✓ pandoc
- ✓ pdftotext
- ✓ tesseract
- ✗ ocrmypdf
- ✓ pymupdf
- ✓ rapidocr
- ✓ lxml
- ✓ epubcheck
- ✓ mineru
- multimodal：待 agent 自报（能否看图）
- search：待 agent 自报（是否有网络搜索工具）

## 路由提示（确定性；最终决策见 preprocessing/plan.md）


## agent 待办

- [ ] 元数据核对：对照源文版权页/题录核实 facts 嗅探的 title/creator/publisher/date/rights（嗅探值仅是推断，常错常缺；存疑处询问用户；确认/补全后用 auto-epublizer meta 写回 publication.json；译者署名默认=你的 agent 框架名（如 OpenCode/DouBao），用户指定名优先）
- [ ] 源盘点（可选，目录完整性）：撰写 preprocessing/catalog.csv（列 item,kind,status,locator,unit_id,note），逐项声明源内容去向——included（已收录到某单元）/physical（护封腰封等实体元素，有意不进 EPUB）/excluded（有意排除，note 必填理由）/absent（源件本身不含，如题注所指插图不在源包里；note 必填依据，不阻断放行）/unresolved（未决，qa 阻断放行）
- [ ] 语义整备（信号触发）：体检检出可疑信号（见 facts.md「可疑信号」表；信号是线索非缺陷）——按 references/repair.md 对照 raw 证据核对/修复 structured/，写 preprocessing/repairs.jsonl留痕；OCR/扫描件路径无论有无信号都应做一遍
- [ ] preprocessing/todo.md：把全书处理细化到每个可执行动作的逐项任务清单（覆盖理解/翻译/审校/封装/质检全流程，含每单元翻译项与每 3-5 单元 build 校验项），见 references/preprocessing.md §2.0
- [ ] preprocessing/capabilities.md：自报五维能力边界（multimodal/search/模型/外部 API/工作量），见 references/preprocessing.md §1.1
- [ ] preprocessing/plan.md：结合 capabilities 与 suggestions 写处理方案决策（路由+依据）
- [ ] preprocessing/global.md：主要内容/中心思想/语言风格/叙事结构
- [ ] preprocessing/units/<id>.md：每章梗概/思想/登场人物/术语注意
- [ ] preprocessing/terms.csv：术语预提取（列格式=glossary.csv；翻译前可经 import --terms 导入）
- [ ] preprocessing/risks.md：难段落/多语/文化梗/术语冲突预判
- [ ] preprocessing/report.md：汇总报告（翻译前输入锚点）
