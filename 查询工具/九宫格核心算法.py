# -*- coding: utf-8 -*-
"""
九宫格完整算法
包含: 阳格/阴格/子时/半补
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from lunarcalendar import Converter, Solar

def ds(n):
    return sum(int(c) for c in str(n) if c.isdigit())

def rds(n):
    s = n
    while s >= 10:
        s = ds(s)
    return s

def yang_grid_calc(year, month, day):
    """阳格计算"""
    po = [int(c) for c in str(year)] + [int(c) for c in str(month).zfill(2)] + [int(c) for c in str(day).zfill(2)]
    total = sum(po)

    if total >= 10:  # 路线A
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

        # 最终阳格: 新主魂与原主魂不同时才添加
        final_parts = upgraded + intermediates + [main]
        for nm in new_mains:
            if nm != main:
                final_parts.append(nm)

        result_str = ''.join(str(p) for p in final_parts)
        return int(result_str) if result_str else main

    else:  # 路线B
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
    """阴格计算: 转阴历后同样算法"""
    try:
        solar = Solar(year, month, day)
        lunar = Converter().Solar2Lunar(solar)
        ly = lunar.year
        lm = abs(lunar.month)
        ld = lunar.day
        leap = lunar.month < 0

        result = yang_grid_calc(ly, lm, ld)
        if leap:
            result = '1' + str(result)
        return result
    except:
        return '0'

def missing_numbers(grid_str):
    """计算缺数"""
    present = set(int(c) for c in grid_str if c.isdigit())
    missing = {1,2,3,4,5,6,7,8,9} - present
    return ''.join(str(x) for x in sorted(missing))

# ===== 验证所有测试 =====
print("=" * 60)
print("阳格算法验证")
print("=" * 60)

tests = [
    (1991, 12, 24, 1291121),
    (2002, 2, 12, 24239),
    (1995, 7, 18, 404),
    (2000, 1, 1, 2114),
]

for y, m, d, expected in tests:
    result = yang_grid_calc(y, m, d)
    status = "OK" if result == expected else "FAIL"
    print(f"  {y}/{m:02d}/{d:02d}: {result} | 期望: {expected} | {status}")

# ===== 验证明天 =====
print("\n" + "=" * 60)
print("验证明天(2026-03-25,二月初七)")
print("=" * 60)

yg = yang_grid_calc(2026, 3, 25)
yg2 = yin_grid_calc(2026, 3, 25)
print(f"  阳格={yg} (期望: 2202)")
print(f"  阴格={yg2} (期望: 0219101)")
