#!/usr/bin/env python3
"""定位「被分页与编者注释打断」的证据（确定性，只读）。

本脚本不改任何产物：扫 ``structured/raw/page-NNN.json``，找出每个被清洗掉的
版式标记（印刷书名页眉 ``مطلع سعدین… ص NN:``、分隔线 ``____``、数字页眉），
记录其**两侧最近的存活行**，再把这两行映射到当前 ``structured/*.md`` 的正文块编号，
产出：

- ``preprocessing/breaks.jsonl``  —— 每行一个被删标记（页断证据）；
- ``preprocessing/fragments.csv`` —— 按（单元, 块 i, 块 i+1）去重的候选碎片边界，
  供 agent 逐条语义裁定（merge|keep|unresolved），**不做自动合并**。

判据说明：不用「上一块是否以句末标点结尾」——RTL 抽取会把句号搬到下一词首
（如 ``.العالمین``），该判据误报极高。本脚本只用「页眉/分隔线被删的位置」这一
确定性证据，语义由 agent 读原文裁定。
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from normalize_structured import (  # noqa: E402
    UNIT_MAP,
    _is_digital_header,
    _is_print_header,
    _is_separator,
    _load_page,
)

WS = Path(__file__).resolve().parents[2]
STRUCT = WS / "structured"
_NORM = re.compile(r"[\s\W_]+")
_NOTE_RE = re.compile(r"^\s*\d+\s*\)")
_VERSE_LABEL_RE = re.compile(r"^\*(نظم|بیت|مصرع)\*$")


def norm(s: str) -> str:
    return _NORM.sub("", s or "")


def content_blocks(md: str) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", (md or "").strip("\n")):
        b = block.strip()
        if b and not b.startswith("#"):
            out.append(b)
    return out


def unit_rel(unit: dict) -> str:
    return "cover.md" if unit["region"] == "cover" else f"{unit['region']}/{unit['id']}.md"


def stream_lines(unit: dict) -> list[tuple[str, int, int, str]]:
    """把单元的 raw 行流压成 [(kind, pdf_page, block_idx, text)]。

    kind ∈ {live, print_header, separator, digital_header}；live 是保留行，
    其余是被清洗的标记行。block_idx 是 raw 块序号（页内从 0 计），便于定位。
    """
    out: list[tuple[str, int, int, str]] = []
    for pno in range(unit["pages"][0], unit["pages"][1] + 1):
        page = _load_page(pno)
        for bi, block in enumerate(page.get("blocks", [])):
            if block.get("type") == "image":
                out.append(("image", pno, bi, (block.get("text") or "").strip()))
                continue
            if block.get("type") != "text":
                continue
            if _is_digital_header(block):
                out.append(("digital_header", pno, bi, (block.get("text") or "").strip()))
                continue
            for raw_line in (block.get("text") or "").split("\n"):
                s = raw_line.strip()
                if not s:
                    continue
                if _is_separator(s):
                    out.append(("separator", pno, bi, s))
                elif _is_print_header(s):
                    out.append(("print_header", pno, bi, s))
                else:
                    out.append(("live", pno, bi, s))
    return out


def assign_blocks(blocks: list[str], lines: list[tuple]) -> tuple[list[int | None], int]:
    """把 raw 存活行映射到当前 structured 正文块号。

    structured 的块序与 raw 行序可能局部不一致（手写组装 / realign / RTL 重排），
    故不用严格顺序游标，而是「命中候选块中取离上一行块号最近者」（同距则取靠后）。
    这样短行不会误配到很远的块。返回 (每行块号, 未命中数)。
    """
    nb = [norm(b) for b in blocks]
    idx = [i for i, x in enumerate(lines) if x[0] == "live"]
    assigned: dict[int, int | None] = {}
    last = 0
    miss = 0
    for i in idx:
        t = norm(lines[i][3])
        if not t:
            assigned[i] = None
            continue
        cands = [k for k, b in enumerate(nb) if t in b]
        if not cands:
            miss += 1
            assigned[i] = None
            continue
        b = min(cands, key=lambda k: (abs(k - last), 0 if k >= last else 1))
        assigned[i] = b
        last = b
    return [assigned.get(i) for i in range(len(lines))], miss


def trace() -> tuple[list[dict], list[dict]]:
    breaks: list[dict] = []
    frag_rows: dict[tuple, dict] = {}
    total_miss = 0
    for unit in UNIT_MAP:
        md_path = STRUCT / unit_rel(unit)
        if not md_path.is_file():
            continue
        blocks = content_blocks(md_path.read_text(encoding="utf-8"))
        lines = stream_lines(unit)
        blk_of, miss = assign_blocks(blocks, lines)
        total_miss += miss
        live_idx = [i for i, x in enumerate(lines) if x[0] == "live"]
        for i, (kind, pno, bi, text) in enumerate(lines):
            if kind in ("live", "image"):
                continue
            prev_i = next((j for j in reversed(live_idx) if j < i), None)
            next_i = next((j for j in live_idx if j > i), None)
            prev_line = lines[prev_i][3] if prev_i is not None else ""
            next_line = lines[next_i][3] if next_i is not None else ""
            pb = blk_of[prev_i] if prev_i is not None else None
            nblk = blk_of[next_i] if next_i is not None else None
            rec = {
                "unit": unit["id"],
                "pdf_page": pno,
                "raw_block": bi,
                "kind": kind,
                "prev_line": prev_line,
                "next_line": next_line,
                "prev_block": pb,
                "next_block": nblk,
            }
            breaks.append(rec)
            if pb is None or nblk is None or pb == nblk:
                continue
            pi, nj = blocks[pb].strip(), blocks[nblk].strip()
            pi_note, nj_note = bool(_NOTE_RE.match(pi)), bool(_NOTE_RE.match(nj))
            if _VERSE_LABEL_RE.match(pi):
                cls = "verse_label"
            elif pi_note and not nj_note and not nj.startswith("*"):
                cls = "note_cont"        # 注文跨页被切断（后块无新注号）
            elif not pi_note and nj_note:
                cls = "body_to_note"     # 正文页 → 该页注释区（合法边界）
            elif pi_note and nj_note:
                cls = "note_to_note"     # 相邻两条注（合法边界）
            else:
                cls = "body"             # 正文-正文：潜在页断续段
            key = (unit["id"], pb, nblk)
            cur = frag_rows.get(key)
            if cur is None:
                frag_rows[key] = {
                    "unit": unit["id"],
                    "block_i": pb,
                    "block_j": nblk,
                    "class": cls,
                    "evidence_kinds": {kind},
                    "evidence_pages": {pno},
                    "decision": "",
                }
            else:
                cur["evidence_kinds"].add(kind)
                cur["evidence_pages"].add(pno)
    if total_miss:
        print(f"警告：{total_miss} 条 raw 存活行未能在 structured 中顺序定位", file=sys.stderr)
    frags = []
    for r in frag_rows.values():
        r["evidence_kinds"] = "|".join(sorted(r["evidence_kinds"]))
        r["evidence_pages"] = "|".join(str(p) for p in sorted(r["evidence_pages"]))
        frags.append(r)
    frags.sort(key=lambda r: (r["unit"], r["block_i"]))
    return breaks, frags


def main() -> int:
    breaks, frags = trace()
    bp = WS / "preprocessing" / "breaks.jsonl"
    with bp.open("w", encoding="utf-8") as f:
        for r in breaks:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    fp = WS / "preprocessing" / "fragments.csv"
    with fp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["unit", "block_i", "block_j", "class",
                        "evidence_kinds", "evidence_pages", "decision"],
        )
        w.writeheader()
        w.writerows(frags)
    from collections import Counter

    by_kind = Counter(r["kind"] for r in breaks)
    by_cls = Counter(r["class"] for r in frags)
    print(f"breaks.jsonl: {len(breaks)} 条  {dict(by_kind)}")
    print(f"fragments.csv: {len(frags)} 条候选边界  {dict(by_cls)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
