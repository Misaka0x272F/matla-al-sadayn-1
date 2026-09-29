#!/usr/bin/env python3
"""导出某单元的源文块（编号），供逐块对译——保证 align 语义不错配。

`make_align.py` 只能校验「块数相等」，无法发现译块与源块的语义错配。因此每个单元
开译前先用本工具列出 structured 的正文块（与 fidelity.content_blocks 同一切块规则），
再按同一编号逐块翻译。

用法：
  python preprocessing/tools/dump_blocks.py <unit_id> [--translated]
  python preprocessing/tools/dump_blocks.py --all
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from make_align import content_blocks

WS = Path(__file__).resolve().parents[2]


def rel_paths() -> dict[str, str]:
    with open(WS / "preprocessing" / "structure.csv", encoding="utf-8-sig", newline="") as f:
        return {r["id"].strip(): r["rel_path"].strip() for r in csv.DictReader(f)}


def dump(unit_id: str, rel: str, side: str) -> int:
    p = WS / ("translation" if side == "tgt" else "structured") / rel
    if not p.is_file():
        print(f"[{unit_id}] 缺文件：{p}", file=sys.stderr)
        return 1
    blocks = content_blocks(p.read_text(encoding="utf-8"))
    print(f"===== {unit_id} ({side}) 共 {len(blocks)} 块：{rel}")
    for i, b in enumerate(blocks, 1):
        print(f"\n----- [{i}] len={len(b)}")
        print(b)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("units", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--translated", action="store_true", help="改列 translation 侧")
    args = ap.parse_args()
    rels = rel_paths()
    units = list(rels) if args.all else args.units
    side = "tgt" if args.translated else "src"
    rc = 0
    for u in units:
        if u not in rels:
            print(f"未知单元：{u}", file=sys.stderr)
            rc = 2
            continue
        rc |= dump(u, rels[u], side)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
