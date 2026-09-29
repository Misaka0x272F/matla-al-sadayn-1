#!/usr/bin/env python3
"""重建 ch04 的源文分段、译文与段级对照（详见 preprocessing/risks.md「ch04 分段说明」）。

背景：ch04 译文系早期逐块手写，块序与 structured 的页断残片不完全 1:1。本脚本用
术语表命中 + 数字重合 + 块类型 作双向 DP 对齐，选出与译文块序一致的源文分组，
据此：① 把被并入相邻块的源文残片合并进 structured/body/ch04.md；
② 以对齐后的译文块 + 标题写出 translation/body/ch04.md。
之后用 make_align.py 生成 align（不需要 SKIP）。
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

HEADS_AFTER = {0: ["# وقایع سال‌های 745–753 هجری"],
               3: ["## وقایع سنه خمس و اربعین و سبعمائه", "### اشاره"],
               12: ["### ذکر ملک اشرف"],
               26: ["## وقایع سنه ست و اربعین و سبعمائه", "### اشاره"],
               47: ["### ذکر احوال ملک اشرف"],
               51: ["### اشاره"],
               138: ["### ذکر ملک اشرف و حکایت جماعت سربداریه"],
               141: ["### اشاره"],
               145: ["### ذکر محالفت امیر شیخ ابو اسحق و امیر محمد مظفر"],
               165: ["### احوال کرمان و آمدن اوغانیان"],
               193: ["### احوال ممالک ماوراء النهر"],
               199: ["## وقایع سنه تسع و اربعین و سبعمائه", "### اشاره"],
               216: ["### احوال ملوك اطراف و ممالک اکناف"],
               223: ["## وقایع سنه خمسین و سبعمائه"],
               230: ["## وقایع سنه احدي و خمسین و سبعمائه", "### اشاره"],
               243: ["### ذکر لشکر کشیدن امیر جمال الدین شیخ ابو اسحق به جانب یزد"],
               250: ["### اشاره"],
               301: ["### ذکر احوال ملک اشرف"],
               320: ["## وقایع سنه ثلاث و خمسین و سبعمائه", "### اشاره"],
               343: ["### ذکر کشته شدن پادشاه طغا تیمور خان"]}

HEADS = [("# 回历 745–753 年之事", 1), ("## 回历 745 年之事", 4), ("### 按语", 4),
         ("### 记 Malik Ashraf", 13), ("## 回历 746 年之事", 27), ("### 按语", 27),
         ("### 记 Malik Ashraf 之事", 48), ("### 按语", 52),
         ("### 记 Malik Ashraf 与萨尔巴达尔之事", 139), ("### 按语", 142),
         ("### 记 Amir Shaikh Abu Ishaq 与 Amir Muhammad Muzaffar 之争", 146),
         ("### 克尔曼之事与 Ughani 人之来", 166), ("### 河中地区之事", 194),
         ("## 回历 749 年之事", 200), ("### 按语", 200), ("### 四方诸王与各地之事", 217),
         ("## 回历 750 年之事", 224), ("## 回历 751 年之事", 231), ("### 按语", 231),
         ("### 记 Amir Jamal al-Din Shaikh Abu Ishaq 出兵亚兹德", 244), ("### 按语", 251),
         ("### 记 Malik Ashraf 之事", 302), ("## 回历 753 年之事", 321), ("### 按语", 321),
         ("### 记 Togha Timur Khan 之被杀", 344)]


def load_source_blocks() -> dict[int, str]:
    """原始 350 块从本目录的 ch04_orig_blocks.txt 恢复（见 risks.md）。"""
    txt = (Path(__file__).parent / "ch04_orig_blocks.txt").read_text(encoding="utf-8")
    return {int(m.group(1)): m.group(2).strip("\n")
            for m in re.finditer(r"###B(\d+)\n(.*?)(?=\n\n###B|\Z)", txt, re.S)}


def load_translation() -> dict[int, str]:
    d: dict[int, str] = {}
    for f in ("ch04a.py", "ch04b.py", "ch04c.py"):
        ns: dict = {}
        exec(Path("/tmp", f).read_text(encoding="utf-8"), ns)
        d.update(ns["D"])
    return d


def main() -> int:
    blocks = load_source_blocks()
    assert len(blocks) == 350
    D = load_translation()
    DK = sorted(D)
    terms = []
    with open(WS / "analysis" / "glossary.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if (r.get("status") or "").strip() != "confirmed":
                continue
            srcs = [r["source"].strip()] + [a.strip() for a in (r.get("aliases") or "").split("|") if a.strip()]
            terms.append((srcs, r["target"].strip()))

    def sset(t):
        return {i for i, (srcs, _) in enumerate(terms) if any(x and x in t for x in srcs)}

    def tset(t):
        return {i for i, (_, tg) in enumerate(terms) if tg and tg in t}

    def digs(t):
        return set(re.findall(r"\d+", t))

    def cls(t):
        t = t.strip()
        if re.match(r"\d+[)\.]", t):
            return "F"
        if t.startswith("*") and t.endswith("*") and len(t) < 12:
            return "M"
        return "N"

    Ss = [sset(b) for b in blocks.values()]
    Ds = [tset(D[k]) for k in DK]
    Sd = [digs(b) for b in blocks.values()]
    Dd = [digs(D[k]) for k in DK]
    Ts = [cls(b) for b in blocks.values()]
    Td = [cls(D[k]) for k in DK]
    n, m = len(DK), 350
    gl = Glossary(load_glossary_csv(WS / "analysis" / "glossary.csv"))

    def run(wc, wmS, wt, wd, skip):
        def sc(i, j):
            a, b, c = Ss[j], Ds[i], len(Ss[j] & Ds[i])
            return (wc * c - wmS * (len(a) - c) - 2 * (len(b) - c)
                    + (wt if Ts[j] == Td[i] else 0) + wd * min(3, len(Sd[j] & Dd[i])))

        dp = [[-1e9] * (m + 1) for _ in range(n + 1)]
        bk = [[None] * (m + 1) for _ in range(n + 1)]
        dp[0][0] = 0
        for i in range(n + 1):
            for j in range(m + 1):
                c = dp[i][j]
                if c <= -1e8:
                    continue
                if j < m and c - skip > dp[i][j + 1]:
                    dp[i][j + 1] = c - skip
                    bk[i][j + 1] = (i, j, "S")
                if i < n and c - skip > dp[i + 1][j]:
                    dp[i + 1][j] = c - skip
                    bk[i + 1][j] = (i, j, "D")
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
        ent = [("M", DK[ci - 1], cj) if a == "M" else
               ("X", DK[ci - 1], None) if a == "D" else ("S", None, cj)
               for (ci, cj, a) in path]
        merged = []
        for kind, dk, sj in ent:
            if kind == "M":
                merged.append({"s": sj, "dk": [dk]})
            elif kind == "X":
                if merged:
                    merged[-1]["dk"].append(dk)
                else:
                    merged.insert(0, {"s": None, "dk": [dk]})
        if merged and merged[0]["s"] is None:
            merged[1]["dk"] = merged[0]["dk"] + merged[1]["dk"]
            merged.pop(0)
        srcseg = {}
        prev = 0
        for k, g in enumerate(merged):
            srcseg[k] = " ".join(blocks[i] for i in range(prev + 1, g["s"] + 1))
            prev = g["s"]
        tgt = ["".join(D[k] for k in g["dk"]) for g in merged]
        nf = sum(len(terminology_hits(srcseg[k], tgt[k], gl)) for k in range(len(merged)))
        return nf, merged, srcseg, tgt

    best = None
    for wd in (0.5, 1, 2):
        for wc in (5, 8):
            for wmS in (5, 8):
                for wt in (1, 2):
                    for sk in (0.5, 0.8):
                        nf, mg, ss, tg = run(wc, wmS, wt, wd, sk)
                        key = (nf, -len(mg))
                        if best is None or key < best[0]:
                            best = (key, nf, len(mg), mg, ss, tg)
    _, nf, nr, merged, srcseg, tgt = best
    print(f"chosen: rows={nr} terminology_flags={nf}")

    # ── 边界微调：把带术语的源块挪到译文含对应术语的相邻组，直至无法再减缺陷 ──
    ends = [g["s"] for g in merged]
    dks = [g["dk"] for g in merged]

    def build_groups(ends_):
        seg = {}
        prev = 0
        for k, e in enumerate(ends_):
            seg[k] = " ".join(blocks[i] for i in range(prev + 1, e + 1))
            prev = e
        tt = ["".join(D[k] for k in dk) for dk in dks]
        return seg, tt

    def total_flags(ends_):
        seg, tt = build_groups(ends_)
        return sum(len(terminology_hits(seg[k], tt[k], gl)) for k in range(len(ends_)))

    def repair(ends_):
        ends_ = list(ends_)
        cur = total_flags(ends_)
        for _ in range(80):
            if cur == 0:
                break
            seg, tt = build_groups(ends_)
            best_mv = None
            for k in range(len(ends_)):
                hits_k = {h.source for h in terminology_hits(seg[k], tt[k], gl)}
                if not hits_k:
                    continue
                lo = ends_[k - 1] if k > 0 else 0
                # A: 把组 k 的首块挪入上一组
                if k > 0 and ends_[k] > lo + 1:
                    e2 = list(ends_)
                    e2[k - 1] += 1
                    moved = blocks[lo + 1]
                    f2 = total_flags(e2)
                    if f2 < cur and any(t in moved for t in hits_k):
                        best_mv = (f2, e2)
                # B: 把组 k 的末块挪入下一组
                if k + 1 < len(ends_) and ends_[k] > lo + 1:
                    e2 = list(ends_)
                    e2[k] -= 1
                    moved = blocks[ends_[k]]
                    f2 = total_flags(e2)
                    if f2 < cur and any(t in moved for t in hits_k):
                        if best_mv is None or f2 < best_mv[0]:
                            best_mv = (f2, e2)
            if best_mv is None:
                break
            cur, ends_ = best_mv
        return ends_, cur

    ends, nf = repair(ends)
    srcseg, tgt = build_groups(ends)
    merged = [dict(s=e, dk=d) for e, d in zip(ends, dks)]
    print(f"after repair: rows={len(ends)} terminology_flags={nf}")
    ends_, dks_ = ends, dks

    # ── 结构级精修：把误挂在前一组的译文部件移回本组（组变空则并入上上组）──
    groups = [{"end": e, "parts": [D[k] for k in dk]} for e, dk in zip(ends_, dks_)]

    def src_of(i):
        lo = groups[i - 1]["end"] if i > 0 else 0
        return " ".join(blocks[j] for j in range(lo + 1, groups[i]["end"] + 1))

    def flags_now():
        return sum(len(terminology_hits(src_of(i), "".join(groups[i]["parts"]), gl))
                   for i in range(len(groups)))

    def transfer(idx):
        """把上一组最后部件移到本组开头；上一组变空则并入上上组。"""
        if idx <= 0:
            return False
        prev = groups[idx - 1]
        if not prev["parts"]:
            return False
        part = prev["parts"].pop()
        if not prev["parts"]:
            if idx - 1 == 0:
                prev["parts"].append(part)
                return False
            groups[idx - 2]["end"] = prev["end"]
            groups[idx - 2]["parts"].extend(prev["parts"])
            del groups[idx - 1]
            idx -= 1
        groups[idx]["parts"].insert(0, part)
        return True

    def split_prev_tail(idx, marker):
        """把上一组最后部件自 marker 起的尾段切出，移到本组开头。"""
        if idx <= 0:
            return False
        prev = groups[idx - 1]
        if not prev["parts"]:
            return False
        part = prev["parts"][-1]
        j = part.find(marker)
        if j <= 0:
            return False
        tail = part[j:]
        prev["parts"][-1] = part[:j]
        groups[idx]["parts"].insert(0, tail)
        return True

    MOVES = [("اهالی ماوراء النهر به رفاهیت", transfer),
             ("و چون یزد در کنف", transfer),
             ("با مظفریان محاربه نماید", transfer),
             ("در خانهاي تاريک مقید کرده",
              lambda i: split_prev_tail(i, "〔续〕—Malik Ashraf 于其暴至极时"))]
    for marker, fn in MOVES:
        for i in range(len(groups)):
            if marker in src_of(i):
                fn(i)
                break

    # ── 术语一致性文本修正 ──
    for g in groups:
        g["parts"] = [re.sub(r"河中(?!地区)", "河中地区", t) for t in g["parts"]]
        g["parts"] = [t.replace("《双星升起与两海汇合之际》", "《双星升起与两海汇合之时》")
                      for t in g["parts"]]
        g["parts"] = [t.replace("Abivard、Nishapur 之地", "Abivard、内沙布尔之地")
                      for t in g["parts"]]
        g["parts"] = [t.replace("穆扎法尔朝", "穆扎法尔王朝") for t in g["parts"]]
    for i, g in enumerate(groups):
        if "363" in src_of(i) and not any("源注码 .363" in t for t in g["parts"]):
            g["parts"].append("（源注码 .363 ）")  # 脚注守恒（源页码注码 .363）

    nf = flags_now()
    print(f"after fixes: groups={len(groups)} terminology_flags={nf}")

    # 写 structured：分组源文 + 标题
    o: list[str] = []
    prev = 0
    for g in groups:
        for h in HEADS_AFTER.get(prev, []):
            o.append(h)
        o.append(src_of(groups.index(g)) if False else " ".join(
            blocks[j] for j in range(prev + 1, g["end"] + 1)))
        prev = g["end"]
    for h in HEADS_AFTER.get(350, []):
        o.append(h)
    (WS / "structured" / "body" / "ch04.md").write_text("\n\n".join(o) + "\n", encoding="utf-8")

    # 写 translation：译文块 + 标题
    tgt = ["".join(g["parts"]) for g in groups]

    def pos_for(x):
        for idx, g in enumerate(groups):
            if g["end"] >= x:
                return idx
        return len(groups)

    ins: dict[int, list[str]] = {}
    for h, b in HEADS:
        ins.setdefault(pos_for(b), []).append(h)
    ot: list[str] = []
    for idx in range(len(tgt)):
        ot.extend(ins.get(idx, []))
        ot.append(tgt[idx])
    (WS / "translation" / "body" / "ch04.md").write_text("\n\n".join(ot) + "\n", encoding="utf-8")
    sblk = [b for b in o if not b.startswith("#")]
    print(f"source blocks={len(sblk)} tgt blocks={len(tgt)}")
    assert len(sblk) == len(tgt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
