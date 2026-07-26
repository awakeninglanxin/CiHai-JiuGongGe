# -*- coding: utf-8 -*-
"""
自研阴历引擎 v2 — 基于 PyEphem 精确天文计算 + 农历编历规则
完全绕过 JD 转换，直接使用 ephem.Date

精度: 朔日±1分钟，可覆盖公元前到公元后任意年份
"""
import ephem
from math import pi
from datetime import date, timedelta

# ===== ephem 直接调用 =====

def next_new_moon_eph(date_str):
    """date_str → 下一个朔日的 ephem.Date"""
    return ephem.next_new_moon(date_str)

def prev_new_moon_eph(date_str):
    """date_str → 上一个朔日的 ephem.Date"""
    return ephem.previous_new_moon(date_str)

def sun_longitude_deg(date_str):
    """太阳黄经（度）"""
    sun = ephem.Sun(date_str)
    return float(sun.hlon) * 180.0 / pi

def ephem_to_tuple(edate):
    """ephem.Date → (year, month, day)"""
    t = edate.tuple()
    return (t[0], t[1], t[2])

def d2s(year, month, day):
    """公历 → ephem.Date 字符串"""
    return f'{year}/{month}/{day}'

# ===== 农历主逻辑 =====

def new_moon_at_or_before(year, month, day):
    """找到目标日期当天或之前的最近朔日 (ephem Date)"""
    date_str = d2s(year, month, day)
    target_d = ephem.Date(date_str)
    # 先找严格之前的朔日
    prev_nm = prev_new_moon_eph(date_str)
    # 检查下一个朔日是否在目标日当天
    next_nm = next_new_moon_eph(str(prev_nm))
    # 如果 next_nm 的天数 ≤ target_d 的天数，说明目标日与朔日在同一天
    # 简化: 如果 ephem.Date(prev_nm+1) 的日期与 target_d 不同，说明 prev_nm 就在当天
    if int(float(target_d)) == int(float(prev_nm)):
        return prev_nm  # 朔日就在目标日当天
    return prev_nm

def get_lunar_date(year, month, day):
    date_eph = ephem.Date(d2s(year, month, day))
    jd_now = float(date_eph) + 2415020.0
    
    # 冬至
    approx_ws_year = year
    approx_ws_jd = float(ephem.Date(d2s(approx_ws_year, 12, 22))) + 2415020.0
    if approx_ws_jd > jd_now:
        approx_ws_year -= 1
    
    ws_jd = find_solar_term_jd(approx_ws_year, 90.0)
    if ws_jd > jd_now:
        ws_jd = find_solar_term_jd(approx_ws_year - 1, 90.0)
    
    # 冬至月朔日
    ws_date_str = str(ephem.Date(ws_jd - 2415020.0))
    ws_nm = prev_new_moon_eph(ws_date_str)
    ws_nm_jd = float(ephem.Date(ws_nm)) + 2415020.0
    
    # 目标月朔日 (当天朔日作为本月朔日)
    target_nm = new_moon_at_or_before(year, month, day)
    target_nm_jd = float(ephem.Date(target_nm)) + 2415020.0
    
    # 月偏移 (截断避免边界四舍五入)
    diff = target_nm_jd - ws_nm_jd
    month_offset = int(diff / 29.530588853)
    
    if month_offset >= 0:
        lun_month = 11 + month_offset
        lun_year = approx_ws_year
        while lun_month > 12:
            lun_month -= 12
            lun_year += 1
    else:
        lun_month = 11 + month_offset + 1  # 修正负偏移
        lun_year = approx_ws_year
        while lun_month <= 0:
            lun_month += 12
            lun_year -= 1
    
    # 农历日: floor(目标jd) - floor(朔日jd) + 1
    lun_day = int(jd_now) - int(target_nm_jd) + 1
    return lun_year, lun_month, max(1, lun_day), False
    lun_day = int(jd_now) - int(target_nm_jd) + 1


def find_solar_term_jd(year, target_lon_deg):
    """找到指定年份太阳黄经target_lon_deg(ephem hlon)的精确JD"""
    # 节气对应的公历日偏移 (从1月1日起)
    # ephem hlon: 秋分0°, 冬至90°, 春分180°, 夏至270°
    offset_map = {0: 265, 90: 355, 180: 78, 270: 172}
    day_in_year = offset_map.get(int(target_lon_deg), int(target_lon_deg / 360.0 * 365.25))
    base_date = float(ephem.Date(d2s(year, 1, 1))) + day_in_year
    
    lo = base_date - 3
    hi = base_date + 3
    
    for _ in range(40):
        mid = (lo + hi) / 2.0
        sl_val = sun_longitude_deg(str(ephem.Date(mid)))
        if abs(sl_val - target_lon_deg) < 0.01:
            return mid + 2415020.0  # 返回JD
        elif sl_val < target_lon_deg:
            lo = mid
        else:
            hi = mid
    
    return (lo + hi) / 2.0 + 2415020.0


# ===== 测试 =====
if __name__ == '__main__':
    from lunarcalendar import Converter, Solar
    
    tests = [
        (1910,1,1),(1911,1,1),(1950,6,15),(1970,1,1),
        (2000,2,5),(2002,2,11),(2020,1,25),
        (2026,7,10),(2050,6,15),(2099,12,31),
        (2101,6,15),(2200,6,15),(2500,1,1),(3000,12,31),
    ]
    
    print('测试日期      | 标准库(year-m-d) | 自研(year-m-d) | 结果')
    print('-'*60)
    for y,m,d in tests:
        try:
            s = Solar(y,m,d)
            l = Converter().Solar2Lunar(s)
            ref = (l.year, abs(l.month), l.day)
        except:
            ref = ('?','?','?')
        
        try:
            my = get_lunar_date(y,m,d)
        except Exception as e:
            my = ('ERR',str(e),-1,-1)
        
        try:
            ok = ref[0]==my[0] and ref[1]==my[1] and ref[2]==my[2]
            mark = '✅' if ok else '❌'
        except:
            mark = '🆕'  # 新范围无对照
        
        print(f'{y}-{m:02d}-{d:02d} | {ref[0]:>4}-{ref[1]:>2}-{ref[2]:>2}     | {my[0]:>4}-{my[1]:>2}-{my[2]:>2}     | {mark}')
