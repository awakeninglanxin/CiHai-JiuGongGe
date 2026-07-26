# -*- coding: utf-8 -*-
"""
批量日历九宫格阴阳格统计
从 nine_palace_core_v5 导入 yangCalc/yinCalc，遍历日期范围，
分别累积阳格和阴格的数字组合出现次数。

★ 修改日期：编辑 config_grid_count.py
★ 运行方式：双击 一键统计阴阳格频率.bat
"""
import sys, os, json
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from nine_palace_core_v5 import yangCalc, yinCalc, ds
try:
    from config_grid_count import START_DATE, END_DATE
except ImportError:
    START_DATE = datetime(1910, 1, 1)
    END_DATE   = datetime(2050, 12, 31)


def count_grids(start_date, end_date):
    """统计日期范围内每天阳格/阴格数字组合频次"""
    yang_counter = Counter()
    yin_counter  = Counter()
    total_days   = 0
    yang_fail    = 0
    yin_fail     = 0

    current = start_date
    today   = datetime.now()
    dt_today = datetime(today.year, today.month, today.day)

    while current <= end_date:
        total_days += 1
        y, m, d = current.year, current.month, current.day

        # 阳格
        try:
            yang_res, _, _, _ = yangCalc(y, m, d)
            if yang_res:
                yang_counter[yang_res] += 1
            else:
                yang_fail += 1
        except Exception:
            yang_fail += 1

        # 阴格（农历转换可能对2100年之后失败）
        try:
            yin_res, _ = yinCalc(y, m, d)
            if yin_res and yin_res != '0':
                yin_counter[yin_res] += 1
            else:
                yin_fail += 1
        except Exception:
            yin_fail += 1

        # 进度提示
        if total_days % 5000 == 0:
            print(f"  已处理 {total_days} 天 ... ({current.strftime('%Y-%m-%d')})")

        current += timedelta(days=1)

    return {
        'total_days': total_days,
        'date_range': f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        'yang_counter': dict(yang_counter),
        'yin_counter': dict(yin_counter),
        'yang_total_types': len(yang_counter),
        'yin_total_types': len(yin_counter),
        'yang_fail': yang_fail,
        'yin_fail': yin_fail,
    }


def main():
    try:
        start = input(f"起始日期 [{START_DATE.strftime('%Y-%m-%d')}]: ").strip()
    except (EOFError, OSError):
        start = ""
    try:
        end   = input(f"结束日期 [{END_DATE.strftime('%Y-%m-%d')}]:   ").strip()
    except (EOFError, OSError):
        end = ""

    sdt = datetime.strptime(start, '%Y-%m-%d') if start else START_DATE
    edt = datetime.strptime(end, '%Y-%m-%d') if end else END_DATE

    print(f"\n统计范围: {sdt.strftime('%Y-%m-%d')} ~ {edt.strftime('%Y-%m-%d')}")
    print("计算中...\n")

    result = count_grids(sdt, edt)

    # 排序输出
    yang_sorted = sorted(result['yang_counter'].items(), key=lambda x: -x[1])
    yin_sorted  = sorted(result['yin_counter'].items(), key=lambda x: -x[1])

    print(f"\n{'='*60}")
    print(f"总天数: {result['total_days']}")
    print(f"阳格种类: {result['yang_total_types']}  |  阴格种类: {result['yin_total_types']}")
    print(f"阳格失败: {result['yang_fail']}  |  阴格失败: {result['yin_fail']}")

    print(f"\n--- 阳格 TOP 30 (共{result['yang_total_types']}种) ---")
    for code, cnt in yang_sorted[:30]:
        print(f"  {code}: {cnt}次")

    print(f"\n--- 阴格 TOP 30 (共{result['yin_total_types']}种) ---")
    for code, cnt in yin_sorted[:30]:
        print(f"  {code}: {cnt}次")

    # 合并阳+阴的去重种类
    all_codes = set(result['yang_counter'].keys()) | set(result['yin_counter'].keys())
    print(f"\n--- 阴阳格合并去重种类 ---")
    print(f"  阳格种类: {result['yang_total_types']}")
    print(f"  阴格种类: {result['yin_total_types']}")
    print(f"  合并去重: {len(all_codes)} 种大神")

    # 找出只在阳格或只在阴格出现的
    yang_only = set(result['yang_counter'].keys()) - set(result['yin_counter'].keys())
    yin_only  = set(result['yin_counter'].keys()) - set(result['yang_counter'].keys())
    print(f"  仅在阳格: {len(yang_only)} 种")
    print(f"  仅在阴格: {len(yin_only)} 种")

    # 保存到 JSON
    out_path = os.path.join(os.path.dirname(__file__), '..', 'grid_frequency_data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n完整数据已保存: {out_path}")
    return result


if __name__ == '__main__':
    main()
