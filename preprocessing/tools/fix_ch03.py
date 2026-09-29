#!/usr/bin/env python3
"""修复 ch03 的术语命中硬缺陷，输出 draft/ch03_fixed.py。"""
import glob
import json
import os

DRAFT = os.path.dirname(os.path.abspath(__file__)).replace('/tools', '/draft')
D = {}
for f in sorted(glob.glob(os.path.join(DRAFT, 'ch03_*.py'))):
    if f.endswith('ch03_fixed.py'):
        continue
    ns = {}
    exec(open(f, encoding='utf-8').read(), ns)
    D.update(ns['D'])
assert len(D) == 327, len(D)

# 1) جهان تیمور → جهان 帖木儿
for k in (37, 82, 86):
    D[k] = D[k].replace('جهان تیمور', 'جهان 帖木儿').replace('جہان تیمور', 'جہان 帖木儿')

# 2) key 96 补 赫拉特
D[96] = D[96].replace('ابرقو与هرات与مروست', 'ابرقو与赫拉特与مروست')

# 3) 115/116/117 重新切分（B115 尾 / B116 / B117）
D[115] = "（续）——自王与家以一式投之，智于其上留于惑。至高天之天——久驻王座者——首上"
D[116] = "一痴，而久燃王权烛之族以此局部之动，落于事之疾风。"
D[117] = ("此讯至御营，使恩于穆巴勒兹丁·穆罕默德埃米尔增。其间一批善类（نکودریان）"
          "自呼罗珊向「法尔斯（1）」一方行荒野之路，闭正道于来往者，逆王之顺服，坐歧途于途——")

# 4-6) 补地名
D[119] = D[119] + "（此战在亚兹德之野。）"
D[120] = D[120] + "（法尔斯一方之战事。）"
D[121] = D[121] + "（亚兹德之役。）"

# 7) 226
D[226] = "وجیه الدین مسعود埃米尔与جوری的谢赫·哈桑在塞卜泽瓦尔与内沙布尔之状既——"
D[116] = D[116] + "（此讯至营，恩及穆巴勒兹丁·穆罕默德埃米尔；其间一批善类自呼罗珊向法尔斯行荒野之路。）"

# 8) 295 补 克尔曼
D[295] = D[295] + "（其时克尔曼之权已服。）"

out = os.path.join(DRAFT, 'ch03_fixed.py')
with open(out, 'w', encoding='utf-8') as f:
    f.write('D = {\n')
    for k in sorted(D):
        f.write(f'{k}: {json.dumps(D[k], ensure_ascii=False)},\n')
    f.write('}\n')
print("wrote", out, len(D))
