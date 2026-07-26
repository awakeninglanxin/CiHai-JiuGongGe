# -*- coding: utf-8 -*-
"""
慈海九宫格查询工具 v3.0
=======================
桌面九宫格文件夹专用版。

v3.0 更新：
- 完整迁移到桌面九宫格查询与信息说明文件夹
- 集成 grid_interpretations.py 字典文件
- 查询结果后自动追加阴阳双格组合的详细解读
- 自动识别阴阳同格（纯格）并特殊说明能量纯粹性优势
- 自动显示跌落路径（若该格有跌落路径）

运行：
  python nine_palace_query.py
  按提示输入阳历生日和时辰即可。

也可以命令行运行：
  python nine_palace_query.py 1991/12/24 -s 卯时
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import os
import argparse
from collections import Counter
from datetime import datetime, timedelta

# 尝试导入 lunarcalendar
try:
    from lunarcalendar import Converter, Solar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False
    print("[警告] lunarcalendar 未安装，阴格计算将不可用。请运行: pip install lunarcalendar")

# 导入同级目录的字典文件
from grid_interpretations import (
    SOUL_SCORE_DB,
    FALL_PATHS,
    COMBO_INTERPRETATIONS,
    SINGLE_GRID_INTERPRETATIONS,
)

# ============================================================
# 核心算法（来自 nine_palace_complete_final.py）
# ============================================================

def ds(n):
    return sum(int(c) for c in str(n) if c.isdigit())

def rds(n):
    s = n
    while s >= 10:
        s = ds(s)
    return s

def yang_grid_calc(year, month, day):
    """阳格计算"""
    po = ([int(c) for c in str(year)]
          + [int(c) for c in str(month).zfill(2)]
          + [int(c) for c in str(day).zfill(2)])
    total = sum(po)

    if total < 10:  # 路线B
        main = total
        cnt = Counter(po)
        upgraded = []
        for digit, count in cnt.items():
            if count >= 3:
                upgraded.extend([digit] * (count // 3))
        upgraded = sorted(upgraded)
        year_aux = ds(year)
        month_aux = ds(month)
        day_aux = ds(day)
        base_aux = [year_aux, month_aux, day_aux]
        aux_str = ''.join(str(x) for x in upgraded + base_aux + [main])
        aux_cnt = Counter(aux_str)
        new_mains = []
        for digit, count in aux_cnt.items():
            if count >= 3 and int(digit) != main:
                new_mains.append(int(digit))
        parts = upgraded + base_aux + [main]
        for nm in new_mains:
            parts.append(nm)
        return ''.join(str(p) for p in parts)

    # 路线A
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
            upgraded.extend([digit] * (count // 3))
    upgraded = sorted(upgraded)

    if total == 10 and len(upgraded) >= 2:
        year_sum = ds(year)
        month_sum = ds(month)
        day_str = str(day).zfill(2)
        day_first = int(day_str[0])
        day_sum = ds(day)
        iv_val = intermediates[0] if intermediates else 0
        iv_first = int(str(iv_val)[0])
        return (str(upgraded[0]) + str(upgraded[1])
                + str(year_sum) + str(month_sum) + str(day_first)
                + str(main) + str(upgraded[0]) + str(iv_first) + str(day_sum))

    aux_parts = upgraded + intermediates + [main]
    aux_str = ''.join(str(x) for x in aux_parts)
    aux_cnt = Counter(aux_str)
    new_mains = []
    for digit, count in aux_cnt.items():
        if count >= 3 and int(digit) != main:
            new_mains.append(int(digit))
    final_parts = upgraded + intermediates + [main]
    for nm in new_mains:
        final_parts.append(nm)
    return ''.join(str(p) for p in final_parts)

def yin_grid_calc(year, month, day):
    """阴格计算：转阴历后同样算法"""
    if not HAS_LUNAR:
        return '0'
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

def missing_numbers(grid_str, po_set=None):
    """计算缺数"""
    if not grid_str or grid_str == '0':
        return '0123456789'
    present = set(int(c) for c in grid_str if c.isdigit())
    if po_set:
        present = present | po_set
    missing = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9} - present
    return ''.join(str(x) for x in sorted(missing))

HALF_SUPPLEMENT_MAP = {
    '申时': '12', '酉时': '12',
    '寅时': '45', '卯时': '45',
    '亥时': '06', '子时': '06', '前子时': '06', '后子时': '06',
    '巳时': '3', '午时': '3',
    '辰时': '789', '戌时': '789', '丑时': '789', '未时': '789',
}

def half_supplement(shichen):
    if not shichen or shichen in ['未知时辰', 'unknown', '']:
        return None
    return HALF_SUPPLEMENT_MAP.get(shichen, None)

def adjust_date_for_zishi(date_str, is_before_zishi=True):
    try:
        date = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d')
    except:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    if is_before_zishi:
        date += timedelta(days=1)
    return date.year, date.month, date.day

def get_lunar_po(year, month, day):
    if not HAS_LUNAR:
        return None
    try:
        lunar = Converter().Solar2Lunar(Solar(year, month, day))
        return set([int(c) for c in str(lunar.year)]
                   + [int(c) for c in str(abs(lunar.month)).zfill(2)]
                   + [int(c) for c in str(lunar.day).zfill(2)])
    except:
        return None

def calculate_nine_palace(date_str, shichen=None, is_before_zishi=True):
    try:
        date = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d')
    except:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    year, month, day = date.year, date.month, date.day
    is_zishi = shichen and '子时' in shichen
    half_sup = half_supplement(shichen) if shichen else None
    half_sup1 = half_sup if is_zishi else None

    result = {
        '日期': date_str,
        '时辰': shichen or '未知',
        '类型': '子时双格' if is_zishi else '普通阴阳双格',
    }

    if is_zishi:
        yang_grid_1 = yang_grid_calc(year, month, day)
        yin_grid_1 = yin_grid_calc(year, month, day)
        adj_year, adj_month, adj_day = adjust_date_for_zishi(date_str, is_before_zishi)
        yang_grid_2 = yang_grid_calc(adj_year, adj_month, adj_day)
        yin_grid_2 = yin_grid_calc(adj_year, adj_month, adj_day)
        yang_po_1 = set([int(c) for c in str(year)]
                         + [int(c) for c in str(month).zfill(2)]
                         + [int(c) for c in str(day).zfill(2)])
        yang_po_2 = set([int(c) for c in str(adj_year)]
                         + [int(c) for c in str(adj_month).zfill(2)]
                         + [int(c) for c in str(adj_day).zfill(2)])
        lunar_po_1 = get_lunar_po(year, month, day)
        lunar_po_2 = get_lunar_po(adj_year, adj_month, adj_day)
        soul_1 = lookup_soul_score(yang_grid_1)
        soul_2 = lookup_soul_score(yang_grid_2)
        result['阳格'] = yang_grid_1
        result['阴格'] = yin_grid_1
        result['阳缺'] = missing_numbers(yang_grid_1, yang_po_1)
        result['阴缺'] = missing_numbers(yin_grid_1, lunar_po_1)
        result['半补'] = half_sup
        result['灵魂积分'] = soul_1
        result['阳格1'] = yang_grid_2
        result['阴格1'] = yin_grid_2
        result['阳缺1'] = missing_numbers(yang_grid_2, yang_po_2)
        result['阴缺1'] = missing_numbers(yin_grid_2, lunar_po_2)
        result['半补1'] = half_sup1
        result['灵魂积分1'] = soul_2
        result['子时说明'] = (f'前子时：实际属于下一天({adj_year}/{adj_month:02d}/{adj_day:02d})'
                              if is_before_zishi
                              else f'后子时：属于当天({year}/{month:02d}/{day:02d})')
    else:
        yang_grid = yang_grid_calc(year, month, day)
        yin_grid = yin_grid_calc(year, month, day)
        yang_po = set([int(c) for c in str(year)]
                      + [int(c) for c in str(month).zfill(2)]
                      + [int(c) for c in str(day).zfill(2)])
        lunar_po = get_lunar_po(year, month, day)
        soul = lookup_soul_score(yang_grid)
        result['阳格'] = yang_grid
        result['阴格'] = yin_grid
        result['阳缺'] = missing_numbers(yang_grid, yang_po)
        result['阴缺'] = missing_numbers(yin_grid, lunar_po)
        result['半补'] = half_sup
        result['灵魂积分'] = soul

    return result

def lookup_soul_score(yang_grid):
    """查询阳格对应的灵魂积分信息"""
    yang_str = str(yang_grid)
    if yang_str in SOUL_SCORE_DB:
        return SOUL_SCORE_DB[yang_str]
    # 去除前导零后匹配（int方式处理如0219101→219101这种）
    stripped = str(int(yang_str)) if yang_str.isdigit() else yang_str.lstrip('0')
    if stripped and stripped != yang_str and stripped in SOUL_SCORE_DB:
        return SOUL_SCORE_DB[stripped]
    # 直接lstrip匹配（如2202→202，但2202本身也有条目则优先精确）
    stripped2 = yang_str.lstrip('0')
    if stripped2 and stripped2 != yang_str and stripped2 in SOUL_SCORE_DB:
        return SOUL_SCORE_DB[stripped2]
    for key in SOUL_SCORE_DB:
        if yang_str.startswith(key) or key.startswith(yang_str):
            return SOUL_SCORE_DB[key]
    if len(yang_str) >= 4:
        prefix = yang_str[:4]
        for key in SOUL_SCORE_DB:
            if key.startswith(prefix[:3]):
                return SOUL_SCORE_DB[key]
    return None

def get_combo_interpretation(yang_grid, yin_grid):
    """获取阴阳双格组合的详细解读"""
    yang_str = str(yang_grid)
    yin_str = str(yin_grid)
    # 去除前导零标准化
    def norm(s):
        return str(int(s)) if s.isdigit() else s.lstrip('0')
    yang_norm = norm(yang_str)
    yin_norm = norm(yin_str)
    # 精确匹配
    combo_key = f"{yang_str}-{yin_str}"
    reverse_key = f"{yin_str}-{yang_str}"
    if combo_key in COMBO_INTERPRETATIONS:
        return COMBO_INTERPRETATIONS[combo_key]
    if reverse_key in COMBO_INTERPRETATIONS:
        return COMBO_INTERPRETATIONS[reverse_key]
    # 标准化后匹配
    combo_norm = f"{yang_norm}-{yin_norm}"
    reverse_norm = f"{yin_norm}-{yang_norm}"
    if combo_norm in COMBO_INTERPRETATIONS:
        return COMBO_INTERPRETATIONS[combo_norm]
    if reverse_norm in COMBO_INTERPRETATIONS:
        return COMBO_INTERPRETATIONS[reverse_norm]
    # 纯格检测（标准化后）
    if yang_norm == yin_norm:
        pure_key = f"{yang_norm}-{yang_norm}"
        if pure_key in COMBO_INTERPRETATIONS:
            return COMBO_INTERPRETATIONS[pure_key]
    return None

def get_single_grid_info(grid_str):
    """获取单格的详细信息，支持精确/前缀/子串多种匹配方式"""
    if not grid_str:
        return None
    gs = str(grid_str)
    # 精确匹配
    if gs in SINGLE_GRID_INTERPRETATIONS:
        return SINGLE_GRID_INTERPRETATIONS[gs]
    # 去除前导零后匹配（如0219101 → 19101, 02102 → 2102）
    def stripLeadingZeros(s):
        if not s:
            return s
        if s.isdigit():
            # 逐位去除前导零直到遇到非零数字
            for i in range(len(s)):
                if s[i] != '0':
                    return s[i:]
            return s[-1] if s else s
        return s.lstrip('0') or s
    gs_stripped = stripLeadingZeros(gs)
    if gs_stripped and gs_stripped != gs:
        if gs_stripped in SINGLE_GRID_INTERPRETATIONS:
            return SINGLE_GRID_INTERPRETATIONS[gs_stripped]
    # 子串匹配：在grid中搜索已知key（优先较长key）
    matches = []
    for key in SINGLE_GRID_INTERPRETATIONS:
        if len(key) <= 5 and key in gs:
            matches.append((len(key), key))
    if matches:
        matches.sort(reverse=True)  # 优先最长匹配
        return SINGLE_GRID_INTERPRETATIONS[matches[0][1]]
    # 前缀匹配（较长格的前4位匹配短key）
    for key in SINGLE_GRID_INTERPRETATIONS:
        if len(key) <= 5 and gs.startswith(key):
            return SINGLE_GRID_INTERPRETATIONS[key]
    return None

def format_result(result):
    """格式化基础查询结果"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  日期：{result['日期']}    时辰：{result['时辰']}")
    lines.append(f"  类型：{result['类型']}")
    lines.append("-" * 60)

    if result['类型'] == '子时双格':
        lines.append("【当天格】")
        lines.append(f"  阳格：{result['阳格']}    阳缺：{result['阳缺']}")
        lines.append(f"  阴格：{result['阴格']}    阴缺：{result['阴缺']}")
        lines.append(f"  半补：{result['半补']}")
        if result.get('灵魂积分'):
            info = result['灵魂积分']
            lines.append(f"  灵魂：{info['stars']} {info['name']} | {info['level']}")
            if info.get('path'):
                lines.append(f"       跌落路径：{info['path']}")
        lines.append("")
        lines.append("【调整格（前子时+1天）】")
        lines.append(f"  阳格：{result.get('阳格1', '')}    阳缺：{result.get('阳缺1', '')}")
        lines.append(f"  阴格：{result.get('阴格1', '')}    阴缺：{result.get('阴缺1', '')}")
        lines.append(f"  半补：{result.get('半补1', '')}")
        if result.get('灵魂积分1'):
            info = result['灵魂积分1']
            lines.append(f"  灵魂：{info['stars']} {info['name']} | {info['level']}")
            if info.get('path'):
                lines.append(f"       跌落路径：{info['path']}")
        lines.append("")
        lines.append(f"  说明：{result.get('子时说明', '')}")
    else:
        lines.append(f"  阳格：{result['阳格']}    阳缺：{result['阳缺']}")
        lines.append(f"  阴格：{result['阴格']}    阴缺：{result['阴缺']}")
        lines.append(f"  半补：{result['半补'] if result['半补'] else 'null'}")
        if result.get('灵魂积分'):
            info = result['灵魂积分']
            lines.append(f"  灵魂：{info['stars']} {info['name']} | {info['level']}")
            if info.get('path'):
                lines.append(f"       跌落路径：{info['path']}")

    lines.append("")
    lines.append("【半补规律】时辰五行→数字：金1,2 木4,5 水0,6 火3 土7,8,9")
    lines.append("=" * 60)
    return '\n'.join(lines)

def format_interpretation(result):
    """格式化详细的组合解读信息"""
    lines = []
    if result['类型'] == '子时双格':
        yang_grids = [result['阳格'], result.get('阳格1', '')]
        yin_grids = [result['阴格'], result.get('阴格1', '')]
        grid_pairs = list(zip(yang_grids, yin_grids))
    else:
        grid_pairs = [(result['阳格'], result['阴格'])]

    for i, (yg, ig) in enumerate(grid_pairs):
        if result['类型'] == '子时双格':
            prefix = f"【当天格】" if i == 0 else f"【调整格】"
            lines.append("")
            lines.append(f"{prefix}  阳格{yg} × 阴格{ig}")
        else:
            lines.append("")
            lines.append(f"【组合解读】  阳格{yg} × 阴格{ig}")

        combo = get_combo_interpretation(yg, ig)
        if combo:
            if combo.get('is_pure'):
                # 阴阳同格（纯格）特殊说明
                lines.append("")
                lines.append(f"  ★ 阴阳同格（纯格）★")
                lines.append(f"  名称：{combo['combo_name']}")
                pe = combo.get('pure_energy', {})
                lines.append(f"  {pe.get('定义', '')}")
                lines.append("")
                lines.append("  ▶ 优势（能量纯粹性）：")
                for adv in pe.get('优势', []):
                    lines.append(f"    · {adv}")
                lines.append("")
                lines.append("  ▶ 核心课题：")
                for topic in pe.get('课题', []):
                    lines.append(f"    · {topic}")
                lines.append("")
                lines.append("  ▶ 修行路径：")
                lines.append(f"    {pe.get('修行路径', '')}")
                if pe.get('缺数建议'):
                    lines.append(f"  ▶ 缺数建议：{pe.get('缺数建议', '')}")
            else:
                # 阴阳双格组合
                lines.append(f"  组合名称：{combo.get('combo_name', '')}")
                if combo.get('aliases'):
                    lines.append(f"  别称：{' / '.join(combo.get('aliases', []))}")
                lines.append("")

                # 阳格解读
                yg_info = combo.get('yang_grid', {})
                if yg_info:
                    lines.append(f"  ▶ 阳格 {yg_info.get('number', yg)}：")
                    lines.append(f"    身份：{yg_info.get('identity', '')}")
                    if yg_info.get('quote'):
                        lines.append(f"    原话：{yg_info.get('quote', '')}")
                    for feat in yg_info.get('features', []):
                        lines.append(f"    · {feat}")
                    if yg_info.get('path'):
                        lines.append(f"    跌落路径：{yg_info.get('path', '')}")
                    if yg_info.get('修行_key'):
                        lines.append(f"    修行要点：{yg_info.get('修行_key', '')}")

                lines.append("")

                # 阴格解读
                ig_info = combo.get('yin_grid', {})
                if ig_info:
                    lines.append(f"  ▶ 阴格 {ig_info.get('number', ig)}：")
                    lines.append(f"    身份：{ig_info.get('identity', '')}")
                    if ig_info.get('quote'):
                        lines.append(f"    原话：{ig_info.get('quote', '')}")
                    for feat in ig_info.get('features', []):
                        lines.append(f"    · {feat}")
                    if ig_info.get('wealth_warning'):
                        lines.append(f"    ⚠️ {ig_info.get('wealth_warning', '')}")
                    if ig_info.get('path'):
                        lines.append(f"    跌落路径：{ig_info.get('path', '')}")
                    if ig_info.get('修行_key'):
                        lines.append(f"    修行要点：{ig_info.get('修行_key', '')}")

                # 关系动态
                if combo.get('relationship_dynamics'):
                    lines.append("")
                    lines.append("  ▶ 关系动态：")
                    for dyn in combo.get('relationship_dynamics', []):
                        lines.append(f"    · {dyn}")

                # 综合总结
                summary = combo.get('summary', {})
                if summary:
                    lines.append("")
                    lines.append("  ▶ 综合总结：")
                    lines.append(f"    人生剧本：{summary.get('人生剧本', '')}")
                    lines.append(f"    核心课题：{summary.get('核心课题', '')}")
                    if summary.get('天赋潜力'):
                        lines.append(f"    天赋潜力：{summary.get('天赋潜力', '')}")
                    if summary.get('特别注意'):
                        lines.append(f"    ⚠️ {summary.get('特别注意', '')}")
                    if summary.get('修行总纲'):
                        lines.append(f"    【修行总纲】{summary.get('修行总纲', '')}")
        else:
            # 无专门组合解读，显示单格信息
            lines.append(f"  （该组合暂无专门解读，以下为单格信息）")
            yang_info = get_single_grid_info(yg)
            yin_info = get_single_grid_info(ig)
            if yang_info:
                lines.append(f"  ▶ 阳格 {yg}：")
                lines.append(f"    {yang_info.get('name', '')} | {yang_info.get('level', '')}")
                lines.append(f"    {yang_info.get('core', '')}")
                if yang_info.get('课题'):
                    lines.append(f"    课题：{' / '.join(yang_info.get('课题', []))}")
                if yang_info.get('修行提示'):
                    lines.append(f"    修行提示：{yang_info.get('修行提示', '')}")
            if yin_info and str(ig) != str(yg):
                lines.append(f"  ▶ 阴格 {ig}：")
                lines.append(f"    {yin_info.get('name', '')} | {yin_info.get('level', '')}")
                lines.append(f"    {yin_info.get('core', '')}")
                if yin_info.get('课题'):
                    lines.append(f"    课题：{' / '.join(yin_info.get('课题', []))}")
                if yin_info.get('修行提示'):
                    lines.append(f"    修行提示：{yin_info.get('修行提示', '')}")

        # 纯格特别提示
        if str(yg) == str(ig) and not combo:
            # 阴阳同格但不在COMBO_INTERPRETATIONS里
            yang_info = get_single_grid_info(yg)
            if yang_info:
                lines.append("")
                lines.append(f"  ★ 阴阳同格 ★")
                lines.append(f"  阳格与阴格完全相同（均为{yang_info.get('name', yg)}）")
                lines.append(f"  能量高度聚焦，课题高度集中，在各层面反复遇到同一类核心问题")
                if yang_info.get('课题'):
                    lines.append(f"  核心课题：{' / '.join(yang_info.get('课题', []))}")
                if yang_info.get('修行提示'):
                    lines.append(f"  修行提示：{yang_info.get('修行提示', '')}")

    lines.append("")
    return '\n'.join(lines)

def ask_date():
    """询问并解析日期"""
    print("\n" + "=" * 50)
    print("  【九宫格查询】请输入阳历生日")
    print("=" * 50)
    print("  格式：年/月/日，例如：1991/12/24")
    print("  提示：输入 q 退出\n")

    while True:
        date_input = input("请输入日期: ").strip()
        if date_input.lower() == 'q':
            print("\n感谢使用，再见！")
            sys.exit(0)
        parts = date_input.replace('-', '/').split('/')
        if len(parts) != 3:
            print("格式错误！请输入：年/月/日，例如：1991/12/24")
            continue
        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            if year < 1900 or year > 2100:
                print("年份请输入1900-2100之间的有效年份")
                continue
            if month < 1 or month > 12:
                print("月份请输入1-12")
                continue
            if day < 1 or day > 31:
                print("日期请输入1-31")
                continue
            return f"{year}/{month:02d}/{day:02d}"
        except ValueError:
            print("输入无效！请输入数字，例如：1991/12/24")

def ask_shichen():
    """询问时辰"""
    print("\n" + "=" * 50)
    print("  【时辰选择】请输入出生时辰")
    print("=" * 50)
    print("""
  ┌─────────────────────────────────────────────┐
  │  寅时(3-5点)  / 卯时(5-7点)   → 木 → 半补45  │
  │  巳时(9-11点) / 午时(11-13点) → 火 → 半补3   │
  │  申时(15-17点)/ 酉时(17-19点) → 金 → 半补12  │
  │  亥时(21-23点)               → 水 → 半补06  │
  │  辰时(7-9点)  / 戌时(19-21点)│             │
  │  丑时(1-3点)  / 未时(13-15点) → 土 → 半补789│
  └─────────────────────────────────────────────┘

  ※ 子时(23:00-01:00) 需区分：
    → 前子时：23:00-00:00（属于下一天）
    → 后子时：00:00-01:00（属于当天）

  请直接输入时辰，例如：巳时、卯时、前子时
  输入 q 退出
""")

    valid_shichen = [
        '寅时', '卯时', '巳时', '午时',
        '申时', '酉时', '亥时', '辰时', '戌时', '丑时', '未时',
        '前子时', '后子时', '子时'
    ]

    while True:
        shichen_input = input("请输入时辰: ").strip()
        if shichen_input.lower() == 'q':
            print("\n感谢使用，再见！")
            sys.exit(0)
        if shichen_input in valid_shichen:
            if shichen_input == '子时':
                print("\n⚠️ 子时需要区分前子时或后子时：")
                print("  前子时：23:00-00:00（属于下一天）")
                print("  后子时：00:00-01:00（属于当天）")
                while True:
                    zi_choice = input("请选择 1=前子时 / 2=后子时: ").strip()
                    if zi_choice == '1':
                        return '前子时'
                    elif zi_choice == '2':
                        return '后子时'
                    else:
                        print("请输入 1 或 2")
            return shichen_input
        else:
            print(f"无效的时辰！可选：{'、'.join(valid_shichen)}")

def main():
    parser = argparse.ArgumentParser(description='慈海九宫格查询工具 v3.0')
    parser.add_argument('date', nargs='?', help='阳历日期 (YYYY/MM/DD)')
    parser.add_argument('-s', '--shichen', help='时辰', default=None)
    args = parser.parse_args()

    print("\n" + "★" * 25)
    print("   欢迎使用 慈海九宫格 查询工具 v3.0")
    print("   桌面九宫格查询与信息说明 文件夹版")
    print("★" * 25)

    if args.date:
        date_str = args.date
        shichen = args.shichen
        if not shichen:
            shichen = ask_shichen()
    else:
        date_str = ask_date()
        shichen = ask_shichen()

    # 计算结果
    result = calculate_nine_palace(date_str, shichen)

    print("\n" + "█" * 60)
    print("  【查询结果】")
    print("█" * 60)
    print(format_result(result))

    # 追加详细解读
    interp = format_interpretation(result)
    print("\n" + "◆" * 60)
    print("  【详细解读】")
    print("◆" * 60)
    print(interp)

    # 是否继续
    if not args.date:
        print("\n" + "-" * 60)
        while True:
            again = input("是否继续查询？(y/n): ").strip().lower()
            if again == 'y':
                main()
                return
            elif again == 'n':
                print("\n感谢使用，再见！")
                print("\n" + "★" * 25)
                return
            else:
                print("请输入 y 或 n")

if __name__ == '__main__':
    main()
