# -*- coding: utf-8 -*-
"""
重算 1910-01-01 … 2101-12-31 的阴阳格出现频率（每天各记一次）。

为什么不用仓库里的 grid_frequency_data.json：
  该文件 yang_counter 合计 435,004、yin_counter 合计 69,762 —— 比值 6.24，
  而生成脚本 batch_grid_count.py 是「每天各 +1」，两个合计本应相等。
  实测：阴格那侧 = 1910-01-01..2100-12-31（69,762 天，正好差 365 天）；
        阳格那侧约跨 1200 年（1400–2600 区间 438,656 天 / 784 种，1300–2700 得 804 种，
        与它的 798 种吻合）。分母不统一 ⟹ 无法换算概率，必须重算。

输出 freq.json：
  {"start":"1910-01-01","end":"2101-12-31","days":70127,
   "yang":{格:次数},"yin":{格:次数},"meta":{...}}
"""
import json, os, sys, time
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "核心引擎"))
import nine_palace_core_v5 as core

START = date(1910, 1, 1)
END = date(2101, 12, 31)


def main():
    t0 = time.time()
    yg, ig, pair = {}, {}, {}
    d, n = START, 0
    while d <= END:
        r = core.calc("%d/%02d/%02d" % (d.year, d.month, d.day), "午时", "male")
        y, i = r["阳格"], r["阴格"]
        yg[y] = yg.get(y, 0) + 1
        ig[i] = ig.get(i, 0) + 1
        k = y + "|" + i
        pair[k] = pair.get(k, 0) + 1
        n += 1
        d += timedelta(days=1)
    dt = time.time() - t0

    print("区间 %s .. %s" % (START, END))
    print("天数 %d   阳格 %d 种 / 合计 %d   阴格 %d 种 / 合计 %d   用时 %.1fs"
          % (n, len(yg), sum(yg.values()), len(ig), sum(ig.values()), dt))
    assert sum(yg.values()) == n and sum(ig.values()) == n

    def top(m, k=5):
        return sorted(m.items(), key=lambda x: -x[1])[:k]

    print("阳格 TOP5", top(yg))
    print("阴格 TOP5", top(ig))
    print("阳格只出现 1 次: %d 种；阴格只出现 1 次: %d 种"
          % (sum(1 for v in yg.values() if v == 1), sum(1 for v in ig.values() if v == 1)))
    print("双格组合去重 %d 种；只出现 1 次 %d 种"
          % (len(pair), sum(1 for v in pair.values() if v == 1)))

    # ── 独立性检验：实测联合次数 vs 独立估算 N*py*pi ──
    devs = []
    for k, c in pair.items():
        y, i = k.split("|")
        est = n * (yg[y] / n) * (ig[i] / n)
        devs.append((abs(c - est) / max(est, 1e-9), c, est, k))
    devs.sort()
    med = devs[len(devs) // 2]
    p90 = devs[int(len(devs) * 0.9)]
    print("独立性偏差：中位 %.1f%%（例 %s 实测 %d / 估算 %.1f）；P90 %.1f%%"
          % (med[0] * 100, med[3], med[1], med[2], p90[0] * 100))

    # 抽样看具体例子
    for probe in ["121121|1167", "1358|347"]:
        if probe in pair:
            y, i = probe.split("|")
            est = n * (yg[y] / n) * (ig[i] / n)
            print("  %s 实测 %d 天，独立估算 %.1f 天" % (probe, pair[probe], est))

    out = {
        "start": START.isoformat(),
        "end": END.isoformat(),
        "days": n,
        "yang": dict(sorted(yg.items())),
        "yin": dict(sorted(ig.items())),
        "meta": {
            "yang_types": len(yg),
            "yin_types": len(ig),
            "pair_types": len(pair),
            "median_dev": round(med[0], 4),
            "p90_dev": round(p90[0], 4),
        },
    }
    with open(os.path.join(HERE, "freq.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("已写 freq.json", os.path.getsize(os.path.join(HERE, "freq.json")), "字节")

    # ── 联合分布（双格组合实测天数）──
    # map 只存 count>=2 的组合，未出现的按 1 计；hist 存完整直方图用于算分位。
    hist = {}
    for c in pair.values():
        hist[c] = hist.get(c, 0) + 1
    jmap = {k: c for k, c in pair.items() if c >= 2}
    jt = {
        "single": sum(1 for c in pair.values() if c == 1),
        "hist": {str(k): hist[k] for k in sorted(hist)},
        "map": dict(sorted(jmap.items())),
    }
    with open(os.path.join(HERE, "freq_joint.json"), "w", encoding="utf-8") as f:
        json.dump(jt, f, ensure_ascii=False, separators=(",", ":"))
    print("已写 freq_joint.json", os.path.getsize(os.path.join(HERE, "freq_joint.json")),
          "字节 | 直方图档位", len(hist), "| map", len(jmap), "| 单次组合", jt["single"])
    print("联合次数分布", [(k, hist[k]) for k in sorted(hist)[:6]])


if __name__ == "__main__":
    main()
