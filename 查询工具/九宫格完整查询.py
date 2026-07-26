# -*- coding: utf-8 -*-
"""
九宫格完整查询工具 v3.0
集成：阳格/阴格/子时/半补/四清跌落路径
卢先生体系 · 慈海九宫格

使用方式：
  python 九宫格完整查询.py 1991 8 16
  python 九宫格完整查询.py 1991 8 16 9  # 包含时辰
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

try:
    import lu_fall_paths as fp
    HAS_FALL_PATHS = True
except ImportError:
    HAS_FALL_PATHS = False

from collections import Counter

# ─────────────────────────────────────────
# 核心算法（来自 nine_palace_complete_final.py）
# ─────────────────────────────────────────

def ds(n):
    return sum(int(c) for c in str(n) if c.isdigit())

def rds(n):
    s = n
    while s >= 10:
        s = ds(s)
    return s

def yang_grid_calc(year, month, day):
    po = [int(c) for c in str(year)] + [int(c) for c in str(month).zfill(2)] + [int(c) for c in str(day).zfill(2)]
    total = sum(po)
    if total >= 10:
        intermediates = []
        if total >= 10:
            intermediates.append(total)
        s = total
        while s >= 10:
            s = ds(s)
            if s >= 10:
                intermediates.append(s)
        main = s
        cnt = Counter(po)
        upgraded = []
        for digit, count in cnt.items():
            if count >= 3:
                for _ in range(count // 3):
                    upgraded.append(digit)
        upgraded = sorted(upgraded)
        aux_seq = upgraded + intermediates + [main]
        aux_str = ''.join(str(x) for x in aux_seq)
        aux_cnt = Counter(list(aux_str))
        new_mains = []
        for digit, count in aux_cnt.items():
            if count >= 3:
                new_mains.append(int(digit))
        final_parts = upgraded + intermediates + [main]
        for nm in new_mains:
            if nm != main:
                final_parts.append(nm)
        result_str = ''.join(str(p) for p in final_parts)
        return int(result_str) if result_str else main
    else:
        main = total
        cnt = Counter(po)
        upgraded = []
        for digit, count in cnt.items():
            if count >= 3:
                for _ in range(count // 3):
                    upgraded.append(digit)
        upgraded = sorted(upgraded)
        year_aux = ds(year)
        month_aux = ds(month)
        day_aux = ds(day)
        base_aux = [year_aux, month_aux, day_aux]
        parts = upgraded + base_aux + [main]
        return ''.join(str(p) for p in parts)

def yin_grid_calc(year, month, day):
    try:
        from lunarcalendar import Converter, Solar, Lunar
        lunar_date = Converter.Solar2Lunar(Solar(year, month, day))
        ly, lm, ld = lunar_date.year, lunar_date.month, lunar_date.day
        return yang_grid_calc(ly, lm, ld)
    except Exception:
        return yang_grid_calc(year, month, day)

def half_fill_calc(birth_hour):
    """半补计算：时辰→五行→数字映射"""
    hour_branch_map = {
        23:('子', '水', 0),  0:('子', '水', 0),
        1:('丑', '土', 1),   2:('丑', '土', 1),
        3:('寅', '木', 4),   4:('寅', '木', 4),
        5:('卯', '木', 4),   6:('卯', '木', 4),
        7:('辰', '土', 7),   8:('辰', '土', 7),
        9:('巳', '火', 3),   10:('巳', '火', 3),
        11:('午', '火', 3),  12:('午', '火', 3),
        13:('未', '土', 7),  14:('未', '土', 7),
        15:('申', '金', 12), 16:('申', '金', 12),
        17:('酉', '金', 12), 18:('酉', '金', 12),
        19:('戌', '土', 7),  20:('戌', '土', 7),
        21:('亥', '水', 0),  22:('亥', '水', 0),
    }
    branch, wuxing, num = hour_branch_map.get(birth_hour, ('子', '水', 0))
    return branch, wuxing, num

def hour_branch(birth_hour):
    branch_map = {
        23:'子', 0:'子', 1:'丑',  2:'丑',
        3:'寅',  4:'寅', 5:'卯',  6:'卯',
        7:'辰',  8:'辰', 9:'巳',  10:'巳',
        11:'午', 12:'午', 13:'未', 14:'未',
        15:'申', 16:'申', 17:'酉', 18:'酉',
        19:'戌', 20:'戌', 21:'亥', 22:'亥',
    }
    return branch_map.get(birth_hour, '子')

def wuxing_of(digit):
    """数字→五行属性"""
    w = {1:'金', 2:'水', 3:'火', 4:'木', 5:'土',
         6:'水', 7:'土', 8:'金', 9:'火', 0:'土'}
    return w.get(int(digit) % 10 if int(digit) != 0 else 5, '?')

def wuxing_summary(grid_str):
    """统计各行能量"""
    cnts = Counter(str(grid_str))
    result = {}
    for d, c in cnts.items():
        wx = wuxing_of(d)
        result[wx] = result.get(wx, 0) + c
    return result

def missing_numbers(grid_str, po_list):
    """缺数计算"""
    all_digits = set(range(10))
    used = set(int(d) for d in str(grid_str))
    po_set = set(po_list)
    return all_digits - used - po_set

# ─────────────────────────────────────────
# 四清跌落路径信息（集成）
# ─────────────────────────────────────────

FALL_SUMMARY = """
━━━━━━━━━━━━━━━━━━━━━━━━
【四清跌落路径总纲】
━━━━━━━━━━━━━━━━━━━━━━━━

【二清路径】28101→1268→268→358→325→235→145
  玉皇(天蓬元帅)→工程师(刑天)→猪八戒→猎户魔王→唐僧→无名唐僧→婴儿
  核心课题：权威与公正→汲取教训→欲望管理→权力管理→情绪与亲密关系→无我服务

【三清/财神路径】37101→347→314→224→134
  财神玉皇→牛魔王→孵蛋者→迷路弥勒佛→跌落态
  核心课题：对物质的恐惧→放下控制→创造的正确使用→从迷失中找方向

【一清路径】19101→37101→456101（未跌落）
  西王母→九天玄女→轮值官
  注：一清团队未跌落，在事故前已集体扬升

【接引道人路径】1303→456101→0224/1224/2224
  接引道人→轮值官→迷路者（情感纠葛与物质细节中迷失）
"""

# ─────────────────────────────────────────
# 查询函数
# ─────────────────────────────────────────

def query_bazi(year, month, day, hour=None):
    """完整九宫格查询"""
    print(f"\n{'='*50}")
    print(f"  卢先生体系 · 慈海九宫格 完整查询")
    print(f"{'='*50}")

    yang = yang_grid_calc(year, month, day)
    yin = yin_grid_calc(year, month, day)

    print(f"\n▶ 公历：{year}年{month:02d}月{day:02d}日")
    try:
        from lunarcalendar import Converter, Solar
        ld = Converter.Solar2Lunar(Solar(year, month, day))
        print(f"▶ 农历：{ld.year}年{ld.month:02d}月{ld.day:02d}日")
    except:
        pass

    if hour is not None:
        branch, wx, num = half_fill_calc(hour)
        print(f"▶ 时辰：{hour:02d}时（{branch}时）")
        print(f"▶ 半补：{num}（{wx}）")

    print(f"\n{'─'*40}")
    print(f"  阳格：{yang}")
    print(f"  阴格：{yin}")

    if hour is not None:
        branch = hour_branch(hour)
        print(f"  时支：{branch}")

    print(f"\n{'─'*40}")
    print(f"  【五行能量分布】")
    yang_wx = wuxing_summary(str(yang))
    for wx, cnt in sorted(yang_wx.items(), key=lambda x: -x[1]):
        bar = '█' * cnt
        print(f"  {wx}：{bar} ({cnt}个)")

    print(f"\n{'─'*40}")
    print(f"  【缺数分析】")
    po = [int(c) for c in str(year)] + [int(c) for c in str(month).zfill(2)] + [int(c) for c in str(day).zfill(2)]
    miss = missing_numbers(str(yang), po)
    if miss:
        miss_wx = [wuxing_of(m) for m in miss]
        print(f"  阳格缺：{', '.join(str(m) for m in sorted(miss))} → {', '.join(miss_wx)}")
    else:
        print(f"  阳格不缺数")

    # 阴阳同格检测
    if str(yang) == str(yin):
        print(f"\n  ⚠️ 阴阳同格！能量高度聚焦，课题集中。")
        if HAS_FALL_PATHS:
            print(fp.get_fall_info("阴阳同格"))

    # 特殊组合：1325/347
    if yang == 1325 and yin == 347:
        print(f"\n  ⚠️ 唐僧与牛魔王组合！")
        if HAS_FALL_PATHS:
            print(fp.get_fall_info("1325_347"))

    # 附加四清信息
    print(FALL_SUMMARY)

    print(f"{'='*50}\n")
    return yang, yin


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4]) if len(sys.argv) >= 5 else None
        query_bazi(year, month, day, hour)
    else:
        print(__doc__)
        print("\n用法示例：")
        print("  python 九宫格完整查询.py 1991 8 16      # 1991年8月16日")
        print("  python 九宫格完整查询.py 1991 8 16 9    # 1991年8月16日巳时")
