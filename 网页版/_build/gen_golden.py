# -*- coding: utf-8 -*-
"""生成黄金样本：用 Python 原引擎（lunarcalendar 版）算出结果，供 JS 比对"""
import json, os, sys, random
from datetime import date, timedelta

EDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "核心引擎"))
sys.path.insert(0, EDIR)
import nine_palace_core_v5 as V5

HERE = os.path.dirname(os.path.abspath(__file__))
SHICHEN = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时',
           '申时', '酉时', '戌时', '亥时', '前子时', '后子时']
CUR_YEAR = 2026


def one(ds, sc, g):
    r = V5.calc(ds, sc, g)
    out = {
        "date": ds, "shichen": sc, "gender": g,
        "type": r.get("类型"),
        "yang": r.get("阳格"), "yin": r.get("阴格"),
        "yangQue": r.get("阳缺"), "yinQue": r.get("阴缺"),
        "half": r.get("半补"),
        "po": r.get("魄"), "up": r.get("up"), "route": r.get("路线"),
    }
    if "阳格1" in r:
        out.update({
            "yang1": r.get("阳格1"), "yin1": r.get("阴格1"),
            "yangQue1": r.get("阳缺1"), "yinQue1": r.get("阴缺1"),
            "half1": r.get("半补1"), "adjDate": r.get("调整日期"), "note": r.get("说明"),
        })
    lc = V5.calc_life_cycle(int(ds.replace('/', '-').split('-')[0]), g, CUR_YEAR)
    out["life"] = {k: lc[k] for k in ['年龄', '当前阶段', '当前类型', '当前阶段开始',
                                      '当前阶段结束', '下次换魂', '下次换魂年龄', '距下次换魂']}
    return out


def main():
    random.seed(20261027)
    cases = []

    # 1) 全 14 时辰 × 3 个日期 × 2 性别
    for ds in ['1991/12/24', '2000/01/01', '2026/03/25']:
        for sc in SHICHEN:
            for g in ('male', 'female'):
                cases.append((ds, sc, g))

    # 2) 跨 1900-2100 随机 600 个日期
    span = (date(2100, 12, 31) - date(1900, 1, 1)).days
    for _ in range(600):
        d = date(1900, 1, 1) + timedelta(days=random.randrange(span + 1))
        cases.append((d.strftime('%Y/%m/%d'), random.choice(SHICHEN), random.choice(['male', 'female'])))

    # 3) 闰月密集区（2020 闰四月 / 2023 闰二月 / 2025 闰六月 / 2033 闰十一月）
    for ds in ['2020/05/23', '2020/06/20', '2023/03/22', '2025/07/25', '2033/12/22']:
        for sc in ('巳时', '前子时'):
            cases.append((ds, sc, 'female'))

    # 4) 边界
    for ds in ['1900/01/01', '1900/01/02', '2100/12/30', '2100/12/31',
               '1999/12/31', '2000/02/29', '2100/02/28']:
        cases.append((ds, '午时', 'male'))

    # 5) 十位数总和特殊（tot==10 且 up>=2 → MultiSoul）
    for ds in ['1990/10/10', '2000/01/09', '1988/11/11', '1991/01/08']:
        cases.append((ds, '卯时', 'male'))

    out = []
    for ds, sc, g in cases:
        try:
            out.append(one(ds, sc, g))
        except Exception as e:
            out.append({"date": ds, "shichen": sc, "gender": g, "error": "%s: %s" % (type(e).__name__, e)})

    # 单格/组合解读查询也验一遍（用查询工具真正的匹配函数）
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "查询工具")))
    import grid_interpretations as G
    from nine_palace_query import get_combo_interpretation, get_single_grid_info

    combos = []
    for yg, ig in [('1325', '347'), ('347', '347'), ('369', '369'), ('325', '325'),
                   ('028101', '28101'), ('0219101', '19101'), ('22', '0202'), ('666336', '666336')]:
        c = get_combo_interpretation(yg, ig)
        combos.append({'yg': yg, 'ig': ig, 'res': {
            'hit': c is not None,
            'name': c.get('combo_name') if c else None,
            'isPure': bool(c.get('is_pure')) if c else None,
        }})

    singles = []
    for gs in ['0202', '28101', '19101', '0219101', '37101', '437', '999']:
        s = get_single_grid_info(gs)
        singles.append({'g': gs, 'res': {'hit': s is not None, 'name': s.get('name') if s else None}})

    dst = os.path.join(HERE, 'golden.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump({"cases": out, "combos": combos, "singles": singles,
                   "curYear": CUR_YEAR}, f, ensure_ascii=False)
    print("黄金样本 %d 例 | 组合 %d | 单格 %d → %s (%d 字节)"
          % (len(out), len(combos), len(singles), dst, os.path.getsize(dst)))


if __name__ == '__main__':
    main()
