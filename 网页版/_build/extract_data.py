# -*- coding: utf-8 -*-
"""
从 查询工具 / 核心引擎 抽取全部数据库 → data.json（供网页内嵌）

原则：只抽取、不改写。任何字段原样搬运，便于日后源码更新后重新生成。
"""
import json, os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
QDIR = os.path.join(ROOT, "查询工具")
EDIR = os.path.join(ROOT, "核心引擎")
for p in (QDIR, EDIR):
    sys.path.insert(0, p)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main():
    sys.path.insert(0, EDIR)
    import nine_palace_core_v5 as V5
    import grid_interpretations as G
    import lu_fall_paths as L
    bao = load_mod("bao_report", os.path.join(EDIR, "完整综合命理报告v3.9.py"))
    sl = load_mod("shiliao", os.path.join(EDIR, "食疗动功生成器v3.3.py"))
    nhx = load_mod("nihaixia", os.path.join(EDIR, "倪海厦中医建议生成器.py"))
    ty = load_mod("tongyong", os.path.join(EDIR, "通用报告生成器.py"))
    wp = load_mod("weapon", os.path.join(EDIR, "weapon_rules.py"))

    # 城市经纬度：两处合并，通用版更全 → 以其为底，倪海厦版补齐
    city = dict(ty.CITY_COORDS)
    for k, v in nhx.CITY_COORDS.items():
        city.setdefault(k, v)

    # 缺格诊断（硬编码在 v3.9 报告函数内）
    zangfu_simple = {"0": "小肠", "1": "肺", "2": "大肠", "3": "心", "4": "肝",
                     "5": "胆", "6": "肾", "7": "胃", "8": "脾", "9": "膀胱"}
    que_fix = {"0": "分清泌浊", "1": "多做深呼吸", "2": "腹式呼吸+蔬菜配方",
               "3": "通心轮（小白瓶）", "4": "A杯+蔬菜配方", "5": "宁化府饺子醋",
               "6": "黑米套餐+动功", "7": "小绿瓶+情感和谐", "8": "铁棍山药+忌甜食",
               "9": "开天门+黑豆黑木耳"}

    # 频率：不用仓库里的 grid_frequency_data.json（阳/阴两侧合计 435,004 vs 69,762，
    # 分母不统一，且未记录区间），改用 recount_freq.py 按日实算的结果。
    freq = json.load(open(os.path.join(HERE, "freq.json"), encoding="utf-8"))
    joint = json.load(open(os.path.join(HERE, "freq_joint.json"), encoding="utf-8"))

    out = {
        "_meta": {
            "生成时间": "",
            "来源": ["查询工具/grid_interpretations.py", "查询工具/lu_fall_paths.py",
                    "核心引擎/nine_palace_core_v5.py", "核心引擎/完整综合命理报告v3.9.py",
                    "核心引擎/食疗动功生成器v3.3.py", "核心引擎/倪海厦中医建议生成器.py",
                    "核心引擎/通用报告生成器.py", "核心引擎/weapon_rules.py",
                    "grid_frequency_data.json"],
        },
        # ── 灵魂 / 解读 ──
        "SOUL_SCORE_DB": G.SOUL_SCORE_DB,
        "SOUL_DB": V5.SOUL_DB,
        "COMBO": G.COMBO_INTERPRETATIONS,
        "SINGLE": G.SINGLE_GRID_INTERPRETATIONS,
        "FALL_STRUCT": G.FALL_PATHS,
        "FALL_DOC": L.FALL_PATHS,
        # ── 阴阳 / 周期 ──
        "DIGIT_YIN": V5.DIGIT_YIN,
        "DIGIT_YANG": V5.DIGIT_YANG,
        "CYCLE_PARAMS": V5.CYCLE_PARAMS,
        "HALF_MAP": nhx.SHICHEN_LIST and {
            "申时": "12", "酉时": "12", "寅时": "45", "卯时": "45",
            "亥时": "06", "子时": "06", "前子时": "06", "后子时": "06",
            "巳时": "3", "午时": "3", "辰时": "789", "戌时": "789",
            "丑时": "789", "未时": "789"},
        # ── 脏腑 / 中医 ──
        "ZANGFU_SIMPLE": zangfu_simple,
        "QUE_FIX": que_fix,
        "ZANGFU_MAP": nhx.ZANGFU_MAP,
        "SIX_DIVISION": nhx.SIX_DIVISION_MAP,
        "NI_DIET": nhx.NI_FORMULA_DIET,
        "NI_EXERCISE": nhx.NI_EXERCISE,
        "CITY": city,
        # ── 食疗动功 ──
        "DIGIT_ORGAN": sl.DIGIT_ORGAN,
        "REMEDY_DB": sl.REMEDY_DB,
        "FOOD_DB": sl.FOOD_DB,
        "DG_CORE": sl.DONG_GONG_CORE,
        "DG_BADUANJIN": sl.DONG_GONG_BADUANJIN,
        "DG_HUXI": sl.DONG_GONG_HUXI,
        "DG_LIANHUA": sl.DONG_GONG_LIANHUA,
        "PROHIBIT": sl.GENERAL_PROHIBIT,
        "DAILY": sl.DAILY_EXECUTION,
        # ── 图腾 / 法器 ──
        "WEAPON": wp.WEAPON_MAP,
        "ROLE_REF": wp.ROLE_REFERENCES,
        # ── 统计 ──
        "FREQ": {"start": freq["start"], "end": freq["end"], "days": freq["days"],
                 "yang": freq["yang"], "yin": freq["yin"]},
        "JOINT": joint,
    }

    from datetime import datetime
    out["_meta"]["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 体积体检
    print("%-16s %s" % ("键", "条目/长度"))
    for k, v in out.items():
        if k == "_meta":
            continue
        if isinstance(v, dict):
            print("  %-14s %d 键" % (k, len(v)))
        elif isinstance(v, list):
            print("  %-14s %d 项" % (k, len(v)))
        else:
            print("  %-14s %r" % (k, v))

    # 两套灵魂库的一致性体检（信息性）
    a, b = set(G.SOUL_SCORE_DB), set(V5.SOUL_DB)
    print("\n灵魂库：SOUL_SCORE_DB=%d  SOUL_DB=%d  交集=%d  仅SCORE=%d  仅V5=%d"
          % (len(a), len(b), len(a & b), len(a - b), len(b - a)))

    dst = os.path.join(HERE, "data.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("\n已写 %s  (%d 字节)" % (dst, os.path.getsize(dst)))


if __name__ == "__main__":
    main()
