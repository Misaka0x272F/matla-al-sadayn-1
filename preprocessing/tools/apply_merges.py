#!/usr/bin/env python3
"""按 ``preprocessing/merge_plan.jsonl`` 的逐条裁定，把被分页/注释打断的段落合并。

只做**确定性搬运**：把同一 unit 的相邻正文块 i、i+1 合并为一块（源文以空格连接、
译文直接相接），标题位置不变，**不增删任何字符**。语义裁定（merge/keep）由 agent
写在 merge_plan.jsonl 里，本脚本不判断。

用法::

    python preprocessing/tools/apply_merges.py            # 应用全部 merge 裁定
    python preprocessing/tools/apply_merges.py --unit ch07 # 只做某单元
    python preprocessing/tools/apply_merges.py --verify preprocessing/backups/pre-merge-<ts>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
PLAN = WS / "preprocessing" / "merge_plan.jsonl"
_NORM = re.compile(r"[\s\W_]+")
REGION = {
    "cover": "cover.md",
    "front-titlepage": "frontmatter/front-titlepage.md",
    "front-copyright": "frontmatter/front-copyright.md",
    "front-preface": "frontmatter/front-preface.md",
    "front-dibache": "frontmatter/front-dibache.md",
    "back-appendix": "backmatter/back-appendix.md",
    "back-about": "backmatter/back-about.md",
}
for _n in range(1, 11):
    REGION[f"ch{_n:02d}"] = f"body/ch{_n:02d}.md"


def norm(s: str) -> str:
    return _NORM.sub("", s or "")


def segments(md: str) -> list[list[str]]:
    out: list[list[str]] = []
    for block in re.split(r"\n\s*\n", (md or "").strip("\n")):
        b = block.strip()
        if b:
            out.append(["H" if b.startswith("#") else "C", b])
    return out


def merge_unit(unit: str, pairs: list[tuple[int, int]]) -> list[str]:
    msgs: list[str] = []
    for side, sep in (("structured", " "), ("translation", "")):
        p = WS / side / REGION[unit]
        segs = segments(p.read_text(encoding="utf-8"))
        cpos = [k for k, (k2, _) in enumerate(segs) if k2 == "C"]
        for i, j in sorted(pairs, reverse=True):
            if j != i + 1:
                msgs.append(f"{unit}/{side}: 非相邻合并 {i},{j} 跳过")
                continue
            if i + 1 >= len(cpos):
                msgs.append(f"{unit}/{side}: 索引越界 {i},{j} 跳过")
                continue
            pi, pj = cpos[i], cpos[j]
            if any(segs[k][0] == "H" for k in range(pi + 1, pj)):
                msgs.append(f"{unit}/{side}: 块间存在标题 {i},{j} 跳过")
                continue
            segs[pi][1] = segs[pi][1].rstrip() + sep + segs[pj][1].lstrip()
            del segs[pj]
            cpos = [k for k, (k2, _) in enumerate(segs) if k2 == "C"]
        p.write_text("\n\n".join(t for _, t in segs) + "\n", encoding="utf-8")
        msgs.append(f"{unit}/{side}: 合并 {len(pairs)} 处 → 正文块 {len(cpos)}")
    return msgs


def verify(backup: Path) -> int:
    bad = 0
    for unit in REGION:
        for side in ("structured", "translation"):
            cur = WS / side / REGION[unit]
            old = backup / side / REGION[unit]
            if not cur.is_file() or not old.is_file():
                continue
            a = norm(old.read_text(encoding="utf-8"))
            b = norm(cur.read_text(encoding="utf-8"))
            if a != b:
                bad += 1
                print(f"✗ 不守恒 {unit}/{side}: 前 {len(a)} 字 vs 后 {len(b)} 字")
    print("守恒校验：" + ("全部通过" if bad == 0 else f"{bad} 项不一致"))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", help="只处理指定单元")
    ap.add_argument("--plan", default=str(PLAN), help="合并方案 JSONL 路径")
    ap.add_argument("--verify", help="对比备份目录做守恒校验")
    args = ap.parse_args()
    if args.verify:
        return verify(Path(args.verify))

    plan_path = Path(args.plan)
    plan = [json.loads(l) for l in plan_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_unit: dict[str, list[tuple[int, int]]] = {}
    for r in plan:
        if r.get("decision") == "merge":
            by_unit.setdefault(r["unit"], []).append((int(r["i"]), int(r["j"])))
    if args.unit:
        by_unit = {k: v for k, v in by_unit.items() if k == args.unit}
    for unit, pairs in by_unit.items():
        for m in merge_unit(unit, pairs):
            print(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
