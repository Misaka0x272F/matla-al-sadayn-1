#!/usr/bin/env python3
"""通用单元对齐重建（ch04 方法的推广）。

用途：某些单元的译文手写分块与 structured 页断残片不 1:1（译文内容在、但配对错位），
表现为大量「长度比」advisory。本脚本用「术语命中 + 数字重合 + 块类型」双向 DP 求
源块↔译块的分组映射，然后：
  ① 合并源文中被并入相邻块的残片（只删空行，文本不损）；
  ② 以分组后的译文块重写 translation md（文本不损，仅并块 + 重排标题位置）。
结果：源块数 == 译块数，make_align 顺序配对即正确。

用法：python preprocessing/tools/realign_unit.py ch07 [ch05 ch06 ...]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# CLI 源路径相对本脚本推导（tools → preprocessing → 工作区 → workspaces → 根）
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "auto-epublizer" / "src"))

from make_align import content_blocks  # noqa: E402
from auto_translator.glossary.csv_io import Glossary, load_glossary_csv  # noqa: E402
from auto_translator.review.g0 import terminology_hits  # noqa: E402

WS = Path(__file__).resolve().parents[2]
GLOSSARY = WS / "analysis" / "glossary.csv"


def _cls(t: str) -> str:
    t = t.strip()
    if re.match(r"\d+[)\.]", t):
        return "F"
    if t.startswith("*") and t.endswith("*") and len(t) < 12:
        return "M"
    return "N"


def _segments(md: str) -> list[tuple[str, str]]:
    """返回 [(kind, text)]，kind ∈ {H, C}；H=标题行，C=正文块（保序）。"""
    out: list[tuple[str, str]] = []
    for block in re.split(r"\n\s*\n", (md or "").strip("\n")):
        b = block.strip()
        if not b:
            continue
        out.append(("H" if b.startswith("#") else "C", b))
    return out


def _locate(side: str, unit: str) -> Path:
    """在 body/ 或 frontmatter/ 下定位单元文件。"""
    base = WS / side
    for sub in ("body", "frontmatter", "backmatter"):
        p = base / sub / f"{unit}.md"
        if p.is_file():
            return p
    p = base / f"{unit}.md"
    if p.is_file():
        return p
    raise FileNotFoundError(f"{side}/{unit}.md")


def realign(unit: str) -> int:
    smd_path = _locate("structured", unit)
    tmd_path = _locate("translation", unit)
    S = content_blocks(smd_path.read_text(encoding="utf-8"))
    tsegs = _segments(tmd_path.read_text(encoding="utf-8"))
    T = [x for k, x in tsegs if k == "C"]
    n, m = len(T), len(S)
    if n != m:
        print(f"{unit}: 源 {m} / 译 {n} 不等，先跳过（需人工）")
        return 1

    terms = []
    with open(GLOSSARY, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if (r.get("status") or "").strip() != "confirmed":
                continue
            srcs = [r["source"].strip()] + [
                a.strip() for a in (r.get("aliases") or "").split("|") if a.strip()
            ]
            terms.append((srcs, r["target"].strip()))

    def sset(t):
        return {i for i, (srcs, _) in enumerate(terms) if any(x and x in t for x in srcs)}

    def tset(t):
        return {i for i, (_, tg) in enumerate(terms) if tg and tg in t}

    def digs(t):
        return set(re.findall(r"\d+", t))

    Ss = [sset(s) for s in S]
    Ts = [tset(t) for t in T]
    Sd = [digs(s) for s in S]
    Td = [digs(t) for t in T]
    Sc = [_cls(s) for s in S]
    Tc = [_cls(t) for t in T]

    def sc(i, j):
        a, b = Ss[j], Ts[i]
        c = len(a & b)
        return (
            5 * c
            - 5 * (len(a) - c)
            - 2 * (len(b) - c)
            + (2 if Sc[j] == Tc[i] else 0)
            + 0.5 * min(3, len(Sd[j] & Td[i]))
        )

    NEG = -1e9
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    bk = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            c = dp[i][j]
            if c <= -1e8:
                continue
            if j < m and c - 0.5 > dp[i][j + 1]:
                dp[i][j + 1] = c - 0.5
                bk[i][j + 1] = (i, j, "S")
            if i < n and c - 0.5 > dp[i + 1][j]:
                dp[i + 1][j] = c - 0.5
                bk[i + 1][j] = (i, j, "T")
            if i < n and j < m:
                v = c + sc(i, j)
                if v > dp[i + 1][j + 1]:
                    dp[i + 1][j + 1] = v
                    bk[i + 1][j + 1] = (i, j, "M")
    i, j = n, m
    path = []
    while (i, j) != (0, 0):
        a = bk[i][j][2]
        path.append((i, j, a))
        i, j = bk[i][j][0], bk[i][j][1]
    path.reverse()

    # 分组：每组 = (S 末块号, [T 块号…])；skipS → 并入上一组；skipT → 并入上一组
    groups: list[dict] = []
    for ci, cj, a in path:
        if a == "M":
            groups.append({"s": cj, "t": [ci]})
        elif a == "T":
            if groups:
                groups[-1]["t"].append(ci)
            else:
                groups.append({"s": None, "t": [ci]})
        elif a == "S" and groups:
            pass  # 源块并入上一组
    if groups and groups[0]["s"] is None:
        groups[1]["t"] = groups[0]["t"] + groups[1]["t"]
        groups.pop(0)

    # ① structured：按组并段
    s_out: list[str] = []
    sseg_after: dict[int, list[str]] = {}
    for kind, text in _segments(smd_path.read_text(encoding="utf-8")):
        if kind == "H":
            sseg_after.setdefault(len(s_out), []).append(text)
        else:
            s_out.append(text)
    new_s: list[str] = []
    prev = 0
    for g in groups:
        new_s.extend(sseg_after.get(prev, []))
        new_s.append(" ".join(S[prev:g["s"]]))
        prev = g["s"]
    new_s.extend(sseg_after.get(prev, []))

    # ② translation：按组并块，标题插在组首
    t_blocks = [x for k, x in tsegs if k == "C"]
    heads_before: dict[int, list[str]] = {}
    idx = 0
    for kind, text in tsegs:
        if kind == "H":
            heads_before.setdefault(idx, []).append(text)  # 位于第 idx+1 个正文块之前
        else:
            idx += 1
    new_t: list[str] = []
    for g in groups:
        for h in heads_before.get(g["t"][0] - 1, []):
            new_t.append(h)
        new_t.append("".join(t_blocks[t - 1] for t in g["t"]))

    # 术语冲突自检（源组文本 vs 译组文本）
    gl = Glossary(load_glossary_csv(GLOSSARY))
    conf = 0
    prev = 0
    for g in groups:
        stext = " ".join(S[prev : g["s"]])
        ttext = "".join(t_blocks[t - 1] for t in g["t"])
        if terminology_hits(stext, ttext, gl):
            conf += 1
        prev = g["s"]

    smd_path.write_text("\n\n".join(new_s) + "\n", encoding="utf-8")
    tmd_path.write_text("\n\n".join(new_t) + "\n", encoding="utf-8")
    print(f"{unit}: groups={len(groups)} 源块={len(new_s)} 译块={len(new_t)} 术语冲突={conf}")
    return 1 if conf else 0


if __name__ == "__main__":
    rc = 0
    for u in sys.argv[1:]:
        rc |= realign(u)
    raise SystemExit(rc)
