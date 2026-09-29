#!/usr/bin/env python3
"""组装 ch02.md：按源块序号 1:1 写出译文并插入标题。"""
D = {}
_fixed = 'preprocessing/draft/ch02_fixed.py'
import os as _os
if _os.path.exists(_fixed):
    ns = {}
    exec(open(_fixed, encoding='utf-8').read(), ns)
    D.update(ns['D'])
else:
    for f in ['ch02_1.py', 'ch02_2.py', 'ch02_3.py', 'ch02_4.py', 'ch02_5.py',
              'ch02_6.py', 'ch02_7.py', 'ch02_8.py', 'ch02_9.py', 'ch02_10.py',
              'ch02_11.py']:
        ns = {}
        exec(open('/tmp/' + f, encoding='utf-8').read(), ns)
        D.update(ns['D'])

missing = [i for i in range(1, 395) if i not in D]
assert not missing, missing

HEADS = [
    ("回历 728–736 年之事", "# ", 0),
    ("回历 728 年之事", "## ", 9), ("按语", "### ", 9),
    ("记楚班埃米尔诸子及其状", "### ", 20),
    ("回历 730 年之事", "## ", 114), ("按语", "### ", 114),
    ("记马立克·吉亚斯丁之卒及其诸子之状", "### ", 117),
    ("记此数年间察合台部之状", "### ", 123),
    ("回历 731 与 732 年之事", "## ", 130),
    ("回历 733 年之事", "## ", 135),
    ("回历 734 年之事", "## ", 141),
    ("回历 735 年之事", "## ", 144),
    ("回历 736 年之事", "## ", 148), ("按语", "### ", 148),
    ("记幸运之主殿下之事迹与圣言之要", "### ", 177),
    ("记阿尔帕汗之王权", "### ", 299),
    ("记穆萨汗之王权及其状", "### ", 318),
    ("记谢赫·哈桑·诺扬埃米尔之起——人称大谢赫·哈桑", "### ", 365),
    ("记幸运之主诞生之年呼罗珊之状", "### ", 388),
]
ins = {}
for t, lv, after in HEADS:
    ins.setdefault(after + 1, []).append(lv + t)
out = []
for i in range(1, 395):
    out.extend(ins.get(i, []))
    out.append(D[i])
open('translation/body/ch02.md', 'w', encoding='utf-8').write("\n\n".join(out) + "\n")
print("wrote", len(out))
