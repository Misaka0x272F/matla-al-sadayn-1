#!/usr/bin/env python3
"""组装 ch03.md：按源块序号 1:1 写出译文并插入标题。"""
import glob
import os

D = {}
_fixed = 'preprocessing/draft/ch03_fixed.py'
if os.path.exists(_fixed):
    ns = {}
    exec(open(_fixed, encoding='utf-8').read(), ns)
    D.update(ns['D'])
else:
    for f in sorted(glob.glob('preprocessing/draft/ch03_*.py')):
        ns = {}
        exec(open(f, encoding='utf-8').read(), ns)
        D.update(ns['D'])

missing = [i for i in range(1, 328) if i not in D]
assert not missing, missing

HEADS = [
    ("回历 737–744 年之事", "# ", 0),
    ("按语", "### ", 19),
    ("记托盖帖木儿汗第二次赴伊拉克", "### ", 24),
    ("记جهان تیمور汗之王权", "### ", 36),
    ("记萨尔巴达尔之起及其治呼罗珊之始", "### ", 46),
    ("记وجیه الدین مسعود埃米尔在塞卜泽瓦尔之统帅", "### ", 51),
    ("回历 740 年之事", "## ", 79), ("按语", "### ", 79),
    ("记阿勒穆扎法尔朝之兴与其家族之状", "### ", 92),
    ("按语", "### ", 160),
    ("回历 742 年之事", "## ", 191), ("按语", "### ", 191),
    ("记马立克·阿什拉夫于皮尔·侯赛因埃米尔逃后之来", "### ", 202),
    ("按语", "### ", 204),
    ("记马立克·阿什拉夫自设拉子返回之后", "### ", 207),
    ("记七四四年之事", "### ", 256),
    ("记马立克·阿什拉夫之埃米尔位与其十三年之治", "### ", 285),
    ("记穆巴勒兹丁·穆罕默德·مظفر数年间之状", "### ", 287),
    ("记穆巴勒兹丁·穆罕默德与铁阿拉伯之战", "### ", 308),
    ("记毛拉·谢姆斯丁·صائن·塞姆南卡迪", "### ", 317),
]
ins = {}
for t, lv, after in HEADS:
    ins.setdefault(after + 1, []).append(lv + t)
out = []
for i in range(1, 328):
    out.extend(ins.get(i, []))
    out.append(D[i])
open('translation/body/ch03.md', 'w', encoding='utf-8').write("\n\n".join(out) + "\n")
print("wrote", len(out))
