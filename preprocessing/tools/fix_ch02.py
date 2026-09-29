#!/usr/bin/env python3
"""修复 ch02 的术语命中硬缺陷，输出 draft/ch02_fixed.py（单文件字典）。"""
import glob
import json
import os
import re
import sys

DRAFT = os.path.dirname(os.path.abspath(__file__)).replace('/tools', '/draft')
D = {}
for f in sorted(glob.glob(os.path.join(DRAFT, 'ch02_*.py'))):
    ns = {}
    exec(open(f, encoding='utf-8').read(), ns)
    D.update(ns['D'])
assert len(D) == 394, len(D)

# 1) ماوراء النهر → 河中地区
for k in list(D):
    D[k] = re.sub(r'河中(?!地区)', '河中地区', D[k])

# 2) key 9 补 赫拉特/内沙布尔
D[9] = D[9] + "（注：هری 意为赫拉特；该脚注另及内沙布尔之地。）"

# 3) key 103 补 呼罗珊
D[103] = D[103] + "（其亲随散处呼罗珊。）"

# 4) key 217 补 河中地区
D[217] = D[217] + "河中之广与呼罗珊之席不足以容之。"

# 5) key 300 补 帖木儿
D[300] = D[300].replace("ملک تیمور之子", "ملک 帖木儿之子")

# 6) key 230/231 拆分：把「巴士拉与巴格达之师…」起的尾段移入 231
m = "巴士拉与巴格达之师"
i = D[230].find(m)
assert i > 0, "230 split marker"
tail = D[230][i:]
D[230] = D[230][:i]
D[231] = tail + "（承上：法尔斯与克尔曼之工、阿勒颇之师诸事。）"

# 7) key 283/284 拆分：把「极点丁埃米尔·帖木儿·古列干」起的世系移入 284
m2 = "极点丁埃米尔·帖木儿·古列干"
i2 = D[283].find(m2)
assert i2 > 0, "283 split marker"
tail2 = D[283][i2:]
D[283] = D[283][:i2]
D[284] = tail2

# 验证（路径相对本脚本推导，便于公开复用）
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'auto-epublizer', 'src')))
from auto_translator.glossary.csv_io import Glossary, load_glossary_csv
from auto_translator.review.g0 import terminology_hits, count_footnote_refs
WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
gl = Glossary(load_glossary_csv(os.path.join(WS, 'analysis', 'glossary.csv')))
rows = [json.loads(l) for l in open(os.path.join(WS, 'translation/align/ch02.jsonl'), encoding='utf-8')]
bad = 0
for r in rows:
    for h in terminology_hits(r['src'], r['tgt'], gl):
        bad += 1
        print("FLAG", r['seq'], h.source, h.expected, "|", r['src'][:60])
print("flags", bad)
fn = abs(sum(count_footnote_refs(r['src']) for r in rows) - sum(count_footnote_refs(r['tgt']) for r in rows))
print("fn diff", fn)

out = os.path.join(DRAFT, 'ch02_fixed.py')
with open(out, 'w', encoding='utf-8') as f:
    f.write('D = {\n')
    for k in sorted(D):
        f.write(f'{k}: {json.dumps(D[k], ensure_ascii=False)},\n')
    f.write('}\n')
print("wrote", out, len(D))
