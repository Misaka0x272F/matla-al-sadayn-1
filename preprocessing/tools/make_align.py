#!/usr/bin/env python3
"""从 structured/ + translation/ 自动生成段级 align（保证 src 逐字源文、md↔align 一致）。

契约（见 auto-epublizer 的 review/fidelity.py、review/g0.py）：
- 反向源保真：align 的 src 去空白后须是 structured 非空行的子串 → 本工具**直接取
  structured 的正文块原文**作 src，杜绝手抄误差；
- md↔align 交付审计：translation md 与 align 的 tgt 归一化后须一致 → 本工具**直接取
  translation md 的同一块**作 tgt；
- 正文块定义与 fidelity.content_blocks 一致：按空行切、跳过 `#` 开头标题行与空块。

因此要求：**translation md 的正文块与 structured 的正文块一一对应、顺序一致、数量相等**。
若某源块有意不译，请在脚本 SKIP 映射中显式声明（按 unit 与块序号），不要静默丢弃。

用法：
  python preprocessing/tools/make_align.py front-titlepage front-copyright
  python preprocessing/tools/make_align.py --all
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[2]

# 有意不译的源块：{unit_id: {块序号(1起): 理由}}；生成时该块不进 align（前向保真仅 advisory）
SKIP: dict[str, dict[int, str]] = {}


def content_blocks(md: str) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", (md or "").strip("\n")):
        b = block.strip()
        if not b or b.startswith("#"):
            continue
        out.append(b)
    return out


def unit_rel_paths() -> dict[str, str]:
    m: dict[str, str] = {}
    with open(WS / "preprocessing" / "structure.csv", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            m[row["id"].strip()] = row["rel_path"].strip()
    return m


def make(unit_id: str, rel: str) -> tuple[bool, str]:
    sp = WS / "structured" / rel
    tp = WS / "translation" / rel
    if not sp.is_file() or not tp.is_file():
        return False, f"{unit_id}: 缺文件（structured={sp.is_file()}, translation={tp.is_file()}）"
    src_blocks = content_blocks(sp.read_text(encoding="utf-8"))
    tgt_blocks = content_blocks(tp.read_text(encoding="utf-8"))
    skip = SKIP.get(unit_id, {})

    pairs: list[tuple[str, str]] = []
    ti = 0
    for i, s in enumerate(src_blocks, start=1):
        if i in skip:
            continue
        if ti >= len(tgt_blocks):
            return False, f"{unit_id}: 译文块不足（源 {len(src_blocks)}，译 {len(tgt_blocks)}）"
        pairs.append((s, tgt_blocks[ti]))
        ti += 1
    if ti != len(tgt_blocks):
        return False, (
            f"{unit_id}: 块数不匹配（源 {len(src_blocks)} 跳过 {len(skip)} 译 {len(tgt_blocks)}）"
        )

    ap = WS / "translation" / "align" / f"{unit_id}.jsonl"
    ap.parent.mkdir(parents=True, exist_ok=True)
    with ap.open("w", encoding="utf-8") as f:
        for seq, (s, t) in enumerate(pairs, start=1):
            f.write(json.dumps({"seq": seq, "src": s, "tgt": t, "note": None},
                               ensure_ascii=False) + "\n")
    return True, f"{unit_id}: {len(pairs)} 行 → {ap.relative_to(WS)}"


def main() -> int:
    ap = argparse.ArgumentParser(description="自动生成段级 align")
    ap.add_argument("units", nargs="*", help="单元 id（缺省配合 --all）")
    ap.add_argument("--all", action="store_true", help="对全部已有译文的单元生成")
    args = ap.parse_args()

    rels = unit_rel_paths()
    units = list(rels) if args.all else args.units
    if not units:
        print("请给单元 id 或 --all", file=sys.stderr)
        return 2

    ok = True
    for u in units:
        if u not in rels:
            print(f"未知单元：{u}", file=sys.stderr)
            ok = False
            continue
        good, msg = make(u, rels[u])
        print(("✓ " if good else "✗ ") + msg)
        ok = ok and good
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
