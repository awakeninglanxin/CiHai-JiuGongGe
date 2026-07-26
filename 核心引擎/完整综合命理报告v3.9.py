# -*- coding: utf-8 -*-
"""完整综合命理报告生成器 v3.9"""
import sys, os
from datetime import datetime
from nine_palace_core_v5 import calc

def generate_comprehensive_report(birth_date="1991/08/16", birth_time="巳时", gender="male", name="蓝馨", target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y/%m/%d")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except: pass

    r = calc(birth_date, birth_time, gender)

    # 检查是否是子时双格
    is_zishi = '阳格1' in r and '阴格1' in r

    # 基本信息
    yang_que = r.get("阳缺", "")
    yin_que = r.get("阴缺", "")
    yang_ge = r.get("阳格", "")
    yin_ge = r.get("阴格", "")
    banbu = r.get("半补", "")

    # 子时双格信息
    if is_zishi:
        yang_que1 = r.get("阳缺1", "")
        yin_que1 = r.get("阴缺1", "")
        yang_ge1 = r.get("阳格1", "")
        yin_ge1 = r.get("阴格1", "")
        banbu1 = r.get("半补1", "")
        adj_date = r.get("调整日期", "")
        zishi_note = r.get("说明", "")
    else:
        yang_que1 = ""
        yin_que1 = ""
        yang_ge1 = ""
        yin_ge1 = ""
        banbu1 = ""
        adj_date = ""
        zishi_note = ""

    yang_yin = r.get("阳格阴阳分析", {})
    if isinstance(yang_yin, str): yang_yin = {"阴阳倾向": yang_yin, "解释": ""}
    trend = yang_yin.get("阴阳倾向", "平衡")
    trend_desc = yang_yin.get("解释", "")

    zangfu = {"0":"小肠","1":"肺","2":"大肠","3":"心","4":"肝","5":"胆","6":"肾","7":"胃","8":"脾","9":"膀胱"}
    corrections = {"缺格诊断":{"0":"分清泌浊","1":"多做深呼吸","2":"腹式呼吸+蔬菜配方","3":"通心轮（小白瓶）","4":"A杯+蔬菜配方","5":"宁化府饺子醋","6":"黑米套餐+动功","7":"小绿瓶+情感和谐","8":"铁棍山药+忌甜食","9":"开天门+黑豆黑木耳"}}

    now_dt = datetime.now()
    born_dt = datetime.strptime(birth_date.replace("/", "-"), "%Y-%m-%d")
    age = now_dt.year - born_dt.year - ((now_dt.month, now_dt.day) < (born_dt.month, born_dt.day))

    report = []
    report.append(f"# {name} · 综合命理报告")
    report.append("")
    report.append(f"**生辰**: {birth_date} {birth_time}")
    report.append(f"**性别**: {"男" if gender=="male" else "女"}")
    report.append(f"**生成时间**: {now_dt.strftime("%Y-%m-%d %H:%M")} | **年龄**: {age}岁")
    report.append("")

    # 命盘概要 - 子时显示4格
    if is_zishi:
        report.append("### 命盘概要（子时双格）")
        report.append("")
        report.append(f"| 类型 | 阳格 | 阴格 | 阳缺 | 阴缺 | 半补 |")
        report.append("|:----:|:-----:|:-----:|:-----:|:-----:|:-----:|")
        report.append(f"| **当天格** | {yang_ge} | {yin_ge} | {yang_que} | {yin_que} | {banbu} |")
        report.append(f"| **调整格** | {yang_ge1} | {yin_ge1} | {yang_que1} | {yin_que1} | {banbu1} |")
        report.append("")
        report.append(f"> **{zishi_note}** | 调整日期: {adj_date}")
        report.append("")
        # 合并缺格
        all_yang_que = set(yang_que) | set(yang_que1)
        all_yin_que = set(yin_que) | set(yin_que1)
        all_que = all_yang_que | all_yin_que
        all_que_str = ''.join(sorted(all_que))
        all_que_organs = '、'.join([zangfu.get(n, "?") for n in sorted(all_que)])
        report.append(f"> **综合缺格**: {all_que_str} → {all_que_organs}")
    else:
        report.append(f"**命盘**: 阳格{yang_ge} | 阴格{yin_ge}")
        report.append(f"**缺格**: 阳缺{yang_que} | 阴缺{yin_que} | 半补{banbu}")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 一、基本信息")
    report.append("")
    soul = r.get("灵魂", {}) or {}
    soul_n = soul.get("n", "")
    soul_t = soul.get("t", "")
    if soul_n:
        report.append(f"- **灵魂**: {soul_n}（{soul_t}）")
    report.append(f"- **类型**: {r.get('类型', '普通阴阳双格')}")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 二、阴阳格周期")
    report.append("")
    if trend == "平衡":
        report.append("您的阳格和阴格处于**平衡期**，阴阳同调为佳。")
    elif trend == "阳":
        report.append(f"当前处于**阳格期**：以{yang_ge}为主导能量。{trend_desc}")
    else:
        report.append(f"当前处于**阴格期**：以{yin_ge}为主导能量。{trend_desc}")

    lc = r.get("生命周期", {})
    if lc:
        report.append("")
        report.append("**生命周期状态**:")
        report.append(f"- 年龄: {lc.get('年龄', age)}岁")
        report.append(f"- 当前阶段: {lc.get('当前阶段', '')}")
        report.append(f"- 当前类型: {lc.get('当前类型', '')}")
        report.append(f"- 阶段区间: {lc.get('当前阶段开始', 0):.1f} ~ {lc.get('当前阶段结束', 0):.1f}岁")
        report.append(f"- 下次换魂: {lc.get('下次换魂', '')}（{lc.get('距下次换魂', 0):.1f}年后）")
    report.append("")
    report.append("---")
    report.append("")

    # 缺格修正 - 合并两套格的缺格
    if is_zishi:
        report.append("## 三、缺格修正方案（双格合并）")
        report.append("")
        report.append(f"当天格缺格: 阳缺{yang_que} + 阴缺{yin_que}")
        report.append(f"调整格缺格: 阳缺{yang_que1} + 阴缺{yin_que1}")
        report.append("")
        all_missing = sorted(all_que)
        for num in all_missing:
            organ = zangfu.get(num, "未知")
            desc = corrections["缺格诊断"].get(num, "对应食疗动功调理")
            # 判断是阳缺还是阴缺
            yq_src = []
            if num in yang_que: yq_src.append("当天")
            if num in yang_que1: yq_src.append("调整")
            if num in yin_que: yq_src.append("当天阴")
            if num in yin_que1: yq_src.append("调整阴")
            src_str = '+'.join(set(yq_src))
            report.append(f"**{num}（{organ}）** [{src_str}]: {desc}")
        report.append("")
    else:
        report.append("## 三、缺格修正方案")
        report.append("")
        for num in sorted(set(yang_que+yin_que)):
            organ = zangfu.get(num, "未知")
            desc = corrections["缺格诊断"].get(num, "对应食疗动功调理")
            report.append(f"**{num}（{organ}）**: {desc}")
        report.append("")

    report.append("---")
    report.append("")
    report.append("## 四、脏腑详解（缺格对应）")
    report.append("")
    missing_list = sorted(all_que) if is_zishi else sorted(set(yang_que+yin_que))
    for num in missing_list:
        organ = zangfu.get(num, "未知")
        # 判断阳缺还是阴缺
        is_yang = num in yang_que or num in yang_que1
        is_yin = num in yin_que or num in yin_que1
        if is_zishi:
            yang_src = (num in yang_que) + (num in yang_que1)
            yin_src = (num in yin_que) + (num in yin_que1)
            que_type = f"阳缺{'(双)' if yang_src==2 else '(单)' if yang_src else ''}" if yang_src else ""
            que_type += f" 阴缺{'(双)' if yin_src==2 else '(单)' if yin_src else ''}" if yin_src else ""
        else:
            que_type = "阳缺" if is_yang else "阴缺"
        report.append(f"### {num}（{organ}）")
        report.append(f"- 类型：{que_type.strip()}")
        report.append(f"- 修正：{corrections['缺格诊断'].get(num, '请参考缺格修正方案')}")
        report.append("")

    report.append("---")
    report.append("")
    report.append("## 五、命盘整体分析")
    report.append("")
    if is_zishi:
        miss = sorted(all_que)
        miss_org = [zangfu.get(n,"?") for n in miss]
        report.append(f"命盘缺格共 {len(miss)} 个数字（阳缺合集{yang_que}/{yang_que1}、阴缺合集{yin_que}/{yin_que1}），涉及脏腑：{"、".join(miss_org)}。")
    else:
        qm = yang_que + yin_que
        miss = sorted(set(qm))
        miss_org = [zangfu.get(n,"?") for n in miss]
        report.append(f"命盘缺格共 {len(miss)} 个数字（阳缺{yang_que}、阴缺{yin_que}），涉及脏腑：{"、".join(miss_org)}。")
    report.append("")
    report.append("---")
    report.append("")

    # 六、今日行运分析 - 需要处理双格共振
    report.append(f"## 六、今日行运分析 ({target_date})")
    SHICHEN_LIST = ["子时","丑时","寅时","卯时","辰时","巳时","午时","未时","申时","酉时","戌时","亥时"]
    now_shichen = SHICHEN_LIST[(datetime.now().hour + 1) // 2]
    day_r = calc(target_date, now_shichen, gender)

    day_yang = day_r.get("阳格", "")
    day_yin = day_r.get("阴格", "")
    day_yang_que = day_r.get("阳缺", "")
    day_yin_que = day_r.get("阴缺", "")
    day_banbu = day_r.get("半补", "")

    # 子时需要计算两套格的共振
    if is_zishi:
        day_yang_que1 = day_r.get("阳缺1", "")
        day_yin_que1 = day_r.get("阴缺1", "")

        # 天时共振计算（需要同时考虑两套命盘）
        d_yq = set(day_yang_que)
        d_iq = set(day_yin_que)
        b_yq = set(yang_que) | set(yang_que1)  # 合并两套阳缺
        b_iq = set(yin_que) | set(yin_que1)    # 合并两套阴缺

        level1 = sorted((d_yq & b_yq) | (d_iq & b_iq))
        level2 = sorted((d_yq & b_iq) | (d_iq & b_yq))

        report.append("")
        report.append("**今日天时**:")
        report.append(f"- 天时阳格: {day_yang} | 天时阴格: {day_yin}")
        report.append(f"- 天时阳缺: {day_yang_que} | 天时阴缺: {day_yin_que}")
        report.append(f"- 天时半补: {day_banbu or '无'}")
        report.append("")
        report.append("| 数字 | 脏腑 | 天时 | 命盘(当天) | 命盘(调整) | 共振 |")
        report.append("|:----:|:----:|------|:----------:|:----------:|:-----:|")
        for num in [str(i) for i in range(10)]:
            organ = zangfu.get(num, "未知")
            day_y = "阳缺" if num in day_yang_que else ""
            day_i = "阴缺" if num in day_yin_que else ""
            day_tz = ("阳缺 " if num in day_yang_que else "") + ("阴缺" if num in day_yin_que else "正常")
            birth_y = "缺" if num in yang_que else "正常"
            birth_y1 = "缺" if num in yang_que1 else "正常"
            birth_i = "缺" if num in yin_que else "正常"
            birth_i1 = "缺" if num in yin_que1 else "正常"
            if num in level1: res = "🔴 一级"
            elif num in level2: res = "🟡 二级"
            else: res = "⚪ 潜伏"
            report.append(f"| **{num}** | {organ} | {day_tz} | {birth_y}/{birth_i} | {birth_y1}/{birth_i1} | {res} |")
    else:
        d_yq = set(day_yang_que)
        d_iq = set(day_yin_que)
        b_yq = set(yang_que)
        b_iq = set(yin_que)
        level1 = sorted((d_yq & b_yq) | (d_iq & b_iq))
        level2 = sorted((d_yq & b_iq) | (d_iq & b_yq))

        day_organs_yang = ''.join([zangfu.get(d,"") for d in day_yang if d.isdigit()])
        day_organs_yin = ''.join([zangfu.get(d,"") for d in day_yin if d.isdigit()])
        day_yq_org = '、'.join([zangfu.get(d,"") for d in day_yang_que if d.isdigit()]) or '无'
        day_iq_org = '、'.join([zangfu.get(d,"") for d in day_yin_que if d.isdigit()]) or '无'

        report.append("")
        report.append("| 数字 | 脏腑 | 今日天时 | 命盘 | 共振强度 |")
        report.append("|------|------|----------|------|----------|")
        for num in [str(i) for i in range(10)]:
            organ = zangfu.get(num, "未知")
            day_tz = ("阳缺 " if num in day_yang_que else "") + ("阴缺" if num in day_yin_que else "正常")
            in_birth = "命盘缺" if num in yang_que or num in yin_que else "命盘正常"
            if num in level1: res = "🔴 一级共振"
            elif num in level2: res = "🟡 二级共振"
            else: res = "⚪ 潜伏期"
            report.append(f"| **{num}** | {organ} | {day_tz} | {in_birth} | {res} |")

    report.append("")
    report.append("> 📌 共振等级分档：🔴 一级共振（双重缺格，核心关注）| 🟡 二级共振（单层缺格，辅助关注）| ⚪ 潜伏期（能量休眠）")
    report.append("")
    if level1:
        report.append("**🔴 一级共振器官（需重点关注）**:")
        for num in sorted(level1):
            organ = zangfu.get(num, "未知")
            correction = corrections["缺格诊断"].get(num, "请参考缺格修正方案")
            report.append(f"- {organ}({num}): 天时+命盘双重缺格，能量缺口最大 -> {correction}")
    if level2:
        level2_unique = [n for n in sorted(level2) if n not in level1]
        if level2_unique:
            report.append("**🟡 二级共振器官（需留意）**:")
            for num in level2_unique:
                organ = zangfu.get(num, "未知")
                correction = corrections["缺格诊断"].get(num, "请参考缺格修正方案")
                report.append(f"- {organ}({num}): 单层共振，能量有缺口 -> {correction}")
    report.append("")

    # 七、GDV数据分析
    report.append("---")
    report.append("")
    report.append("## 七、GDV数据分析")
    report.append("")
    report.append("本部分内容请参考详细GDV趋势分析报告。")
    report.append("")

    out_file = f"{name}命理报告_{birth_date.replace('/','')}_{birth_time}_v3.9.md"
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_file)
    with open(out_path, "w", encoding="utf-8") as f: f.write("\n".join(report))
    print(f"报告已生成：{out_path}")
    return out_path, "\n".join(report)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description='完整综合命理报告生成器 v3.9')
    p.add_argument("birth", nargs="?", default="1991/08/16", help="出生日期 YYYY/MM/DD")
    p.add_argument("shichen", nargs="?", default="巳时", help="时辰")
    p.add_argument("gender", nargs="?", default="male", help="性别 male/男 或 female/女")
    p.add_argument("-n", "--name", default="蓝馨", help="姓名")
    args = p.parse_args()
    g = "male" if args.gender in ["male", "男"] else "female"
    path, _ = generate_comprehensive_report(args.birth, args.shichen, g, args.name)
    print(f"输出: {path}")
