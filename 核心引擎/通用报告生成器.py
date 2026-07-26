# -*- coding: utf-8 -*-
"""
九宫格通用报告生成器 v1.0
支持：姓名、性别、出生日期(年月日+时辰)、出生地点(可选)
功能：自动计算真太阳时、生成命理报告和食疗动功报告
"""
import sys, os, subprocess
from datetime import datetime, timedelta
from math import radians, sin, cos, tan, asin, degrees

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)
from nine_palace_core_v5 import calc as v5_calc

# ====== 中国主要城市经纬度数据库 ======
CITY_COORDS = {
    # 华北
    '北京': (39.9042, 116.4074),
    '天津': (39.3434, 117.3616),
    '石家庄': (38.0428, 114.5149),
    '太原': (37.8706, 112.5489),
    '呼和浩特': (40.8414, 111.7519),
    # 东北
    '沈阳': (41.8057, 123.4328),
    '长春': (43.8171, 125.3235),
    '哈尔滨': (45.8038, 126.5340),
    # 华东
    '上海': (31.2304, 121.4737),
    '南京': (32.0603, 118.7969),
    '杭州': (30.2741, 120.1551),
    '合肥': (31.8612, 117.2830),
    '福州': (26.0745, 119.2965),
    '南昌': (28.6820, 115.8579),
    '济南': (36.6512, 117.1201),
    # 华中
    '郑州': (34.7466, 113.6254),
    '武汉': (30.5928, 114.3055),
    '长沙': (28.2282, 112.9388),
    # 华南
    '广州': (23.1291, 113.2644),
    '南宁': (22.8170, 108.3665),
    '海口': (20.0444, 110.1999),
    '深圳': (22.5431, 114.0579),
    # 西南
    '重庆': (29.5630, 106.5516),
    '成都': (30.5728, 104.0668),
    '贵阳': (26.6470, 106.6302),
    '昆明': (25.0406, 102.7129),
    '拉萨': (29.6500, 91.1000),
    # 西北
    '西安': (34.3416, 108.9398),
    '兰州': (36.0611, 103.8343),
    '西宁': (36.6232, 101.7782),
    '银川': (38.4872, 106.2309),
    '乌鲁木齐': (43.8256, 87.6168),
    # 港澳台
    '香港': (22.3193, 114.1694),
    '澳门': (22.1987, 113.5439),
    '台北': (25.0330, 121.5654),
}

# ====== 时辰工具 ======
SHICHEN_LIST = ['子时','丑时','寅时','卯时','辰时','巳时','午时','未时','申时','酉时','戌时','亥时']

def get_shichen_from_hour(hour):
    """根据小时数获取时辰"""
    if hour == 23 or hour < 1:
        return '子时'
    idx = (hour + 1) // 2
    if idx >= 12:
        idx = 11
    return SHICHEN_LIST[idx]

def parse_shichen(shichen_str):
    """解析时辰字符串"""
    if not shichen_str:
        return '巳时'
    shichen_str = shichen_str.strip()
    for sc in SHICHEN_LIST:
        if sc in shichen_str:
            return sc
    return '巳时'

# ====== 真太阳时计算 ======
def calc_true_solar_time(birth_datetime, latitude, longitude, timezone=8):
    """计算真太阳时"""
    standard_lon = timezone * 15
    lon_diff = longitude - standard_lon
    day_of_year = birth_datetime.timetuple().tm_yday
    B = 2 * 3.14159 * (day_of_year - 81) / 365
    EoT = 9.87 * sin(2*B) - 7.53 * cos(B) - 1.5 * sin(B)
    time_diff = lon_diff * 4 + EoT
    adjusted = birth_datetime + timedelta(minutes=time_diff)
    true_shichen = get_shichen_from_hour(adjusted.hour)
    return adjusted, true_shichen, round(time_diff, 1)

def parse_birth_info(birth_str):
    """解析出生日期字符串"""
    birth_str = birth_str.strip().replace('/', '-').replace('.', '-')
    if len(birth_str) == 8 and birth_str.isdigit():
        birth_str = f"{birth_str[:4]}-{birth_str[4:6]}-{birth_str[6:8]}"
    try:
        return datetime.strptime(birth_str, '%Y-%m-%d')
    except:
        try:
            return datetime.strptime(birth_str, '%Y-%m-%d %H:%M')
        except:
            return None

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

# ====== 脏腑映射 ======
ZANGFU = {"0":"小肠","1":"肺","2":"大肠","3":"心","4":"肝","5":"胆","6":"肾","7":"胃","8":"脾","9":"膀胱"}
CORRECTIONS = {"0":"分清泌浊","1":"多做深呼吸","2":"腹式呼吸+蔬菜配方","3":"通心轮（小白瓶）","4":"A杯+蔬菜配方","5":"宁化府饺子醋","6":"黑米套餐+动功","7":"小绿瓶+情感和谐","8":"铁棍山药+忌甜食","9":"开天门+黑豆黑木耳"}

# ====== 主报告生成函数 ======
def generate_mingli_report(name, date_str, shichen, gender_code, gender_text, location_info=""):
    """生成命理报告"""
    r = v5_calc(date_str, shichen, gender_code)
    yang_que = r.get("阳缺", "")
    yin_que = r.get("阴缺", "")
    yang_yin = r.get("阳格阴阳分析", {})
    if isinstance(yang_yin, str):
        yang_yin = {"阴阳倾向": yang_yin, "解释": ""}
    trend = yang_yin.get("阴阳倾向", "平衡")
    trend_desc = yang_yin.get("解释", "")
    
    now_dt = datetime.now()
    born_dt = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d')
    age = now_dt.year - born_dt.year - ((now_dt.month, now_dt.day) < (born_dt.month, born_dt.day))
    
    report = []
    report.append(f"# {name} · 综合命理报告")
    report.append("")
    report.append(f"**生辰**: {date_str} {shichen}")
    report.append(f"**性别**: {gender_text}")
    report.append(f"**生成时间**: {now_dt.strftime('%Y-%m-%d %H:%M')} | **年龄**: {age}岁")
    report.append(f"**命盘**: 阳缺{yang_que} | 阴缺{yin_que}")
    if location_info:
        report.append(f"**出生地**: {location_info}")
    report.append("")
    report.append("---")
    
    soul = r.get("灵魂", {}) or {}
    soul_n = soul.get("n", "")
    soul_t = soul.get("t", "")
    report.append("## 一、基本信息")
    report.append(f"- **灵魂**: {soul_n}（{soul_t}）")
    report.append(f"- **半补**: {r.get('半补', '')}")
    report.append(f"- **阳格**: {r.get('阳格', '')}")
    report.append(f"- **阴格**: {r.get('阴格', '')}")
    report.append(f"- **阳缺**: {yang_que}")
    report.append(f"- **阴缺**: {yin_que}")
    report.append("- **生命周期**:")
    lc = r.get("生命周期", {})
    for key in lc:
        v = lc[key]
        if isinstance(v, float): v = round(v, 1)
        if isinstance(v, dict): v = v.get("desc", str(v))
        report.append(f"- **{key}**: {v}")
    
    report.append("")
    report.append("---")
    report.append("## 二、阴阳格周期")
    if trend == "平衡":
        report.append("您的阳格和阴格处于**平衡期**，阴阳同调为佳。")
    elif trend == "阳":
        report.append(f"当前处于**阳格期**：以{r.get('阳格','')}为主导能量。{trend_desc}")
    else:
        report.append(f"当前处于**阴格期**：以{r.get('阴格','')}为主导能量。{trend_desc}")
    
    report.append("")
    report.append("---")
    report.append("## 三、缺格修正方案")
    for num in sorted(set(yang_que+yin_que)):
        organ = ZANGFU.get(num, "未知")
        desc = CORRECTIONS.get(num, "对应食疗动功调理")
        report.append(f"**{num}（{organ}）**: {desc}")
    
    report.append("")
    report.append("---")
    report.append("## 四、今日行运分析")
    today = datetime.now()
    r_today = v5_calc(today.strftime('%Y/%m/%d'), get_shichen_from_hour(today.hour), gender_code)
    day_yang = r_today.get("阳格", "")
    day_yin = r_today.get("阴格", "")
    day_organs_yang = "、".join([ZANGFU.get(n, "?") for n in day_yang]) if day_yang else "无"
    day_organs_yin = "、".join([ZANGFU.get(n, "?") for n in day_yin]) if day_yin else "无"
    report.append(f"- **今日日期**: {today.strftime('%Y/%m/%d')} {get_shichen_from_hour(today.hour)}")
    report.append(f"- **今日阳格**: {day_yang} （对应脏腑：{day_organs_yang}）")
    report.append(f"- **今日阴格**: {day_yin} （对应脏腑：{day_organs_yin}）")
    
    mingli_content = "\n".join(report)
    mingli_path = os.path.join(TOOL_DIR, f"{name}命理报告_{date_str.replace('/','')}_{shichen}_v1.0.md")
    with open(mingli_path, "w", encoding="utf-8") as f:
        f.write(mingli_content)
    return mingli_path

def generate_shiliao_report(name, date_str, shichen, gender_code):
    """生成食疗动功精简报告"""
    r = v5_calc(date_str, shichen, gender_code)
    yang_missing = [d for d in r.get('阳缺','') if d.isdigit()]
    yin_missing = [d for d in r.get('阴缺','') if d.isdigit()]
    all_missing = sorted(set(yang_missing + yin_missing))
    half_sup = [d for d in r.get('半补','') if d.isdigit()]
    
    now_dt = datetime.now()
    today_str = now_dt.strftime('%Y/%m/%d')
    now_shichen = get_shichen_from_hour(now_dt.hour)
    
    # 今日行运
    r_today = v5_calc(today_str, now_shichen, gender_code)
    
    R = []
    R.append(f"# {name} · 综合食疗动功方案")
    R.append("")
    R.append(f"**生成时间**：{now_dt.strftime('%Y-%m-%d %H:%M')}（{now_shichen}）")
    R.append(f"**命盘**：{date_str} {shichen} | 阳缺{''.join(yang_missing)} | 阴缺{''.join(yin_missing)} | 半补{''.join(half_sup)}")
    R.append("")
    R.append("---")
    
    # 取长补短
    R.append("## 一、取长补短核心原则")
    R.append("")
    if half_sup:
        R.append(f"**半补数字**：{''.join(half_sup)}")
        hb_names = {"1":"肺","2":"大肠","3":"心","4":"肝","5":"胆","6":"肾","7":"胃","8":"脾","9":"膀胱","0":"小肠"}
        hb_organs = "、".join([hb_names.get(d,d) for d in half_sup if d.isdigit()])
        R.append(f"**半补脏腑**：{hb_organs}")
        R.append(f"**原理**：半补数字代表当前天时环境中该数字的能量得到额外支持。")
    R.append("")
    R.append(f"**命盘缺格**：阳缺{''.join(yang_missing)}、阴缺{''.join(yin_missing)}")
    R.append(f"**涉及脏腑**：{', '.join([ZANGFU.get(d,'?') for d in all_missing])}")
    R.append("")
    R.append("---")
    
    # 缺格修正
    R.append("## 二、缺格修正方案")
    R.append("")
    for num in all_missing:
        organ = ZANGFU.get(num, "?")
        desc = CORRECTIONS.get(num, "对应食疗动功调理")
        R.append(f"**{num}（{organ}）**: {desc}")
    R.append("")
    R.append("---")
    
    # 今日行运
    R.append("## 三、今日行运分析")
    R.append("")
    day_yang = r_today.get("阳格", "")
    day_yin = r_today.get("阴格", "")
    day_yang_q = r_today.get("阳缺", "")
    day_yin_q = r_today.get("阴缺", "")
    R.append(f"- **今日阳格**: {day_yang} → 旺：{', '.join([ZANGFU.get(d,'?') for d in day_yang])}")
    R.append(f"- **今日阴格**: {day_yin} → 旺：{', '.join([ZANGFU.get(d,'?') for d in day_yin])}")
    R.append(f"- **今日阳缺**: {day_yang_q or '无'}")
    R.append(f"- **今日阴缺**: {day_yin_q or '无'}")
    R.append("")
    R.append("---")
    
    # 通用禁忌
    R.append("## 四、通用禁忌")
    R.append("")
    prohibitions = [
        "午后不食肉",
        "不饮酒（包括药酒）",
        "不吃垃圾食品、糖果、腌制食品",
        "晚饭后不进食",
        "保持早睡（22:30前）"
    ]
    for p in prohibitions:
        R.append(f"- {p}")
    R.append("")
    R.append(f"*报告生成：{now_dt.strftime('%Y-%m-%d %H:%M')} · v1.0 · 基于nine_palace_core_v5*")
    
    shiliao_content = "\n".join(R)
    shiliao_path = os.path.join(TOOL_DIR, f"{name}_食疗动功_{now_dt.strftime('%Y%m%d')}.md")
    with open(shiliao_path, "w", encoding="utf-8") as f:
        f.write(shiliao_content)
    return shiliao_path

def generate_all_reports(name, gender, birth_date, shichen=None, location=None):
    """生成所有报告"""
    # 解析性别
    gender_code = 'male' if gender in ['male', '男'] else 'female'
    gender_text = '男' if gender_code == 'male' else '女'
    
    # 解析出生日期
    birth_dt = parse_birth_info(birth_date)
    if not birth_dt:
        print(f"[ERROR] 无效的出生日期: {birth_date}")
        return None
    
    date_str = birth_dt.strftime('%Y/%m/%d')
    
    # 真太阳时计算
    final_shichen = shichen
    location_info = ""

    if not final_shichen:
        if location:
            coords = lookup_city_coords(location)
            if coords:
                lat, lon = coords
                adj_dt, true_shichen, diff = calc_true_solar_time(birth_dt, lat, lon)
                final_shichen = true_shichen
                location_info = f"{location} ({lat}°, {lon}°) | 真太阳时差: {diff}分钟"
            else:
                final_shichen = "巳时"  # 无法识别地点时使用默认巳时
                location_info = f"{location} (无法识别，使用默认巳时)"
        else:
            # 没有时辰也没有地点时，必须要求用户提供！
            print("[ERROR] 请提供时辰(-s)或出生地点(-l)！")
            print("示例：python 通用报告生成器.py -s 巳时")
            print("示例：python 通用报告生成器.py -l 深圳")
            return None
    else:
        final_shichen = parse_shichen(final_shichen)
        if location:
            coords = lookup_city_coords(location)
            if coords:
                lat, lon = coords
                adj_dt, true_shichen, diff = calc_true_solar_time(birth_dt, lat, lon)
                location_info = f"{location} ({lat}°, {lon}°) | 真太阳时差: {diff}分钟"
            else:
                location_info = location
        else:
            location_info = "未提供出生地"
    
    print(f"="*50)
    print(f"基本信息")
    print(f"="*50)
    print(f"姓名: {name}")
    print(f"性别: {gender_text}")
    print(f"出生日期: {date_str}")
    print(f"原始时辰: {shichen or '未指定'}")
    print(f"计算时辰: {final_shichen}")
    print(f"地点信息: {location_info}")
    print(f"="*50)
    
    # 生成命理报告
    print(f"\n生成命理报告...")
    try:
        mingli_path = generate_mingli_report(name, date_str, final_shichen, gender_code, gender_text, location_info)
        print(f"命理报告: {mingli_path}")
    except Exception as e:
        print(f"[ERROR] 命理报告生成失败: {e}")
        mingli_path = None
    
    # 生成食疗动功报告
    print(f"\n生成食疗动功报告...")
    try:
        shiliao_path = generate_shiliao_report(name, date_str, final_shichen, gender_code)
        print(f"食疗动功报告: {shiliao_path}")
    except Exception as e:
        print(f"[ERROR] 食疗动功报告生成失败: {e}")
        shiliao_path = None
    
    return {
        'name': name,
        'gender': gender_text,
        'birth_date': date_str,
        'shichen': final_shichen,
        'location': location_info,
        'mingli_report': mingli_path,
        'shiliao_report': shiliao_path
    }

# ====== 命令行入口 ======
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='九宫格通用报告生成器 v1.0 - 支持真太阳时计算',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（默认蓝馨信息）
  python 通用报告生成器.py

  # 指定生日和性别
  python 通用报告生成器.py -b "1991/08/16" -g "男" -s "辰时"

  # 完整参数（自动计算真太阳时）
  python 通用报告生成器.py -n "张三" -b "1990/05/20" -g "女" -l "上海"

  # 使用经纬度
  python 通用报告生成器.py -n "李四" -b "1985/03/15" -l "30.5,114.3"
        """
    )
    
    parser.add_argument('-n', '--name', default='蓝馨', help='姓名')
    parser.add_argument('-b', '--birth', default='1991/08/16', help='出生日期 YYYY/MM/DD')
    parser.add_argument('-s', '--shichen', default=None, help='时辰（不填则自动计算真太阳时）')
    parser.add_argument('-g', '--gender', default='male', help='性别 male/男 或 female/女')
    parser.add_argument('-l', '--location', default=None, help='出生地点（城市名/省份/经纬度）')
    
    args = parser.parse_args()
    
    print(f"\n{'='*50}")
    print(f"九宫格通用报告生成器 v1.0")
    print(f"{'='*50}\n")
    
    result = generate_all_reports(
        name=args.name,
        gender=args.gender,
        birth_date=args.birth,
        shichen=args.shichen,
        location=args.location
    )
    
    if result:
        print(f"\n{'='*50}")
        print(f"全部报告生成完成!")
        print(f"{'='*50}")
