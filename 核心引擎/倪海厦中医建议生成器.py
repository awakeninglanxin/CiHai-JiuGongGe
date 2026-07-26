# -*- coding: utf-8 -*-
"""
倪海厦中医建议生成器 v1.0
整合九宫格命理信息 + 倪海厦经方体系
"""
import os
import sys
from datetime import datetime, timedelta
from math import radians, sin, cos, tan, asin, degrees

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# 路径设置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_DIR = SCRIPT_DIR
sys.path.insert(0, TOOL_DIR)

from nine_palace_core_v5 import calc as v5_calc

# ====== 中国主要城市经纬度数据库 ======
CITY_COORDS = {
    '北京': (39.9042, 116.4074),
    '上海': (31.2304, 121.4737),
    '广州': (23.1291, 113.2644),
    '深圳': (22.5431, 114.0579),
    '成都': (30.5728, 104.0668),
    '重庆': (29.5630, 106.5516),
    '杭州': (30.2741, 120.1551),
    '南京': (32.0603, 118.7969),
    '武汉': (30.5928, 114.3055),
    '西安': (34.3416, 108.9398),
    '天津': (39.3434, 117.3616),
    '苏州': (31.2989, 120.5853),
    '郑州': (34.7466, 113.6254),
    '长沙': (28.2282, 112.9388),
    '沈阳': (41.8057, 123.4328),
    '青岛': (36.0671, 120.3826),
    '济南': (36.6512, 117.1201),
    '大连': (38.9140, 121.6147),
    '福州': (26.0745, 119.2965),
    '厦门': (24.4798, 118.0894),
    '昆明': (25.0406, 102.7129),
    '贵阳': (26.6470, 106.6302),
    '石家庄': (38.0428, 114.5149),
    '太原': (37.8706, 112.5489),
    '哈尔滨': (45.8038, 126.5340),
    '长春': (43.8171, 125.3235),
    '兰州': (36.0611, 103.8343),
    '乌鲁木齐': (43.8256, 87.6168),
    '拉萨': (29.6500, 91.1000),
    '香港': (22.3193, 114.1694),
    '澳门': (22.1987, 113.5439),
    '台北': (25.0330, 121.5654),
}

# ====== 时辰工具 ======
SHICHEN_LIST = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时', '申时', '酉时', '戌时', '亥时']


def get_shichen_from_hour(hour):
    """根据小时数获取时辰"""
    if hour == 23 or hour < 1:
        return '子时'
    idx = (hour + 1) // 2
    if idx >= 12:
        idx = 11
    return SHICHEN_LIST[idx]


def calc_true_solar_time(birth_datetime, latitude, longitude, timezone=8):
    """计算真太阳时"""
    standard_lon = timezone * 15
    lon_diff = longitude - standard_lon
    day_of_year = birth_datetime.timetuple().tm_yday
    B = 2 * 3.14159 * (day_of_year - 81) / 365
    EoT = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.5 * sin(B)
    time_diff = lon_diff * 4 + EoT
    adjusted = birth_datetime + timedelta(minutes=time_diff)
    true_shichen = get_shichen_from_hour(adjusted.hour)
    return adjusted, true_shichen, round(time_diff, 1)


def lookup_city_coords(location):
    """查找城市经纬度"""
    if not location:
        return None
    location = location.strip()
    if location in CITY_COORDS:
        return CITY_COORDS[location]
    for city, coords in CITY_COORDS.items():
        if city in location or location in city:
            return coords
    if ',' in location:
        parts = location.split(',')
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except:
                pass
    return None


def get_true_solar_time(birth_date_str, location=None):
    """获取真太阳时（默认北京时间）"""
    born_dt = datetime.strptime(birth_date_str.replace('/', '-'), '%Y-%m-%d')

    coords = lookup_city_coords(location)
    if coords:
        lat, lon = coords
        adjusted_dt, true_shichen, time_diff = calc_true_solar_time(born_dt, lat, lon)
        location_desc = f"{location} ({lat}°, {lon}°)"
        return {
            "born_dt": born_dt,
            "adjusted_dt": adjusted_dt,
            "shichen": true_shichen,
            "time_diff": time_diff,
            "location": location_desc,
        }
    else:
        # 默认北京时间（东八区）
        return {
            "born_dt": born_dt,
            "adjusted_dt": born_dt,
            "shichen": get_shichen_from_hour(born_dt.hour),
            "time_diff": 0,
            "location": "默认北京时间",
        }


# ====== 脏腑映射（九宫格数字 → 脏腑） ======
ZANGFU_MAP = {
    "0": {"name": "小肠", "yin": "手太阳小肠经", "yang": "小肠", "element": "火"},
    "1": {"name": "肺", "yin": "手太阴肺经", "yang": "大肠", "element": "金"},
    "2": {"name": "大肠", "yin": "手阳明大肠经", "yang": "大肠", "element": "金"},
    "3": {"name": "心", "yin": "手少阴心经", "yang": "小肠", "element": "火"},
    "4": {"name": "肝", "yin": "足厥阴肝经", "yang": "胆", "element": "木"},
    "5": {"name": "胆", "yin": "足少阳胆经", "yang": "胆", "element": "木"},
    "6": {"name": "肾", "yin": "足少阴肾经", "yang": "膀胱", "element": "水"},
    "7": {"name": "胃", "yin": "足阳明胃经", "yang": "胃", "element": "土"},
    "8": {"name": "脾", "yin": "足太阴脾经", "yang": "胃", "element": "土"},
    "9": {"name": "膀胱", "yin": "足太阳膀胱经", "yang": "膀胱", "element": "水"},
}

# ====== 六经辨证对应 ======
SIX_DIVISION_MAP = {
    "0": {"jing": "少阴", "organ": "心", "desc": "心火亢盛、小肠热盛", "formula": "导赤散"},
    "1": {"jing": "太阴", "organ": "肺", "desc": "肺气不宣、津液失调", "formula": "桔梗汤"},
    "2": {"jing": "阳明", "organ": "大肠", "desc": "大肠燥结、津液枯竭", "formula": "承气汤类"},
    "3": {"jing": "少阴", "organ": "心", "desc": "心肾不交、虚烦不眠", "formula": "黄连阿胶汤"},
    "4": {"jing": "厥阴", "organ": "肝", "desc": "肝郁化火、血虚风动", "formula": "乌梅丸"},
    "5": {"jing": "少阳", "organ": "胆", "desc": "胆气郁结、胸胁苦满", "formula": "小柴胡汤"},
    "6": {"jing": "少阴", "organ": "肾", "desc": "肾阴不足、水火不济", "formula": "六味地黄丸"},
    "7": {"jing": "阳明", "organ": "胃", "desc": "胃热炽盛、食积不化", "formula": "白虎汤/保和丸"},
    "8": {"jing": "太阴", "organ": "脾", "desc": "脾气虚弱、运化失常", "formula": "四君子汤"},
    "9": {"jing": "太阳", "organ": "膀胱", "desc": "膀胱气化不利、水湿内停", "formula": "五苓散"},
}

# ====== 倪海厦食疗方案 ======
NI_FORMULA_DIET = {
    "0": {"formula": "导赤散", "diet": ["莲子心茶", "苦瓜", "冬瓜汤", "绿豆汤"], "avoid": ["辛辣", "油炸", "咖啡"]},
    "1": {"formula": "桔梗汤", "diet": ["梨", "蜂蜜", "银耳", "百合", "白萝卜"], "avoid": ["生冷", "寒凉瓜果"]},
    "2": {"formula": "承气汤类", "diet": ["香蕉", "菠菜", "芹菜", "红薯", "酸奶"], "avoid": ["辛辣", "油炸", "烧烤"]},
    "3": {"formula": "黄连阿胶汤", "diet": ["莲子", "桂圆", "红枣", "酸枣仁粥", "牛奶"], "avoid": ["咖啡", "浓茶", "辛辣"]},
    "4": {"formula": "乌梅丸", "diet": ["乌梅", "山楂", "玫瑰花茶", "菠菜", "黑木耳"], "avoid": ["酒精", "油炸", "辛辣"]},
    "5": {"formula": "小柴胡汤", "diet": ["陈皮", "山楂", "绿茶", "胡萝卜", "小米粥"], "avoid": ["生冷", "油腻", "甜食"]},
    "6": {"formula": "六味地黄丸", "diet": ["黑豆", "黑芝麻", "核桃", "枸杞", "桑葚", "山药"], "avoid": ["生冷", "辛辣", "熬夜"]},
    "7": {"formula": "白虎汤/保和丸", "diet": ["薏米", "冬瓜", "苦瓜", "绿豆", "莲子"], "avoid": ["辛辣", "油炸", "甜食", "酒精"]},
    "8": {"formula": "四君子汤", "diet": ["山药", "莲子", "芡实", "小米", "南瓜", "红枣"], "avoid": ["生冷", "油腻", "甜食"]},
    "9": {"formula": "五苓散", "diet": ["赤小豆", "冬瓜", "薏米", "玉米须", "茯苓"], "avoid": ["咸味过重", "腌制品"]},
}

# ====== 倪海厦动功建议 ======
NI_EXERCISE = {
    "0": ["饭后散步30分钟", "轻柔拍打小腹", "八段锦\"调理脾胃须单举\""],
    "1": ["深呼吸练习（早午各50次）", "扩胸运动", "太极云手"],
    "2": ["腹式呼吸", "揉腹顺时针36圈", "快走30分钟"],
    "3": ["静坐冥想", "太极拳", "养心拍打法"],
    "4": ["疏肝理气操", "拉筋", "八段锦\"攒拳怒目增气力\""],
    "5": ["胆经拍打（大腿外侧）", "侧卧睡眠", "疏肝利胆操"],
    "6": ["肾保健操（搓腰眼）", "踮脚尖", "八段锦\"背后七颠百病消\""],
    "7": ["饭后散步", "摩腹", "太极拳"],
    "8": ["八段锦\"调理脾胃须单举\"", "按摩足三里", "健脾瑜珈"],
    "9": ["跑步/快走", "拍打膀胱经", "易筋经\"倒拽九牛尾\""],
}


def generate_ni_report(birth_date, birth_time, gender, name=None, location=None, output_dir=None):
    """
    生成倪海厦中医基于命理八字的建议报告

    Args:
        birth_date: 出生日期 YYYY/MM/DD
        birth_time: 时辰
        gender: male/female
        name: 姓名（默认从config.USER_NAME读取）
        location: 出生地（可选）
        output_dir: 输出目录（默认BASE_DIR，即项目根目录）

    Returns:
        (报告路径, 报告内容)
    """
    from biowell.config import USER_NAME, BASE_DIR
    
    if name is None:
        name = USER_NAME
    if output_dir is None:
        output_dir = BASE_DIR
    print(f"\n{'='*50}")
    print(f"  倪海厦中医建议报告生成中...")
    print(f"{'='*50}")

    # 1. 计算命盘
    gender_str = 'male' if gender in ["male", "男"] else 'female'
    gender_text = "男" if gender_str == 'male' else "女"

    r = v5_calc(birth_date, birth_time, gender_str)

    # 检查是否是子时双格
    is_zishi = '阳格1' in r and '阴格1' in r

    yang_que = r.get("阳缺", "")
    yin_que = r.get("阴缺", "")
    yang_ge = r.get("阳格", "")
    yin_ge = r.get("阴格", "")

    if is_zishi:
        yang_que1 = r.get("阳缺1", "")
        yin_que1 = r.get("阴缺1", "")
        yang_ge1 = r.get("阳格1", "")
        yin_ge1 = r.get("阴格1", "")
        zishi_note = r.get("说明", "")
        adj_date = r.get("调整日期", "")
    else:
        yang_que1 = ""
        yin_que1 = ""
        yang_ge1 = ""
        yin_ge1 = ""
        zishi_note = ""
        adj_date = ""

    # 2. 生命周期分析
    lc = r.get("生命周期", {})

    # 3. 阴阳倾向
    yang_yin = r.get("阳格阴阳分析", {})
    if isinstance(yang_yin, str):
        yang_yin = {"阴阳倾向": yang_yin, "解释": ""}
    trend = yang_yin.get("阴阳倾向", "平衡")
    trend_desc = yang_yin.get("解释", "")

    # 4. 计算年龄
    born_dt = datetime.strptime(birth_date.replace('/', '-'), '%Y-%m-%d')
    age = datetime.now().year - born_dt.year

    # 5. 六经辨证分析
    now = datetime.now()
    r_now = v5_calc(now.strftime('%Y/%m/%d'), get_shichen_from_hour(now.hour), gender_str)
    today_yang = r_now.get("阳格", "")
    today_yin = r_now.get("阴格", "")
    today_yang_que = r_now.get("阳缺", "")
    today_yin_que = r_now.get("阴缺", "")

    # ── 当天行运 ∩ 本命命盘 = 共振缺 ──
    # 阴缺共振 = 本命阴缺 ∩ 当天阴缺
    # 阳缺共振 = 本命阳缺 ∩ 当天阳缺
    natal_yq_set = set(yang_que) if yang_que else set()
    natal_iq_set = set(yin_que) if yin_que else set()
    today_yq_set = set(today_yang_que) if today_yang_que else set()
    today_iq_set = set(today_yin_que) if today_yin_que else set()
    
    resonance_yang = natal_yq_set & today_yq_set  # 阳缺共振
    resonance_yin = natal_iq_set & today_iq_set     # 阴缺共振
    resonance_all = resonance_yang | resonance_yin  # 全部共振

    # 合并缺格（子时双格）
    if is_zishi:
        all_yang_que = set(yang_que) | set(yang_que1)
        all_yin_que = set(yin_que) | set(yin_que1)
        all_missing = all_yang_que | all_yin_que
    else:
        all_yang_que = set(yang_que)
        all_yin_que = set(yin_que)
        all_missing = all_yang_que | all_yin_que

    report = []
    report.append("# " + name + " · 倪海厦中医养生建议")
    report.append("")
    report.append("> **说明**：本报告整合九宫格命理分析 + 倪海厦经方体系，从六经辨证角度提供个性化中医养生方案。")
    report.append("> ")
    report.append("> :warning: **免责声明**：以下内容仅供学习参考，如有不适请咨询当地中医师。")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 一、基本信息")
    report.append(f"| 项目 | 内容 |")
    report.append("|:----:|:----|")
    report.append(f"| 姓名 | {name} |")
    report.append(f"| 出生日期 | {birth_date} {birth_time} |")
    report.append(f"| 性别 | {gender_text} |")
    report.append(f"| 年龄 | {age}岁 |")

    # 子时双格显示4个格
    if is_zishi:
        report.append(f"| 命盘类型 | 子时双格 |")
        report.append(f"| 当天格 | 阳格{yang_ge} / 阴格{yin_ge} / 阳缺{yang_que} / 阴缺{yin_que} |")
        report.append(f"| 调整格 | 阳格{yang_ge1} / 阴格{yin_ge1} / 阳缺{yang_que1} / 阴缺{yin_que1} |")
        report.append(f"| 综合缺格 | 阳缺合集{''.join(sorted(all_yang_que))} / 阴缺合集{''.join(sorted(all_yin_que))} |")
        report.append(f"| {zishi_note} | 调整日期: {adj_date} |")
    else:
        report.append(f"| 命盘 | 阳缺{yang_que} / 阴缺{yin_que} |")
    report.append(f"| 今日天时 | {today_yang} / {today_yin} |")
    report.append(f"| 今日行运缺 | 阳缺{today_yang_que} / 阴缺{today_yin_que} |")
    if resonance_all:
        report.append(f"| ⚡ 共振缺 | 阳缺{''.join(sorted(resonance_yang)) if resonance_yang else '无'} / 阴缺{''.join(sorted(resonance_yin)) if resonance_yin else '无'} |")
    else:
        report.append(f"| 共振状态 | 本命与今天无缺格共振，今日相对平稳 |")
    if location:
        report.append(f"| 出生地 | {location} |")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 二、⚡ 当天行运共振分析（为重点照顾）")
    report.append("")
    if resonance_all:
        report.append("> **原理**：当天行运的阴缺/阳缺与本命命盘的阴缺/阳缺产生信息共振时，")
        report.append("> 对应的脏腑经络在今日格外敏感脆弱，需优先养护。")
        report.append("")
        report.append("| 共振数字 | 对应脏腑 | 六经 | 提示 |")
        report.append("|:---:|------|------|------|")
        for num in sorted(resonance_all):
            zf = ZANGFU_MAP.get(num, {"name": "未知", "yin": ""})
            six = SIX_DIVISION_MAP.get(num, {"jing": "未知", "desc": ""})
            # 标注类型
            tags = []
            if num in resonance_yang: tags.append("阳缺共振")
            if num in resonance_yin: tags.append("阴缺共振")
            tag_str = "·".join(tags)
            report.append(f"| **{num}** | {zf['name']} | {six['jing']} | ⚠️ {tag_str} |")
        report.append("")
        report.append("**今日重点照顾建议**：")
        report.append("")
        # 给共振脏腑额外强化建议
        for num in sorted(resonance_all):
            zf = ZANGFU_MAP.get(num, {"name": "未知", "yin": ""})
            org_name = zf['name']
            yin_type = zf.get('yin', '')
            if '阴' in yin_type:
                report.append(f"- **{num}→{org_name}**：避寒就温，可艾灸、姜汤暖胃，忌生冷。")
            elif '阳' in yin_type:
                report.append(f"- **{num}→{org_name}**：疏泄为主，避免情绪压抑，可饮菊花决明茶。")
            else:
                report.append(f"- **{num}→{org_name}**：作息规律，避免过劳，适度按摩。")
        report.append("")
    else:
        report.append("> 今日行运缺格与本命命盘无交集共振，各脏腑经络处于平稳状态。")
        report.append("> 但仍需注意日常养护，不因安稳而放纵。")
        report.append("")
    report.append("---")
    report.append("")
    report.append("## 三、命理脏腑分析")
    report.append("")
    report.append("### 3.1 缺格脏腑（需重点养护）")
    report.append("")

    # 阳缺（子时双格使用合并后的）
    display_yang_que = ''.join(sorted(all_yang_que)) if is_zishi else yang_que
    display_yin_que = ''.join(sorted(all_yin_que)) if is_zishi else yin_que

    if display_yang_que:
        report.append("**阳缺（" + display_yang_que + "）**：")
        for num in display_yang_que:
            zf = ZANGFU_MAP.get(num, {"name": "未知", "yin": ""})
            six = SIX_DIVISION_MAP.get(num, {"jing": "未知", "desc": ""})
            # 标注来自哪套格 + 共振标记
            src = []
            if num in yang_que: src.append("当天")
            if num in yang_que1: src.append("调整")
            if num in resonance_yang: src.append("⚡共振")
            src_str = f" [{'+'.join(src)}]" if src else ""
            report.append(f"- **{num} → {zf['name']}**{src_str}：{six['jing']}，{six['desc']}")
        report.append("")

    # 阴缺
    if display_yin_que:
        report.append("**阴缺（" + display_yin_que + "）**：")
        for num in display_yin_que:
            zf = ZANGFU_MAP.get(num, {"name": "未知", "yin": ""})
            six = SIX_DIVISION_MAP.get(num, {"jing": "未知", "desc": ""})
            # 标注来自哪套格 + 共振标记
            src = []
            if num in yin_que: src.append("当天")
            if num in yin_que1: src.append("调整")
            if num in resonance_yin: src.append("⚡共振")
            src_str = f" [{'+'.join(src)}]" if src else ""
            report.append(f"- **{num} → {zf['name']}**{src_str}：{six['jing']}，{six['desc']}")
        report.append("")

    report.append("### 3.2 当前周期状态")
    report.append("")
    if trend == "平衡":
        report.append("- 当前处于**阴阳平衡期**，适合全面调理")
    elif trend == "阳":
        report.append(f"- 当前处于**阳格期**：{yang_ge}能量为主导，{trend_desc}")
    else:
        report.append(f"- 当前处于**阴格期**：{yin_ge}能量为主导，{trend_desc}")
    report.append("")

    report.append("### 3.3 生命周期（各年龄段重点）")
    report.append("")
    for key, val in lc.items():
        if isinstance(val, float):
            val = round(val, 1)
        report.append(f"- **{key}**：{val}")
    report.append("")
    report.append("---")
    report.append("")

    # 3. 六经辨证与经方建议
    report.append("## 四、六经辨证分析（倪海厦经方体系）")
    report.append("")
    report.append("> 倪海厦老师常说：\"治病必须先明六经辨证，才能对症下药！\"")
    report.append("")

    # 统计涉及的经络（子时双格使用合并后的）
    all_nums = all_missing
    jing_list = []

    for num in sorted(all_nums):
        zf = ZANGFU_MAP.get(num, {"name": "未知", "yin": "未知"})
        six = SIX_DIVISION_MAP.get(num, {"jing": "未知", "formula": "待定", "desc": ""})
        diet = NI_FORMULA_DIET.get(num, {"formula": "待定", "diet": [], "avoid": []})
        exercise = NI_EXERCISE.get(num, [])

        # 共振标记
        rson = "⚡ 今日共振！" if num in resonance_all else ""
        report.append(f"### 4.{len(jing_list) + 1} {zf['name']}（{six['jing']}）{rson}")
        report.append("")
        report.append(f"**六经辨证**：{six['jing']}")
        report.append("")
        report.append(f"**病机分析**：{six['desc']}")
        report.append("")
        report.append(f"**推荐经方**：{six['formula']}")
        report.append("")
        report.append("**食疗方案**：")
        report.append(f"- 宜食：`{'、'.join(diet['diet'][:4])}`")
        report.append(f"- 忌食：`{'、'.join(diet['avoid'])}`")
        report.append("")
        report.append("**动功建议**：")
        for ex in exercise:
            report.append(f"- {ex}")
        report.append("")
        report.append("---")
        report.append("")

        jing_list.append(num)

    # 4. 综合养生方案
    report.append("## 四、综合养生方案（倪海厦六诊养生）")
    report.append("")
    report.append("### 倪师六健康标准自检")
    report.append("")
    report.append("| 标准 | 正常表现 | 自我检测 |")
    report.append("|:----:|:--------:|:--------:|")
    report.append("| 睡眠 | 一觉到天亮 | 入睡困难？易醒？噩梦？ |")
    report.append("| 食欲 | 三餐定时定量 | 食欲不振？暴饮暴食？ |")
    report.append("| 大便 | 每日一次成形 | 便秘？稀溏？不规律？ |")
    report.append("| 小便 | 每日5-7次淡黄 | 尿频？夜尿？浑浊？ |")
    report.append("| 口渴 | 渴而欲饮 | 不渴？多饮？喜冷/热？ |")
    report.append("| 体温 | 手足温热 | 手脚冰凉？发热？ |")
    report.append("")
    report.append("### 日常养生要点")
    report.append("")

    # 根据缺格给出综合建议
    if "6" in all_nums or "9" in all_nums:
        report.append("**肾与膀胱养护**：")
        report.append("- 早睡（23点前）最关键！倪师说：\"熬夜伤肾，这是第一杀手！\"")
        report.append("- 踮脚尖走路，每天50次，刺激肾经")
        report.append("- 搓腰眼（肾俞穴），每天100下")
        report.append("")

    if "3" in all_nums or "0" in all_nums:
        report.append("**心与小肠养护**：")
        report.append("- 中午小憩30分钟，养心阴")
        report.append("- 避免下午剧烈运动耗伤心气")
        report.append("- 莲子心泡水喝，清心火")
        report.append("")

    if "4" in all_nums or "5" in all_nums:
        report.append("**肝与胆养护**：")
        report.append("- 凌晨1-3点是肝经值班，必须熟睡！")
        report.append("- 疏肝理气：拍打肝经（大腿内侧）")
        report.append("- 保持情绪舒畅，怒伤肝！")
        report.append("")

    if "7" in all_nums or "8" in all_nums:
        report.append("**脾与胃养护**：")
        report.append("- 三餐定时，七八分饱")
        report.append("- 饭后散步30分钟，帮助消化")
        report.append("- 倪师强调：\"小米粥是最好的健脾食物！\"")
        report.append("")

    if "1" in all_nums or "2" in all_nums:
        report.append("**肺与大肠养护**：")
        report.append("- 每天深呼吸，早起50次，宣肺气")
        report.append("- 大肠经值班（早5-7点），养成排便习惯")
        report.append("- 白色食物入肺：梨、百合、银耳")
        report.append("")

    # 5. 节气养生
    report.append("### 节气养生提醒")
    report.append("")
    report.append("- **春**：早睡早起，多做户外活动，疏肝为主")
    report.append("- **夏**：晚睡早起，午休养心，清热解暑")
    report.append("- **秋**：早睡早起，润肺生津，适当秋冻")
    report.append("- **冬**：早睡晚起，藏精养肾，保暖防寒")
    report.append("")
    report.append("---")
    report.append("")

    # 6. 穴位保健
    report.append("## 五、常用保健穴位")
    report.append("")
    report.append("| 脏腑 | 推荐穴位 | 按摩方法 |")
    report.append("|:----:|:--------:|:--------:|")
    report.append("| 心 | 神门、内关 | 每穴按揉2分钟 |")
    report.append("| 肝 | 太冲、三阴交 | 每穴按揉3分钟 |")
    report.append("| 脾 | 足三里、阴陵泉 | 每穴按揉2分钟 |")
    report.append("| 肺 | 列缺、太渊 | 每穴按揉2分钟 |")
    report.append("| 肾 | 涌泉、肾俞 | 搓热为宜 |")
    report.append("| 胃 | 中脘、天枢 | 顺时针揉腹 |")
    report.append("")

    # 结尾
    report.append("---")
    report.append("")
    report.append("## 六、结语")
    report.append("")
    report.append("倪海厦老师常说：")
    report.append("")
    report.append("> \"中医的精髓在于治未病！你们要学会倾听身体的声音，在疾病萌芽时就把它解决掉。\"")
    report.append("")
    report.append("本报告结合您的命理特点，建议：")
    report.append("1. **坚持六健康标准自检**，发现问题及时调理")
    report.append("2. **顺应节气养生**，春疏肝、夏清心、秋润肺、冬补肾")
    report.append("3. **缺格脏腑重点养护**，食疗+动功+穴位三管齐下")
    report.append("4. **保持良好生活习惯**，这是养生最重要的！")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    report.append(f"*数据来源：慈海九宫格 + 倪海厦经方体系*")
    report.append("")
    report.append("---")
    report.append(":warning: **免责声明**：本报告仅供学习参考，不能替代专业中医诊断。如有不适，请咨询当地中医师！")

    # 保存报告
    content = "\n".join(report)
    filename = f"倪海厦中医基于{name}命理八字的建议_{birth_date.replace('/', '')}_{birth_time}_v1.0.md"
    # 输出目录：优先使用output_dir，否则使用TOOL_DIR
    out_dir = output_dir if output_dir else TOOL_DIR
    filepath = os.path.join(out_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[OK] 报告已生成：{filename}")
    print(f"[OK] 路径：{filepath}")

    return filepath, content


if __name__ == "__main__":
    import argparse
    from biowell.config import USER_NAME, USER_BIRTH_DATE
    
    parser = argparse.ArgumentParser(description="倪海厦中医建议生成器")
    parser.add_argument("-n", "--name", default=USER_NAME, help="姓名")
    parser.add_argument("-b", "--birth", default=USER_BIRTH_DATE, help="出生日期 YYYY/MM/DD")
    parser.add_argument("-t", "--time", default=None, help="时辰（不填则自动计算）")
    parser.add_argument("-g", "--gender", default="male", help="性别 male/男 或 female/女")
    parser.add_argument("-l", "--location", default=None, help="出生地")

    args = parser.parse_args()

    birth_time = args.time
    if not birth_time:
        # 自动计算真太阳时
        true_solar = get_true_solar_time(args.birth, args.location)
        birth_time = true_solar["shichen"]
        print(f"自动计算时辰：{birth_time}（真太阳时）")

    generate_ni_report(
        birth_date=args.birth,
        birth_time=birth_time,
        gender=args.gender,
        name=args.name,
        location=args.location
    )
