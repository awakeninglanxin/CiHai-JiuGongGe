# -*- coding: utf-8 -*-
"""生成「待补阳格」清单 CSV：按出现天数排序，附同族已收录条目与当前页面的误配结果。
不改动任何现有文件，只写 _build/待补阳格.csv
"""
import json, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, '_soul_rows.json'), encoding='utf-8'))
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
DB = D['SOUL_SCORE_DB']
N = rows['nd']

# 与 engine.js 的 lookupSoulScore 完全一致
KEYS = list(DB)


def classify(g):
    if g in DB:
        return 'exact', g
    if g.isdigit():
        st = str(int(g))
        if st != g and st in DB:
            return 'strip0', st
    s2 = g.lstrip('0')
    if s2 != g and s2 in DB:
        return 'strip0', s2
    for k in KEYS:
        if g.startswith(k) or k.startswith(g):
            return 'prefix', k
    if len(g) >= 4:
        p3 = g[:3]
        for k in KEYS:
            if k.startswith(p3):
                return 'pre3', k
    return 'null', None


def family(g):
    """同族：剥前导零 或 补前导零 后能在库里找到的条目"""
    cands = []
    s = g.lstrip('0')
    if s != g and s in DB:
        cands.append((s, '剥零同族'))
    for pad in ('0', '1', '2'):
        k = pad + g
        if k in DB:
            cands.append((k, '加' + pad + '同族'))
    s2 = g.lstrip('0')
    for pad in ('0', '1', '2'):
        k = pad + s2
        if k in DB and k not in [c[0] for c in cands]:
            cands.append((k, '剥零后加' + pad))
    return cands


lab = {x['g'] for x in rows['labelled']}
allr = sorted(rows['rows'], key=lambda r: -r['days'])

out = os.path.join(HERE, '待补阳格.csv')
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['序号', '阳格', '出现天数', '占比%', '路线', '构成', '合计(tot)',
                '同族已收录', '同族星级', '当前页面给的结果', '当前页面的判定路径'])
    n = 0
    for r in allr:
        if r['g'] in lab:
            continue
        n += 1
        if n > 120:
            break
        how, key = classify(r['g'])
        if key:
            cur = DB[key]
            curtxt = f"{key} {cur['stars']} {cur['name']}"
        else:
            curtxt = '（无结果）'
        fam = family(r['g'])
        famtxt = '；'.join(f'{k}（{lab2}）' for k, lab2 in fam) if fam else ''
        famstars = '；'.join(DB[k]['stars'] for k, _ in fam) if fam else ''
        w.writerow([n, r['g'], r['days'], round(100.0 * r['days'] / N, 2), r['route'],
                    '|'.join(str(p) for p in r['parts']), r['tot'],
                    famtxt, famstars, curtxt, how])
print('写出', out, '行数', n - 1 if n else 0)

# 同时打印「当前误配最严重」的 12 条，供回复引用
bad = [r for r in allr if classify(r['g'])[0] in ('prefix', 'pre3')][:12]
print('\n最严重的 12 条误配：')
for r in bad:
    how, key = classify(r['g'])
    cur = DB[key]
    print(f"  {r['g']:11s} {r['days']:5d}天 → {key} {cur['stars']} {cur['name']}  [{how}]")
