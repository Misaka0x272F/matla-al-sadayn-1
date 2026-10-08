#!/usr/bin/env python3
"""从 structured/raw/page-*.json 重建本书 structured/（确定性，零 token）。

背景（详见 preprocessing/plan.md）：本 PDF 有文字层，但每页混入三类版式噪声，
且数字版把每张印刷页的**书名页眉**内联进了正文流：

1. 数字版页眉：每页顶部 y<35 的一行 ``صفحه X از 267`` + 书名 + Ghaemiyeh 网址；
2. 分隔线块：整块只有 ``_``（印刷页的脚注分隔线）；
3. 印刷版书名页眉：内联在正文中，形如 ``مطلع سعدین و مجمع بحرین 1ج، ص، 86:``
   —— 数字版每页约压 2 张印刷页，故此类行约每半页出现一次。

本工具只做**确定性搬运**（读 raw 证据 → 机械清洗 → 落 md），不做语义判断：
段落边界按「块末标点 / 标题 / 注释 / 诗体标签」机械断开；注释（``N) …``）
不拆分、保持在原位（保留全部内容）。判断留痕写 ``preprocessing/repairs.jsonl``。

用法::

    python preprocessing/tools/normalize_structured.py [--dry-run]
    python preprocessing/tools/normalize_structured.py --out /tmp/sb   # 沙箱验证 diff
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
RAW = WS / "structured" / "raw"
STRUCT = WS / "structured"

TITLE_FA = "مطلع سعدین و مجمع بحرین"

# 单元划分（印刷页/PDF 页号，含端点）。前 3 页为封面图；p5–14 为目录（由 EPUB 目录生成，
# 不收录，见 preprocessing/catalog.csv）；p267 为封底图。
UNIT_MAP: list[dict] = [
    {"id": "cover", "region": "cover", "kind": "cover", "title": TITLE_FA, "level": 1, "pages": [1, 2]},
    {"id": "front-titlepage", "region": "frontmatter", "kind": "titlepage",
     "title": "صفحه عنوان", "level": 1, "pages": [4, 4]},
    {"id": "front-copyright", "region": "frontmatter", "kind": "copyright",
     "title": "مشخصات کتاب", "level": 1, "pages": [15, 15]},
    {"id": "front-preface", "region": "frontmatter", "kind": "preface",
     "title": "مقدمه و شرح حال مؤلف", "level": 1, "pages": [16, 32]},
    {"id": "front-dibache", "region": "frontmatter", "kind": "preface",
     "title": "دیباچه", "level": 1, "pages": [33, 40]},
    {"id": "ch01", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 717–727 هجری", "level": 1, "pages": [41, 72]},
    {"id": "ch02", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 728–736 هجری", "level": 1, "pages": [73, 105]},
    {"id": "ch03", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 737–744 هجری", "level": 1, "pages": [106, 140]},
    {"id": "ch04", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 745–753 هجری", "level": 1, "pages": [141, 171]},
    {"id": "ch05", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 754–757 هجری", "level": 1, "pages": [172, 187]},
    {"id": "ch06", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 758–763 هجری", "level": 1, "pages": [188, 212]},
    {"id": "ch07", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 764–766 هجری", "level": 1, "pages": [213, 233]},
    {"id": "ch08", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 767–768 هجری", "level": 1, "pages": [234, 242]},
    {"id": "ch09", "region": "body", "kind": "chapter",
     "title": "وقایع سال‌های 769–770 هجری", "level": 1, "pages": [243, 253]},
    {"id": "ch10", "region": "body", "kind": "chapter",
     "title": "وقایع سال 771 هجری و جلوس امیر تیمور", "level": 1, "pages": [254, 261]},
    {"id": "back-appendix", "region": "backmatter", "kind": "appendix",
     "title": "حواشی نسخ", "level": 1, "pages": [262, 263]},
    {"id": "back-about", "region": "backmatter", "kind": "afterword",
     "title": "درباره مرکز تحقیقات رایانه‌ای قائمیه اصفهان", "level": 1, "pages": [264, 267]},
]

# 标题关键词 → markdown 级别（## = 年/篇级；### = 条级）
_H2_KW = ("وقایع", "قسم", "داستان", "فصل", "باب", "دیباچه", "مقدمه", "باعث",
          "طلوع", "شرح حال", "کیفیت", "مشخصات", "نسخه", "حواشی")
_H3_KW = ("ذکر", "حکایت", "اشاره", "احوال", "بقایای", "صورت", "متناسب", "سبب")
_VERSE_LABELS = {"نظم", "بیت", "مصرع"}

# 形似标题实为编者校记/异文的短语（避免误升为 EPUB 目录项）
_HEADING_BAD = ("اشتباه", "جزء", "چاپ", "حاشیه", "متن", "ظاهرا", "نمایند", "سطر")

_FOOTNOTE_RE = re.compile(r"^\d+\s*\)")
_DIGIT_RE = re.compile(r"\d")


def _load_page(pno: int) -> dict:
    return json.loads((RAW / f"page-{pno:03d}.json").read_text(encoding="utf-8"))


def _is_digital_header(block: dict) -> bool:
    bb = block.get("bbox") or [0, 0, 0, 0]
    text = block.get("text") or ""
    if bb[1] >= 35:
        return False
    return "Ghaemiyeh" in text or "صفحه" in text or "مرکز تحقیقات" in text


def _is_separator(line: str) -> bool:
    s = line.strip()
    return bool(s) and set(s) <= {"_"}


def _is_print_header(line: str) -> bool:
    """印刷版内联书名页眉：含书名 + ``ص`` + 数字（如 ``… 1ج، ص، 86:``）。"""
    return TITLE_FA in line and "ص" in line and bool(_DIGIT_RE.search(line)) and len(line) <= 80


def _is_footnote(line: str) -> bool:
    return bool(_FOOTNOTE_RE.match(line.strip()))


def _classify(line: str) -> str | None:
    """返回 ``h2``/``h3``/``verse``/``note``/``body``。"""
    s = line.strip()
    if not s:
        return None
    if s in _VERSE_LABELS:
        return "verse"
    if _is_footnote(s):
        return "note"
    if len(s) <= 55 and not any(b in s for b in _HEADING_BAD):
        for kw in _H2_KW:
            if s.startswith(kw):
                return "h2"
        for kw in _H3_KW:
            if s.startswith(kw):
                return "h3"
    return "body"


# ── 年份标题与条目标题粘连的修复（2026-10-08）────────────────────────────
# 数字版把「年份标题 + 条目标题」压成**一行**，例如（≈66 字符）：
#     وقایع سنه ثمان و خمسین و سبعمائه ذکر عزیمت پادشاه جانی بیک به آذربایجان
#     └──── 回历 758 年之事 ────┘└──── 条目标题 ────┘
# ``_classify`` 的 ≤55 字符上限会把整行判为 ``body``，于是年份标题留在段落
# 中间。短年份标题（≈32 字符）不受影响，故表现为**约一半命中、一半漏切**：
# 本书 46 个年份标题中漏切 24 个，并连锁导致 ch06–ch10 一个 ``##`` 都没有，
# 译者不得不把首条 h3 提到 h2 补层级（G0 判「标题层级数量不守恒」10 条）。
#
# 修法：判级**之前**先按条目标题关键词把年份前缀切出来单独成 ``##``，
# 余下条目标题单独成 ``###``——切分后即使用例的 55 字上限也失效，
# 故此处不走 ``_classify``。
#
# ⚠ **只能在行首命中**：正文叙述里也有 ``…در وقایع سنه …``（「在某某年…」），
# 那是散文不是标题，误切会把句子劈成标题。已核：全书行中命中 5 处，均为散文。
_YEAR_PREFIX = "وقایع سنه"


def _split_year_heading(line: str) -> tuple[str, str] | None:
    """行首年份标题与条目标题粘连时切开；不适用返回 ``None``。"""
    s = line.strip()
    if not s.startswith(_YEAR_PREFIX) or len(s) <= 55:
        return None
    cut = -1
    for kw in _H3_KW:
        i = s.find(kw, len(_YEAR_PREFIX))
        if i > 0 and (cut < 0 or i < cut):
            cut = i
    if cut < 0:
        return None
    year, entry = s[:cut].strip(), s[cut:].strip()
    if not year or not entry:
        return None
    return year, entry


_SENT_END = ".؟!:»…"
_MAX_PARA_CHARS = 600


def _ends_sentence(buf: list[str]) -> bool:
    if not buf:
        return False
    tail = buf[-1].rstrip()
    return bool(tail) and tail[-1] in _SENT_END


class Builder:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.buf: list[str] = []
        self.verse = False
        self.stats = {"header_blocks": 0, "separators": 0, "print_headers": 0,
                      "notes": 0, "headings": 0, "images": 0, "paras": 0}

    def _flush(self) -> None:
        if self.buf:
            self.out.append(" ".join(self.buf).strip())
            self.out.append("")
            self.stats["paras"] += 1
            self.buf = []

    def _emit(self, md_line: str) -> None:
        self._flush()
        self.out.append(md_line)
        self.out.append("")
        self.verse = False

    def feed_block(self, block: dict) -> None:
        if block.get("type") == "image":
            self._emit(block.get("text") or "")
            self.stats["images"] += 1
            return
        if block.get("type") != "text":
            # 表格块（本书均为误判的页眉）与公式块：本书不出现，保守丢弃并在统计里体现
            return
        if _is_digital_header(block):
            self.stats["header_blocks"] += 1
            return
        for raw_line in (block.get("text") or "").split("\n"):
            if not raw_line.strip():
                continue
            if _is_separator(raw_line):
                self.stats["separators"] += 1
                continue
            if _is_print_header(raw_line):
                self.stats["print_headers"] += 1
                continue
            split = _split_year_heading(raw_line)
            if split:
                year_part, entry_part = split
                self._emit("## " + year_part)
                self._emit("### " + entry_part)
                self.stats["headings"] += 2
                continue
            kind = _classify(raw_line)
            if kind in ("h2", "h3"):
                self._emit(("#" * (2 if kind == "h2" else 3)) + " " + raw_line.strip())
                self.stats["headings"] += 1
                continue
            if kind == "verse":
                self._emit(f"*{raw_line.strip()}*")
                self.verse = True
                continue
            if kind == "note":
                self._flush()
                self.buf = [raw_line.strip()]
                self.verse = False
                self.stats["notes"] += 1
                continue
            if self.verse:
                self._emit(raw_line.strip())
            else:
                self.buf.append(raw_line.strip())
        # 段落边界：块末收句标点则断段；过长（标点被 RTL 抽取打乱时）按字数上限兜底
        if not self.verse and self.buf:
            if _ends_sentence(self.buf) or sum(len(x) for x in self.buf) > _MAX_PARA_CHARS:
                self._flush()

    def finish(self) -> str:
        self._flush()
        return "\n".join(self.out).rstrip() + "\n"


def build_unit(unit: dict) -> tuple[str, dict]:
    b = Builder()
    b.out.append(f"# {unit['title']}")
    b.out.append("")
    for pno in range(unit["pages"][0], unit["pages"][1] + 1):
        page = _load_page(pno)
        for block in page.get("blocks", []):
            b.feed_block(block)
    return b.finish(), b.stats


def main() -> int:
    ap = argparse.ArgumentParser(description="重建本书 structured/")
    ap.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    ap.add_argument("--out", type=Path, default=None,
                    help="输出目录；缺省写回 structured/。仅用于沙箱验证 diff，"
                         "给定时不写 repairs.jsonl / structure.csv")
    args = ap.parse_args()

    struct = args.out if args.out is not None else STRUCT
    sandbox = args.out is not None

    repairs = []
    totals = {"header_blocks": 0, "separators": 0, "print_headers": 0,
              "notes": 0, "headings": 0, "images": 0, "paras": 0}
    for unit in UNIT_MAP:
        md, stats = build_unit(unit)
        for k, v in stats.items():
            totals[k] += v
        rel = "cover.md" if unit["region"] == "cover" else f"{unit['region']}/{unit['id']}.md"
        dest = struct / rel
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(md, encoding="utf-8")
        pages = f"{unit['pages'][0]}-{unit['pages'][1]}"
        repairs.append({
            "unit": unit["id"], "kind": "header_footer", "pages": unit["pages"],
            "count": stats["header_blocks"] + stats["print_headers"] + stats["separators"],
            "summary": f"去数字页眉 {stats['header_blocks']} / 印刷书名页眉 {stats['print_headers']} "
                       f"/ 分隔线 {stats['separators']}；保留编者注释段 {stats['notes']}、"
                       f"标题 {stats['headings']}、图 {stats['images']}",
            "method": "normalize_structured.py（按 raw bbox/正则，确定性）",
            "evidence": f"structured/raw/page-{unit['pages'][0]:03d}.json",
            "status": "done", "pages_range": pages,
        })
        print(f"  {rel:34s} chars={len(md):>7d} paras={stats['paras']:>4d} "
              f"h={stats['headings']:>3d} notes={stats['notes']:>3d} img={stats['images']}")

    print("totals:", totals)
    if not args.dry_run and not sandbox:
        rp = WS / "preprocessing" / "repairs.jsonl"
        with rp.open("w", encoding="utf-8") as f:
            for r in repairs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        # structure.csv（供 restructure 登记）
        sc = WS / "preprocessing" / "structure.csv"
        with sc.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "region", "kind", "title", "level", "rel_path"])
            for u in UNIT_MAP:
                rel = "cover.md" if u["region"] == "cover" else f"{u['region']}/{u['id']}.md"
                w.writerow([u["id"], u["region"], u["kind"], u["title"], u["level"], rel])
        print(f"wrote {rp.relative_to(WS)} and {sc.relative_to(WS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
