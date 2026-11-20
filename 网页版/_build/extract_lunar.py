# -*- coding: utf-8 -*-
"""
从 lunarcalendar 导出「农历月首表」并压缩编码，供网页端 JS 使用。

编码：每天查表得到 (lunarYear, lunarMonth, lunarDay)。
月首表每项 3 字符 = [月份 base36][闰月 0/1][本月天数 base36]
  - 月份 1..12 → base36 '1'..'c'
  - 天数 29→'t' / 30→'u'
  - 闰月用 1 位 '0'/'1' 单独记录（阴格计算不用它，但展示要用）
农历年：首项年 = LUNAR_Y0，之后遇到「月份==1 且非闰」则年 +1。
"""
import json, os, sys
from datetime import date, timedelta
from lunarcalendar import Converter, Solar

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"
START = date(1900, 1, 1)
END = date(2101, 12, 31)

OUT = os.path.dirname(os.path.abspath(__file__))


def build():
    months = []          # [{start:date, ly:int, lm:int(正数), leap:bool}]
    prev = None
    d = START
    while d <= END:
        l = Converter().Solar2Lunar(Solar(d.year, d.month, d.day))
        lm = abs(l.month)
        leap = bool(getattr(l, "isleap", False))
        if prev is None or l.day == 1:
            months.append({"start": d, "ly": l.year, "lm": lm, "leap": leap})
        prev = (l.year, lm, l.day, leap)
        d += timedelta(days=1)

    # 计算每月天数
    for i, m in enumerate(months):
        if i + 1 < len(months):
            m["len"] = (months[i + 1]["start"] - m["start"]).days
        else:
            m["len"] = (END - m["start"]).days + 1  # 末月截断
    return months


def encode(months):
    y0 = months[0]["ly"]
    parts = []
    for m in months:
        mon = B36[m["lm"]]
        lp = "1" if m["leap"] else "0"
        ln = B36[m["len"]]
        parts.append(mon + lp + ln)
    return {"y0": y0, "s": "".join(parts), "n": len(months)}


def verify(months):
    """用编码表反推每一天，与 lunarcalendar 直接结果逐日比对"""
    table = encode(months)
    s = table["s"]
    y0 = table["y0"]
    n = table["n"]
    assert len(s) == n * 3, (len(s), n)

    # 展开为 starts
    starts = []
    cur = START
    ly_list = []
    lm_list = []
    leap_list = []
    ly = y0
    for i in range(n):
        chunk = s[i * 3:i * 3 + 3]
        lm = B36.index(chunk[0])
        leap = chunk[1] == "1"
        ln = B36.index(chunk[2])
        # 年推进：月份回到 1 且非闰
        if i > 0 and lm == 1 and not leap:
            ly += 1
        ly_list.append(ly)
        lm_list.append(lm)
        leap_list.append(leap)
        starts.append(cur)
        cur = cur + timedelta(days=ln)

    # 校验起点
    mism = 0
    samples = []
    for i in range(n):
        assert ly_list[i] == months[i]["ly"], (i, ly_list[i], months[i])
        assert lm_list[i] == months[i]["lm"], (i, lm_list[i], months[i]["lm"])
        assert leap_list[i] == months[i]["leap"], (i, leap_list[i], months[i]["leap"])
        assert starts[i] == months[i]["start"], (i, starts[i], months[i]["start"])

    # 全量逐日复核
    import bisect
    d = START
    while d <= END:
        idx = bisect.bisect_right(starts, d) - 1
        pred = (ly_list[idx], lm_list[idx], (d - starts[idx]).days + 1)
        l = Converter().Solar2Lunar(Solar(d.year, d.month, d.day))
        real = (l.year, abs(l.month), l.day)
        if pred != real:
            mism += 1
            if len(samples) < 8:
                samples.append((d.isoformat(), pred, real))
        d += timedelta(days=1)
    return mism, samples, table


def cross_check():
    """与 lunar_python 交叉比对（信息性）"""
    try:
        from lunar_python import Solar as LPSolar
    except Exception:
        return None
    diff = []
    d = START
    while d <= END:
        l = Converter().Solar2Lunar(Solar(d.year, d.month, d.day))
        a = (l.year, abs(l.month), l.day)
        try:
            lp = LPSolar.fromYmd(d.year, d.month, d.day).getLunar()
            b = (lp.getYear(), abs(lp.getMonth()), lp.getDay())
        except Exception:
            b = None
        if b != a:
            diff.append((d.isoformat(), a, b))
        d += timedelta(days=7)   # 每周抽一天，跑得快
    return diff


if __name__ == "__main__":
    months = build()
    mism, samples, table = verify(months)
    print("月份数", table["n"], "| 编码长度", len(table["s"]))
    print("逐日全量复核 1900-01-01..2100-12-31 不一致天数:", mism)
    for s in samples:
        print("   ", s)
    with open(os.path.join(OUT, "lunar_table.json"), "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, separators=(",", ":"))
    print("已写 lunar_table.json")

    diff = cross_check()
    if diff is None:
        print("lunar_python 不可用，跳过交叉比对")
    else:
        print("与 lunar_python 抽样比对（每周一天）分歧数:", len(diff))
        for x in diff[:10]:
            print("   ", x)
