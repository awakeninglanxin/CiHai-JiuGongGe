# -*- coding: utf-8 -*-
"""
食疗动功方案生成器 v3.3
整合"取长补短"原则 + 综合食疗动功 + 时辰活用
升级要点：增加"取长"章节、核心原则分析、详细食疗禁忌、每日执行核心
"""
import sys, os
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))  # 自身所在目录
sys.path.insert(0, TOOL_DIR)
from nine_palace_core_v5 import calc as _v5_calc

# ====== 时辰工具 ======
SHICHEN_LIST = ['子时','丑时','寅时','卯时','辰时','巳时','午时','未时','申时','酉时','戌时','亥时']

def hour_to_shichen(hour):
    if hour == 23:
        return '子时'
    idx = (hour + 1) // 2
    if idx >= 12:
        idx = 11
    return SHICHEN_LIST[idx]

def shichen_time_range(sc):
    idx = SHICHEN_LIST.index(sc) if sc in SHICHEN_LIST else 0
    if idx == 0:
        return '23:00-01:00'
    h_start = idx * 2 - 1
    h_end = idx * 2 + 1
    return f'{h_start:02d}:00-{h_end:02d}:00'

# ====== 脏腑映射 ======
DIGIT_ORGAN = {'1':'肺','2':'大肠','3':'心','4':'肝','5':'胆','6':'肾','7':'胃','8':'脾','9':'膀胱','0':'小肠'}

# ====== 详细修正数据库 ======
REMEDY_DB = {
    '2': {
        '核心':'蔬菜配方（紫色洋葱蒸煮）+ 腹式呼吸 + 律动',
        '方案':['蔬菜配方：紫色洋葱（关键）+西兰花+大白菜，连续34天','律动：每日规律促进肠蠕动','腹式呼吸：每日3组，每组10次'],
        '禁忌':['下午3点后不食肉','严格控制盐摄入','不过量物质性食物'],
        '时辰':'卯时（5-7点）大肠经旺，建议此时段进食清淡'
    },
    '4': {
        '核心':'A杯（晨起空腹）+ 蔬菜配方（西兰花排毒+大白菜降火）',
        '方案':['蔬菜配方：蒸西兰花+大白菜，连续34天','保持适度饥饿感','A杯配合：清晨空腹饮用'],
        '禁忌':['晚上10:30前入睡，睡足10.5小时','严格忌红肉、垃圾食品、碳酸饮料','严禁饮酒'],
        '时辰':'寅时（3-5点）肝经修复，需此时段前入睡'
    },
    '5': {
        '核心':'宁化府饺子醋（饭前15-20分钟，每日20-30克）+ 闭嘴吃饭',
        '方案':['宁化府饺子醋：饭前15-20分钟，每日20-30克','配合蔬菜配方同时调理肝胆','闭嘴吃饭：情绪平稳时进食'],
        '禁忌':['忌高油脂、坚果（胆汁不足难以消化）','闭嘴吃饭：情绪平稳时进食','避免过饱（7分饱）'],
        '时辰':'子时（23-1点）胆经最旺，此时入睡有助胆修复'
    },
    '6': {
        '核心':'黑米套餐 + 动功（熊经鸟伸/枯树盘根）+ 三层补气贴',
        '方案':['黑米套餐：黑米2+黑豆2+核桃1+枸杞1+黄精1份','黑米黑豆需含胚芽并发芽后熬粥，早晚各一份','男性多用黄精，女性多用枸杞','三层补气贴：命门、肾俞贴敷','护腰：尤其冬季和夜间'],
        '禁忌':['不过度纵欲（肾精消耗）','不过度劳累（伤肾气）','不久坐（肾经压迫）'],
        '时辰':'酉时（17-19点）肾经旺，此时进食补肾食物效果最佳'
    },
    '7': {
        '核心':'饮食规律 + 小绿瓶21天 + 小白瓶 + 亲密关系和谐',
        '方案':['饮食规律：三餐定时，不过饥不过饱','家和万事兴：亲密关系和谐对胃有直接补益','小绿瓶21天：修复胃黏膜','伴侣若带7，有天然补益'],
        '禁忌':['修"失去金钱的恐惧"（7与恐惧相关）','不吃过冷过烫食物','不在情绪激动时进食'],
        '时辰':'辰时（7-9点）胃经旺，建议早餐在此时段完成'
    },
    '8': {
        '核心':'河南铁棍山药（带皮蒸）+ 含胚芽谷物 + 严格忌甜食',
        '方案':['河南铁棍山药：带皮蒸食，每日一小段（约10公分）','含胚芽谷物：发芽糙米、发芽黑米、发芽黑豆、青稞','严格忌口所有甜食（白糖/蜂蜜/含糖加工品）'],
        '禁忌':['严格忌口甜食（脾最忌甜）','严格忌口精米精面','不吃过饱（7分饱）','避免含荧光剂白色纸巾（含二氧化钛）'],
        '时辰':'巳时（9-11点）脾经旺，此时进食山药效果佳'
    },
    '9': {
        '核心':'动功（开天门/脊柱疏通）+ 黑豆黑木耳',
        '方案':['开天门：激活顶轮，引肾水上济心火','摇摆脊柱：疏通中脉，刺激背俞穴','黑豆黑木耳：凉拌或炒食，每周3次'],
        '禁忌':['膀胱有疾时减少利尿食物','不憋尿（伤膀胱经）'],
        '时辰':'申时（15-17点）膀胱经旺，可进行脊柱疏通动功'
    },
    '0': {
        '核心':'细嚼慢咽 + 午睡养心阳 + 核桃',
        '方案':['细嚼慢咽：食物在口腔充分消化','午后小憩：11-13点心经旺，养心阳助小肠吸收','核桃：每日2-3颗，温补小肠'],
        '禁忌':['不在午时（11-13点）进食生冷','不吃过快（影响分清泌浊）'],
        '时辰':'未时（13-15点）小肠经旺，午餐宜清淡好消化'
    }
}

# ====== 食疗数据库 ======
FOOD_DB = {
    '1': [('白萝卜','润肺止咳','生吃/煮汤'),('梨','清热润肺','蒸梨/炖汤'),('百合','润肺清心','百合粥'),('银耳','滋阴润肺','银耳羹')],
    '2': [('紫色洋葱','温阳散结（核心）','凉拌/蒸煮'),('芹菜','降压通便','榨汁/凉拌'),('西兰花','疏肝解毒','清炒/蒸'),('大白菜','清热降火','焯水凉拌')],
    '3': [('莲子','清心火安神','莲子粥/蒸'),('红枣','养心血','红枣茶/煮粥'),('苦瓜','清心泻火','苦瓜茶（适量）'),('小白瓶','通心轮核心','按说明服用')],
    '4': [('西兰花','疏肝解毒（核心）','清炒/蒸'),('大白菜','清热降火','焯水凉拌'),('绿茶','清肝明目','每日1-2杯（饭后）'),('A杯','协助肝脏解毒','晨起空腹')],
    '5': [('宁化府饺子醋','利胆消肿（核心）','饭前15分钟20-30克'),('山楂','消食化积','山楂茶（适量）'),('山药','健脾补气','蒸食/煮粥'),('发酵醋','帮助去半魄','配合肉食同用')],
    '6': [('黑米（含胚芽）','补肾益精（核心）','发芽后熬粥早晚各一份'),('黑豆（含胚芽）','补肾活血','发芽后煮/打豆浆'),('核桃','补肾健脑','每日2-3颗'),('枸杞','补肾明目（女）','温水泡/干吃'),('黄精','补气养阴（男）','黄精茶/炖汤'),('黑芝麻','补肾益精','磨粉/煮粥')],
    '7': [('薏米','健脾利湿','薏米粥'),('山药','健脾益胃','蒸食/炒'),('南瓜','补中益气','蒸南瓜'),('小绿瓶','修复胃黏膜（核心）','按21天周期'),('宁化府醋','协助消化','配合肉食同用')],
    '8': [('河南铁棍山药','健脾特效（核心）','带皮蒸每日10cm'),('发芽糙米','含胚芽谷物','发芽后煮粥'),('发芽黑米','补脾补血','发芽后煮粥'),('发芽黑豆','健脾补肾','发芽后煮/打豆浆'),('青稞','健脾去湿','煮粥/打粉')],
    '9': [('海带','软坚散结','凉拌/煮汤'),('冬瓜','清热利水','煮汤（少盐）'),('黑豆','补肾利水','发芽后煮'),('开天门动功','通顶轮（核心）','每日练习')],
    '0': [('黑木耳','补肾活血','凉拌/炒'),('黑芝麻','补肾益精','磨粉/煮粥'),('核桃','温补小肠','每日2-3颗'),('午睡','养心阳助小肠','11-13点小憩20分钟')]
}

# ====== 动功数据库 ======
DONG_GONG_CORE = [
    {'name':'熊经鸟伸','target':'督脉+所有经脉','desc':'疏通全身经脉，升阳气，尤其是督脉','要点':'每天晨起练习，作为所有动功的热身','禁忌':'饭后1小时内不练'},
    {'name':'枯树盘根','target':'肾经/膀胱经/督脉','desc':'补肾气，产生布朗气体通神（连接天地）','要点':'必须先练熊经鸟伸再练此功，防止能量堵在膝盖','禁忌':'膝盖有疾者减小幅度'},
]
DONG_GONG_BADUANJIN = [
    {'name':'两手托天理三焦','target':'三焦经','desc':'疏通三焦，水火交通'},
    {'name':'调理脾胃须单举','target':'脾胃经','desc':'刺激脾胃经，促进胃肠蠕动'},
    {'name':'两手攀足固肾腰','target':'肾经/膀胱经','desc':'刺激肾俞穴命门穴，强腰固肾'},
    {'name':'摇头摆尾去心火','target':'心经/肾经','desc':'交通心肾，清心降火'},
]
DONG_GONG_HUXI = [
    {'name':'逆腹式呼吸','target':'带脉/中脉','desc':'开带脉、补气，引气下行'},
    {'name':'爱的呼吸','target':'心轮/顶轮','desc':'通心轮，改善心神沟通能力'},
]
DONG_GONG_LIANHUA = [
    {'name':'开天门（顶轮激活）','target':'顶轮/三焦','desc':'激活顶轮，引肾水上济心火'},
    {'name':'摇摆脊柱（中脉疏通）','target':'膀胱经/背俞穴','desc':'疏通脊柱，刺激背俞穴'},
    {'name':'观音莲台坐','target':'海底轮','desc':'固本培元，稳固能量根基'},
]

# ====== 行运共振分析 ======
def analyze_yun(day_r, birth_jgg):
    """分析单套行运与命盘的共振"""
    d_yq = set(c for c in day_r.get('阳缺','') if c.isdigit())
    d_iq = set(c for c in day_r.get('阴缺','') if c.isdigit())
    b_yq = set(c for c in birth_jgg.get('阳缺','') if c.isdigit())
    b_iq = set(c for c in birth_jgg.get('阴缺','') if c.isdigit())
    banbu = set(c for c in day_r.get('半补','') if c.isdigit())
    # 一级：天时阳缺∩命盘阳缺，或 天时阴缺∩命盘阴缺
    level1 = sorted((d_yq & b_yq) | (d_iq & b_iq))
    # 二级：天时阳缺∩命盘阴缺，或 天时阴缺∩命盘阳缺
    level2 = sorted((d_yq & b_iq) | (d_iq & b_yq))
    return {
        'day_yang': day_r.get('阳格',''),
        'day_yin': day_r.get('阴格',''),
        'day_yang_que': ''.join(sorted(d_yq)),
        'day_yin_que': ''.join(sorted(d_iq)),
        'day_banbu': ''.join(sorted(banbu)),
        'level1': level1,
        'level2': level2,
        'shichen': day_r.get('时辰',''),
    }

def analyze_yun_dual(day_r, yang_q1, yin_q1, yang_q2, yin_q2):
    """分析子时双格：行运与两套命盘的共振"""
    d_yq = set(c for c in day_r.get('阳缺','') if c.isdigit())
    d_iq = set(c for c in day_r.get('阴缺','') if c.isdigit())
    # 合并两套命盘
    b_yq = set(yang_q1) | set(yang_q2)
    b_iq = set(yin_q1) | set(yin_q2)
    banbu = set(c for c in day_r.get('半补','') if c.isdigit())
    # 一级：天时阳缺∩任一命盘阳缺，或 天时阴缺∩任一命盘阴缺
    level1 = sorted((d_yq & b_yq) | (d_iq & b_iq))
    # 二级：天时阳缺∩命盘阴缺，或 天时阴缺∩命盘阳缺
    level2 = sorted((d_yq & b_iq) | (d_iq & b_yq))
    return {
        'day_yang': day_r.get('阳格',''),
        'day_yin': day_r.get('阴格',''),
        'day_yang_que': ''.join(sorted(d_yq)),
        'day_yin_que': ''.join(sorted(d_iq)),
        'day_banbu': ''.join(sorted(banbu)),
        'level1': level1,
        'level2': level2,
        'shichen': day_r.get('时辰',''),
    }

# ====== 辅助函数 ======
def _grid_organs(grid):
    return '、'.join([DIGIT_ORGAN.get(d,'') for d in grid if d.isdigit()]) if grid else '无'

def _que_organs(que_str):
    return '、'.join([DIGIT_ORGAN.get(d,'') for d in que_str if d.isdigit()]) if que_str else '无'

def _yang_meaning(grid):
    meanings = {'1':'肺气','2':'大肠传导','3':'心神','4':'肝疏','5':'胆决','6':'肾藏','7':'胃纳','8':'脾运','9':'膀胱气化','0':'小肠分清'}
    return '、'.join([meanings.get(d,d) for d in grid if d.isdigit()]) if grid else '无'

def _yin_meaning(grid):
    meanings = {'1':'肺阴','2':'大肠津液','3':'心阴','4':'肝阴','5':'胆阴','6':'肾阴','7':'胃阴','8':'脾阴','9':'三焦水火','0':'心包护心'}
    return '、'.join([meanings.get(d,d) for d in grid if d.isdigit()]) if grid else '无'

# ====== 主生成函数 ======
GENERAL_PROHIBIT = [
    '午后不食肉（尤其蔬菜配方34天期间）',
    '不饮酒（包括药酒）',
    '不吃垃圾食品、糖果、腌制食品',
    '酸性食物摄入控制在20%以内',
    '晚饭后不进食（轻断食原则）',
    '保持早睡（22:30前）与充足睡眠（10.5小时）',
]
DAILY_EXECUTION = {
    '晨起': '空腹A杯（养肝）+ 熊经鸟伸 + 枯树盘根（补肾气）',
    '早餐': '黑米套餐粥（补肾6）+ 蔬菜配方汤（补2/4）',
    '巳时（9-11点）': '脾经旺：铁棍山药一段 + 爱的呼吸/逆腹式呼吸',
    '午餐': '宁化府醋饭前15分钟 + 蔬菜配方 + 清淡肉食',
    '申时（15-17点）': '膀胱经旺：黑芝麻 + 脊柱疏通动功',
    '晚餐': '早吃少吃（19点前），蔬菜为主',
    '酉时（17-19点）': '肾经旺：黑米套餐粥 + 三层补气贴',
    '睡前': '热水泡脚（引火归元）',
    '睡眠': '22:30前入睡，睡足10.5小时（肝胆修复关键期）',
}


def generate_report(name, birth, shichen, gender, output_file=None):
    is_zi = shichen and '子时' in shichen
    now_dt = datetime.now()
    today_str = now_dt.strftime('%Y/%m/%d')
    now_shichen = hour_to_shichen(now_dt.hour)
    now_time_range = shichen_time_range(now_shichen)

    # 命盘
    jgg = _v5_calc(birth, shichen, gender)

    # 检查是否是子时双格
    is_zishi = '阳格1' in jgg and '阴格1' in jgg

    if is_zishi:
        # 子时双格：合并两套格的缺格
        yang_missing = [d for d in jgg.get('阳缺','') if d.isdigit()]
        yin_missing = [d for d in jgg.get('阴缺','') if d.isdigit()]
        yang_missing1 = [d for d in jgg.get('阳缺1','') if d.isdigit()]
        yin_missing1 = [d for d in jgg.get('阴缺1','') if d.isdigit()]
        # 合并两套
        all_yang_missing = sorted(set(yang_missing + yang_missing1))
        all_yin_missing = sorted(set(yin_missing + yin_missing1))
        all_missing = sorted(set(all_yang_missing + all_yin_missing))
        half_sup = [d for d in jgg.get('半补','') if d.isdigit()]
        half_sup1 = [d for d in jgg.get('半补1','') if d.isdigit()]
        zishi_note = jgg.get('说明', '')
        adj_date = jgg.get('调整日期', '')
    else:
        yang_missing = [d for d in jgg.get('阳缺','') if d.isdigit()]
        yin_missing = [d for d in jgg.get('阴缺','') if d.isdigit()]
        all_missing = sorted(set(yang_missing + yin_missing))
        half_sup = [d for d in jgg.get('半补','') if d.isdigit()]
        all_yang_missing = yang_missing
        all_yin_missing = yin_missing

    # 今日行运（全天 + 当前时辰）
    day_all_r = _v5_calc(today_str, shichen, gender)
    day_now_r = _v5_calc(today_str, now_shichen, gender)

    # 子时双格：需要合并两套命盘进行共振分析
    if is_zishi:
        day_all = analyze_yun_dual(day_all_r, yang_missing, yin_missing, yang_missing1, yin_missing1)
        day_now = analyze_yun_dual(day_now_r, yang_missing, yin_missing, yang_missing1, yin_missing1)
    else:
        day_all = analyze_yun(day_all_r, jgg)
        day_now = analyze_yun(day_now_r, jgg)

    R = []

    # ====== 标题 ======
    R.append(f"# {name} · 综合食疗动功方案 v3.3")
    R.append("")
    R.append(f"**生成时间**：{now_dt.strftime('%Y-%m-%d %H:%M')}（{now_shichen} {now_time_range}）")

    # 子时双格显示4个格
    if is_zishi:
        yang_ge = jgg.get('阳格', '')
        yin_ge = jgg.get('阴格', '')
        yang_ge1 = jgg.get('阳格1', '')
        yin_ge1 = jgg.get('阴格1', '')
        banbu = jgg.get('半补', '')
        banbu1 = jgg.get('半补1', '')

        R.append(f"**命盘（子时双格）**：")
        R.append(f"| 类型 | 阳格 | 阴格 | 阳缺 | 阴缺 | 半补 |")
        R.append(f"|:----:|:-----:|:-----:|:-----:|:-----:|:-----:|")
        R.append(f"| 当天格 | {yang_ge} | {yin_ge} | {''.join(yang_missing)} | {''.join(yin_missing)} | {banbu} |")
        R.append(f"| 调整格 | {yang_ge1} | {yin_ge1} | {''.join(yang_missing1)} | {''.join(yin_missing1)} | {banbu1} |")
        R.append(f"> {zishi_note} | 调整日期: {adj_date}")
        R.append(f"> **综合缺格**：{''.join(all_yang_missing)}/{''.join(all_yin_missing)} → {'、'.join([DIGIT_ORGAN.get(d,'') for d in all_missing])}")
    else:
        R.append(f"**命盘**：{birth} {shichen} | 阳缺{''.join(yang_missing)} 阴缺{''.join(yin_missing)} | 半补{''.join(half_sup)}")
    R.append("")
    R.append("---")
    R.append("")

    # ====== 一、取长补短核心原则 ======
    R.append("## 一、取长补短核心原则")
    R.append("")

    R.append("### 1. 取长（利用半补优势）")
    R.append("")
    if half_sup:
        R.append(f"您的命盘**半补数字**：{'、'.join([f'**{d}（{DIGIT_ORGAN.get(d,'')}）**' for d in half_sup])}")
        R.append(f"**当前时辰（{now_shichen}）天时半补**：**{day_now['day_banbu'] or '无'}**")
        R.append("")
        R.append(f"**原理**：半补数字代表当前天时环境中该数字的能量得到额外支持，是当下的**天然优势**。")
        R.append("")
        R.append(f"**当前时辰建议**：")
        for d in half_sup:
            organ = DIGIT_ORGAN.get(d,'')
            fdb = FOOD_DB.get(d,[])
            if fdb:
                fname, feff, fm = fdb[0]
                R.append(f"- **{d}（{organ}）**：此时段适合进食**{fname}**（{feff}，{fm}），或进行{organ}经对应动功")
            R.append(f"  - 💨 **呼吸练习**：逆腹式呼吸或爱的呼吸（通{organ}轮）")
        R.append("")
        overlap = [d for d in half_sup if d in day_now['day_banbu']]
        if overlap:
            R.append(f"**天时半补利用**：命盘半补{d}与天时半补{day_now['day_banbu']}重叠，此时段（{now_time_range}）是调理{d}（{DIGIT_ORGAN.get(d,'')})的**黄金时段**。")
    else:
        R.append("当前无特别半补，参照命盘主导缺格进行日常调理。")
    R.append("")

    R.append("### 2. 补短（补足先天短板）")
    R.append("")

    # 子时双格显示合并后的缺格
    if is_zishi:
        R.append(f"**当天格缺漏**：阳缺**{''.join(yang_missing)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yang_missing])}）、阴缺**{''.join(yin_missing)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yin_missing])}）")
        R.append(f"**调整格缺漏**：阳缺**{''.join(yang_missing1)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yang_missing1])}）、阴缺**{''.join(yin_missing1)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yin_missing1])}）")
        R.append(f"**综合缺格**：阳缺合集**{''.join(all_yang_missing)}**、阴缺合集**{''.join(all_yin_missing)}** → **{'、'.join([DIGIT_ORGAN.get(d,'') for d in all_missing])}**")
    else:
        R.append(f"**命盘缺漏**：阳缺**{''.join(yang_missing)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yang_missing])}）、阴缺**{''.join(yin_missing)}**（{'、'.join([DIGIT_ORGAN.get(d,'') for d in yin_missing])}）")
    R.append("")
    if len(all_missing) <= 2:
        R.append("缺格≤2个，**直接针对性补漏**。")
    else:
        R.append(f"缺格{len(all_missing)}个，涉及多个脏腑，需**系统执行食疗+动功双轨并进**方案。")
    R.append("")
    R.append(f"**行运格的影响**：当前天时阳格**{day_now['day_yang']}**（{_yang_meaning(day_now['day_yang'])}）、阴格**{day_now['day_yin']}**（{_yin_meaning(day_now['day_yin'])}）。")
    R.append("这些能量正在环境中流动，会暂时影响命盘相关数字的特质。**补漏核心仍应围绕命盘固有缺漏进行**。")
    R.append("")

    # ====== 二、现状分析与行运共振 ======
    R.append("---")
    R.append("")
    R.append("## 二、现状分析与行运共振")
    R.append("")

    R.append(f"### 今日（{today_str}）行运与命盘共振")
    R.append("")

    # 子时双格显示两套命盘
    if is_zishi:
        R.append(f"| 数字 | 脏腑 | 今日天时 | 当天格 | 调整格 | 共振 |")
        R.append(f"|:----:|:----:|----------|:------:|:------:|:-----:|")
        for d in [str(i) for i in range(10)]:
            organ = DIGIT_ORGAN.get(d,'')
            d_yq = '阳缺' if d in day_now['day_yang_que'] else ''
            d_iq = '阴缺' if d in day_now['day_yin_que'] else ''
            tianzhi = (d_yq + ' ' + d_iq).strip() if (d_yq or d_iq) else '正常'
            birth_d = "缺" if d in yang_missing or d in yin_missing else "正常"
            birth_d1 = "缺" if d in yang_missing1 or d in yin_missing1 else "正常"
            if d in day_now['level1']:
                res = '🔴 一级'
            elif d in day_now['level2']:
                res = '🟡 二级'
            else:
                res = '⚪ 潜伏'
            R.append(f"| **{d}** | {organ} | {tianzhi} | {birth_d} | {birth_d1} | {res} |")
    else:
        R.append(f"| 数字 | 脏腑 | 今日天时 | 命盘 | 共振 |")
        R.append(f"|:----:|:----:|----------|:------|")
        for d in [str(i) for i in range(10)]:
            in_birth = "命盘缺" if d in yang_missing or d in yin_missing else "命盘正常"
            organ = DIGIT_ORGAN.get(d,'')
            d_yq = '阳缺✓' if d in day_now['day_yang_que'] else ''
            d_iq = '阴缺✓' if d in day_now['day_yin_que'] else ''
            tianzhi = (d_yq + ' ' + d_iq).strip() if (d_yq or d_iq) else '正常'
            if d in day_now['level1']:
                res = '🔴 一级共振'
            elif d in day_now['level2']:
                res = '🟡 二级共振'
            else:
                res = '⚪ 潜伏期'
            R.append(f"| **{d}** | **{organ}** | {tianzhi} | {in_birth} | {res} |")
    R.append("")

    if day_now['level1']:
        R.append(f"**🔴 一级共振器官**（需重点关注）：{', '.join([f'{d}（{DIGIT_ORGAN.get(d,'')})' for d in day_now['level1']])}")
        R.append("> 天时缺格与命盘缺格**同类**（阳缺∩阳缺或阴缺∩阴缺），能量缺口最大，需**优先执行**对应食疗+动功方案。")
        R.append("")
    if day_now['level2']:
        R.append(f"**🟡 二级共振器官**（需留意）：{', '.join([f'{d}（{DIGIT_ORGAN.get(d,'')})' for d in day_now['level2']])}")
        R.append("> 天时缺格与命盘缺格**交叉**（阳缺∩阴缺或阴缺∩阳缺），存在中等能量缺口，需配合日常养护。")
        R.append("")

    R.append(f"### 今日天时九宫格详情")
    R.append("")
    R.append(f"- **天时阳格**：**{day_now['day_yang']}** → {''.join([DIGIT_ORGAN.get(d,'') for d in day_now['day_yang'] if d.isdigit()])}")
    R.append(f"- **天时阴格**：**{day_now['day_yin']}** → {''.join([DIGIT_ORGAN.get(d,'') for d in day_now['day_yin'] if d.isdigit()])}")
    R.append(f"- **天时阳缺**：{day_now['day_yang_que'] or '无'} → {day_now['day_yang_que'] and _que_organs(day_now['day_yang_que']) or '无缺格'}")
    R.append(f"- **天时阴缺**：{day_now['day_yin_que'] or '无'} → {day_now['day_yin_que'] and _que_organs(day_now['day_yin_que']) or '无缺格'}")
    R.append(f"- **天时半补**：{day_now['day_banbu'] or '无'}")
    R.append("")

    # ====== 三、综合食疗建议 ======
    R.append("---")
    R.append("")
    R.append("## 三、综合食疗建议（针对命盘缺漏）")
    R.append("")

    # 优先级标记
    pri = {d:'🔴' for d in day_now['level1']}
    pri.update({d:'🟡' for d in day_now['level2']})

    R.append(f"| 优先级 | 数字 | 脏腑 | 核心食疗方案 | 关键禁忌 |")
    R.append(f"|:-------:|:----:|:----:|-------------|----------|")

    for d in [str(i) for i in range(10)]:
        organ = DIGIT_ORGAN.get(d,'')
        rdb = REMEDY_DB.get(d,{})
        core = rdb.get('核心','对应食疗调理')
        prohibitions = rdb.get('禁忌',[])
        fdb = FOOD_DB.get(d,[])
        food_str = '；'.join([f"{fn}（{feff}）" for fn,feff,fm in fdb[:2]]) if fdb else ''

        # 取前2个禁忌
        pro_str = '；'.join(prohibitions[:2]) if prohibitions else '参照各经脉禁忌'

        R.append(f"| **{pri.get(d,'⚪')}{d}** | **{d}** | **{organ}** | {core}。推荐：{food_str} | {pro_str} |")

    R.append("")
    R.append("### 食疗综合执行要点")
    R.append("")

    if '2' in all_missing or '4' in all_missing:
        R.append(f"**蔬菜配方**（2大肠+4肝联调）：紫色洋葱+西兰花+大白菜，蒸煮，连续34天为基础。")
    if '6' in all_missing:
        R.append(f"**黑米套餐**（6肾核心）：黑米+黑豆+核桃+枸杞+黄精，发芽后熬粥，早晚各一份。")
    if '5' in all_missing:
        R.append(f"**宁化府饺子醋**（5胆核心）：饭前15分钟20-30克，同时有助去半魄。")
    if '8' in all_missing:
        R.append(f"**河南铁棍山药**（8脾特效）：带皮蒸食，每日约10公分段，配合发芽谷物。")
    if '3' in all_missing or half_sup:
        R.append(f"**小白瓶**（3心/通心轮）：按周期服用，配合莲子清心火。")
    R.append("")
    R.append("**通用禁忌**（执行期间严格遵守）：")
    for p in GENERAL_PROHIBIT:
        R.append(f"- {p}")
    R.append("")

    # ====== 四、动功与呼吸练习 ======
    R.append("---")
    R.append("")
    R.append("## 四、动功与呼吸练习建议")
    R.append("")

    R.append("### 核心动功（每日必练）")
    for dg in DONG_GONG_CORE:
        R.append(f"**{dg['name']}**")
        R.append(f"- 目标：{dg['target']}，功效：{dg['desc']}")
        R.append(f"- 要点：{dg['要点']}，禁忌：{dg['禁忌']}")
        R.append("")

    R.append("### 八段锦（辅助经脉调理）")
    for dg in DONG_GONG_BADUANJIN:
        R.append(f"- **{dg['name']}**：{dg['target']}，{dg['desc']}")
    R.append("")

    R.append("### 呼吸练习（每日定时）")
    for dg in DONG_GONG_HUXI:
        R.append(f"- **{dg['name']}**：{dg['target']}，{dg['desc']}")
    R.append("")

    R.append("### 莲花生动功（高级）")
    for dg in DONG_GONG_LIANHUA:
        R.append(f"- **{dg['name']}**：{dg['target']}，{dg['desc']}")
    R.append("")
    R.append("**执行顺序**：熊经鸟伸 → 枯树盘根 → 八段锦 → 呼吸练习")
    R.append("")

    # ====== 五、当前时辰活用建议 ======
    R.append("---")
    R.append("")
    R.append(f"## 五、当前时辰活用建议")
    R.append("")
    R.append(f"**当前时辰**：**{now_shichen}**（{now_time_range}）")
    R.append("")
    R.append(f"- 天时阳格：**{day_now['day_yang']}**（{_yang_meaning(day_now['day_yang'])}）")
    R.append(f"- 天时阴格：**{day_now['day_yin']}**（{_yin_meaning(day_now['day_yin'])}）")
    R.append(f"- 天时半补：**{day_now['day_banbu'] or '无'}**")
    R.append(f"- 天时阳缺：{day_now['day_yang_que'] or '无'} → {day_now['day_yang_que'] and _que_organs(day_now['day_yang_que']) or '无缺格'}")
    R.append(f"- 天时阴缺：{day_now['day_yin_que'] or '无'} → {day_now['day_yin_que'] and _que_organs(day_now['day_yin_que']) or '无缺格'}")
    R.append("")

    R.append(f"**此时段行动建议**：")
    if day_now['level1']:
        for d in day_now['level1']:
            organ = DIGIT_ORGAN.get(d,'')
            fdb = FOOD_DB.get(d,[])
            rdb = REMEDY_DB.get(d,{})
            if fdb:
                fname, feff, fm = fdb[0]
                R.append(f"- 🔴 **优先处理{d}（{organ}）**：此时段适合进食**{fname}**（{feff}，{fm}），或进行{organ}经对应动功")
            if rdb.get('方案'):
                R.append(f"  - 修正要点：{rdb['方案'][0]}")
    if day_now['day_banbu']:
        for d in day_now['day_banbu']:
            if d not in day_now['level1']:
                organ = DIGIT_ORGAN.get(d,'')
                R.append(f"- 💪 **利用半补{d}（{organ}）优势**：此时段{organ}能量最旺，适合进行{organ}经对应动功或呼吸练习")
    if not day_now['level1'] and not day_now['day_banbu']:
        R.append("- 📊 当前时辰能量平稳，进行日常呼吸练习和轻微动功即可")
    R.append("")

    # ====== 六、每日执行核心 ======
    R.append("---")
    R.append("")
    R.append("## 六、每日执行核心（精简版）")
    R.append("")
    for slot, action in DAILY_EXECUTION.items():
        R.append(f"- **{slot}**：{action}")
    R.append("")
    if day_now['level1']:
        R.append(f"**本周重点**：一级共振器官 {', '.join([f'{d}（{DIGIT_ORGAN.get(d,'')})' for d in day_now['level1']])} 需每日重点执行对应食疗+动功方案。")
    R.append("")
    R.append("---")
    R.append("")
    R.append(f"*报告生成：{now_dt.strftime('%Y-%m-%d %H:%M')} · v3.3 · 基于nine_palace_core_v5*")

    report_text = '\n'.join(R)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"报告已生成：{output_file}")

    return report_text


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='食疗动功方案生成器 v3.3')
    p.add_argument('birth', help='YYYY/MM/DD')
    p.add_argument('-s','--shichen', default='未知')
    p.add_argument('-g','--gender', default='male')
    p.add_argument('-o','--output')
    p.add_argument('-n','--name', default='蓝馨')
    args = p.parse_args()
    gender = 'male' if args.gender in ['male','男'] else 'female'
    output = args.output or f'{args.name}_食疗动功_{args.shichen}_{datetime.now().strftime("%Y%m%d")}.md'
    text = generate_report(args.name, args.birth, args.shichen, gender, output)
    print(f"报告长度：{len(text)} 字符")
