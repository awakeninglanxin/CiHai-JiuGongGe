# -*- coding: utf-8 -*-
"""
慈海九宫格完整计算器 v5.0
来源: IMA"卢先生经典语录资料包"
更新时间: 2026-03-30
新增功能：
- 性别输入（必需）
- 阴阳格周期切换计算
- 数字阴阳属性：阴(脏)13468 / 阳(腑)25790
"""
import sys, json as jsonmod
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass
from collections import Counter
from datetime import datetime, timedelta
try:
    from lunarcalendar import Converter, Solar
    HAS_LUNAR = True
except:
    HAS_LUNAR = False

# ═══════════════════════════════════════════════════════════════
# 数字阴阳属性（卢先生体系）
# ═══════════════════════════════════════════════════════════════
DIGIT_YIN = {'1':'肺','3':'心','4':'肝','6':'肾','8':'脾'}  # 阴（五脏）
DIGIT_YANG = {'2':'大肠','5':'胆','7':'胃','9':'膀胱','0':'小肠'}  # 阳（六腑）

# ═══════════════════════════════════════════════════════════════
# 阴阳格周期参数（卢先生体系）
# ═══════════════════════════════════════════════════════════════
CYCLE_PARAMS = {
    'male': {
        'yang_years': 11.9,   # 男性阳格周期
        'yin_years': 9.7,     # 男性阴格周期
        'transition': 2.3,    # 换魂过渡期
        'desc': '男性固定周期制'
    },
    'female': {
        'yang_years': 9.7,    # 女性阳格周期
        'yin_years': 11.9,    # 女性阴格周期
        'transition': 2.3,    # 换魂过渡期
        'desc': '女性生育影响制'
    }
}

def calc_life_cycle(birth_year, gender, current_year=None, has_children=False, children_count=0):
    """
    计算阴阳格生命周期
    
    参数:
        birth_year: 出生年份
        gender: 'male' 或 'female'
        current_year: 当前年份（默认今年）
        has_children: 是否生育（仅女性有效）
        children_count: 孩子数量（仅女性有效）
    
    返回:
        dict: 包含当前阶段、年龄、下次换魂等信息
    """
    if current_year is None:
        current_year = datetime.now().year
    
    age = current_year - birth_year
    params = CYCLE_PARAMS[gender]
    yang_y = params['yang_years']
    yin_y = params['yin_years']
    trans = params['transition']
    
    cycles = []
    current_age = 0
    cycle_num = 0
    
    # 构建周期表
    while current_age < 120:
        # 阳格
        cycles.append({
            'phase': f'阳格{cycle_num+1}',
            'start': current_age,
            'end': current_age + yang_y,
            'type': '阳格'
        })
        current_age += yang_y
        
        # 换魂
        cycles.append({
            'phase': f'换魂{cycle_num+1}',
            'start': current_age,
            'end': current_age + trans,
            'type': '换魂'
        })
        current_age += trans
        
        # 阴格
        cycles.append({
            'phase': f'阴格{cycle_num+1}',
            'start': current_age,
            'end': current_age + yin_y,
            'type': '阴格'
        })
        current_age += yin_y
        
        # 换魂
        cycles.append({
            'phase': f'换魂{cycle_num+2}',
            'start': current_age,
            'end': current_age + trans,
            'type': '换魂'
        })
        current_age += trans
        
        cycle_num += 1
    
    # 找到当前阶段
    current_phase = None
    for c in cycles:
        if c['start'] <= age < c['end']:
            current_phase = c
            break
    
    # 找到下一个换魂期
    next_transition = None
    for c in cycles:
        if c['type'] == '换魂' and c['start'] > age:
            next_transition = c
            break
    
    return {
        '年龄': age,
        '当前阶段': current_phase['phase'] if current_phase else '未知',
        '当前类型': current_phase['type'] if current_phase else '未知',
        '当前阶段开始': current_phase['start'] if current_phase else 0,
        '当前阶段结束': current_phase['end'] if current_phase else 0,
        '下次换魂': next_transition['phase'] if next_transition else '无',
        '下次换魂年龄': next_transition['start'] if next_transition else 0,
        '距下次换魂': (next_transition['start'] - age) if next_transition else 0,
        '周期参数': params
    }

def get_digit_yin_yang(digit):
    """获取数字的阴阳属性"""
    d = str(digit)
    if d in DIGIT_YIN:
        return {'属性': '阴（脏）', '脏腑': DIGIT_YIN[d]}
    elif d in DIGIT_YANG:
        return {'属性': '阳（腑）', '脏腑': DIGIT_YANG[d]}
    return {'属性': '未知', '脏腑': '未知'}

def analyze_grid_yin_yang(grid):
    """分析格子的阴阳分布"""
    yin_count = 0
    yang_count = 0
    yin_digits = []
    yang_digits = []
    
    for d in str(grid):
        if d in DIGIT_YIN:
            yin_count += 1
            yin_digits.append(f"{d}({DIGIT_YIN[d]})")
        elif d in DIGIT_YANG:
            yang_count += 1
            yang_digits.append(f"{d}({DIGIT_YANG[d]})")
    
    total = yin_count + yang_count
    if total == 0:
        tendency = '无'
    else:
        yin_ratio = yin_count / total
        if yin_ratio > 0.6:
            tendency = '偏阴'
        elif yin_ratio < 0.4:
            tendency = '偏阳'
        else:
            tendency = '平衡'
    
    return {
        '阴数': yin_count,
        '阳数': yang_count,
        '阴数字': yin_digits,
        '阳数字': yang_digits,
        '阴阳倾向': tendency
    }

# ═══════════════════════════════════════════════════════════════
# 灵魂数据库（保持不变）
# ═══════════════════════════════════════════════════════════════
SOUL_DB = {
    '033393':{'s':'★★★★★+','l':'先天神圣本源（十二维+）','n':'太上老君','d':'全知全觉者，道家最高神','t':'道法自然、与宇宙合一','m':'开道传法','n2':'极罕见'},
    '0123':{'s':'★★★★★','l':'先天神圣本源','n':'最强大心神','d':'改写物理场','t':'心灵感应','m':'创造新维度','n2':'伏羲女娲'},
    '0161181':{'s':'★★★★★','l':'先天神圣本源','n':'玉皇+统帅双主魂','d':'最高神圣本源','t':'宇宙治理','m':'统领多维度','n2':'极罕见'},
    '1325101':{'s':'★★★★☆','l':'多维创世管理层','n':'新维度播种玉皇','d':'新维度播种任务','t':'维度创造','m':'播种生命','n2':'创世管理层'},
    '12433101':{'s':'★★★★☆','l':'多维创世管理层','n':'新维度播种玉皇','d':'维度播种','t':'播种协调','m':'维度创造','n2':'创世管理层'},
    '0262101':{'s':'★★★★☆','l':'多维创世管理层','n':'新一代玉皇','d':'先天童子七魂','t':'维度播种','m':'新维度演化','n2':'先天童子体系'},
    '946101':{'s':'★★★★☆','l':'多维创世管理层','n':'宇宙拆迁总工程师','d':'旧结构拆迁重建','t':'系统重组','m':'宇宙拆解重建','n2':'维度更替'},
    '939123':{'s':'★★★★','l':'多维创世管理层','n':'天琴萨满院长','d':'天琴座高维萨满','t':'萨满教导','m':'星际灵性教育','n2':'天琴座连接'},
    '019101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'一清玉皇先天体','d':'一清层次先天童子','t':'清净心','m':'一清修行','n2':'先天童子入门'},
    '028101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'二清玉皇先天体','d':'二清层次先天童子','t':'二重清净','m':'二清修行','n2':'先天童子进阶'},
    '37101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'37101系列','d':'三魂七魄完整配置','t':'三魂七魄协调','m':'完成先天序列','n2':'核心先天童子'},
    '737101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'737101净化版','d':'37101净化','t':'纯净三魂七魄','m':'净化修行','n2':'净化优于原版'},
    '1937101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'1937101净化版','d':'净化版本','t':'纯净结构','m':'净化修行','n2':'净化优于原版'},
    '46101':{'s':'★★★☆☆','l':'先天童子（七维）','n':'46101系列','d':'四六配置与肝胆相关','t':'肝胆协调','m':'肝胆系统','n2':'木系统相关'},
    '029112':{'s':'★★★☆☆','l':'先天童子（七维）','n':'先天财富显化体','d':'29112净化版','t':'财富显化','m':'财富修行','n2':'净化29112'},
    '29112':{'s':'★★★☆☆','l':'先天童子（七维）','n':'图特/宇宙记录官','d':'后天未净化','t':'记录能力','m':'记录因果','n2':'宇宙档案管理员'},
    '102191011':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'十魂先天童子','d':'十魂配置','t':'多魂协调','m':'多魂协作','n2':'后天精英较高级'},
    '938112':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'938112系列','d':'多魂后天','t':'多魂协调','m':'后天任务','n2':'后天精英'},
    '19381121':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'19381121','d':'多魂天琴萨满','t':'多魂+天琴','m':'跨维度','n2':'后天精英'},
    '838112':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'838112','d':'多魂后天配置','t':'多魂协调','m':'后天修行','n2':'后天精英'},
    '7437':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'7437系列','d':'财富+协调后天','t':'财富+协调','m':'财富修行','n2':'后天精英'},
    '437':{'s':'★★★☆☆','l':'先天童子（七维）','n':'437先天财神','d':'先天财神配置','t':'先天财富吸引','m':'先天福报','n2':'优于347'},
    '325':{'s':'★★★☆☆','l':'先天童子（七维）','n':'取经唐僧','d':'325是现在的主角','t':'取经使命','m':'完成取经','n2':'325时代'},
    '347':{'s':'★★★☆☆','l':'先天童子（七维）','n':'347牛魔王后天财神','d':'后天财神≈南极仙翁','t':'后天财富创造','m':'创造财富','n2':'需努力获得'},
    '123':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'大心神基础体','d':'0123后天版','t':'心神协调','m':'心神修行','n2':'0123后天'},
    '213':{'s':'★★★☆☆','l':'多魂后天精英（五维）','n':'大心神逆位局','d':'逆位版本跨维度疗愈','t':'逆位心智','m':'疗愈','n2':'疗愈能力强'},
    '112':{'s':'★★☆☆☆','l':'多魂后天精英（五维）','n':'天地人财神','d':'三才配置财神','t':'三维财富协调','m':'财富矩阵','n2':'财富矩阵专家'},
    '219101':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'玉皇组','d':'玉皇基础配置','t':'初步玉皇能量','m':'基础任务','n2':''},
    '1191011':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'玉皇组','d':'玉皇组变体','t':'玉皇能量','m':'基础协调','n2':''},
    '19101':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'玉皇组','d':'占人口约8%','t':'玉皇能量','m':'基础任务','n2':'占人口8%'},
    '01202':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'服务执行组','d':'服务执行系列','t':'执行能力','m':'执行任务','n2':''},
    '0202':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'服务执行组','d':'服务执行标准','t':'执行服务','m':'执行任务','n2':''},
    '09303':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'心神统帅组','d':'心神统帅系列','t':'心神控制','m':'心神管理','n2':''},
    '19303':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'心神统帅组','d':'心神统帅变体','t':'心神能力','m':'心神管理','n2':''},
    '09347':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'财富天使组','d':'财富天使系列','t':'财富感知','m':'财富任务','n2':''},
    '9347':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'财富天使组','d':'财富天使标准','t':'财富能量','m':'财富任务','n2':''},
    '666336':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'特殊功能组','d':'六六六系列','t':'特殊功能','m':'特定功能','n2':''},
    '1336':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'特殊功能组','d':'一三三六配置','t':'特殊能力','m':'特定任务','n2':''},
    '1134':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'权威课题系列','d':'权威属性需处理','t':'权威领导力','m':'处理权威课题','n2':'需重点清理'},
    '0134':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'先天净化系列','d':'已经净化清理','t':'净化能力','m':'先天净化','n2':'净化优于原版'},
    '0224':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'弥勒佛','d':'弥勒佛配置','t':'未来视角','m':'传播弥勒','n2':'弥勒配置'},
    '1224':{'s':'★★☆☆☆','l':'基础职能层（三维）','n':'迷路弥勒','d':'有弥勒缘分未找到方向','t':'弥勒能量','m':'找到弥勒道路','n2':'需要方向'},
    '4314':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'效率强化系列','d':'注重效率','t':'效率优化','m':'提升效率','n2':''},
    '1314':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'金刚手版','d':'金刚手变体','t':'护法能量','m':'护法','n2':''},
    '0145':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'童子唐僧','d':'襁褓中的唐僧','t':'唐僧初始能量','m':'唐僧初始','n2':'唐僧版'},
    '1145':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'权威课题','d':'权威课题','t':'权威能量','m':'处理权威','n2':''},
    '0156':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'哪吒/石猴','d':'哪吒石猴配置','t':'反抗变革','m':'打破旧框架','n2':''},
    '2156':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'服务官版','d':'服务型低层级','t':'服务能力','m':'基础服务','n2':''},
    '-02167':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'服务强化版','d':'强化服务配置','t':'强化服务','m':'强化服务','n2':''},
    '0167':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'水财神','d':'水系统财神与肾膀胱相关','t':'水财富','m':'水系统修行','n2':'肾膀胱相关'},
    '1257':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'金刚手版','d':'金刚手变体','t':'金刚手能量','m':'护法','n2':''},
    '0257':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'童子土财神','d':'土系统童子和财神','t':'土财富','m':'土系统','n2':'土财神'},
    '09358':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'先天净化','d':'先天净化低配版','t':'初步净化','m':'基础净化','n2':''},
    '1358':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'金刚手版','d':'金刚手变体','t':'金刚手能量','m':'护法','n2':''},
    '9448':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'院长导航系列','d':'448最难事业心重','t':'事业导向','m':'平衡事业修行','n2':'最难度过'},
    '448':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'大器晚成','d':'需要时间沉淀','t':'长期积累','m':'长期修行','n2':'大器晚成'},
    '1189':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'权威课题','d':'权威课题','t':'权威能量','m':'处理权威','n2':''},
    '189':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'一清天使','d':'一清层次天使','t':'一清能量','m':'一清天使','n2':''},
    '3279':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'读心术版','d':'读心能力配置','t':'读心能力','m':'发展读心','n2':''},
    '0279':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'先天净化','d':'先天净化与肾气相关','t':'先天净化','m':'先天净化','n2':'与肾相关'},
    '9459':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'九天玄女院长','d':'九天玄女配置','t':'玄女能量','m':'玄女法门','n2':''},
    '8459':{'s':'★☆☆☆☆','l':'基础职能层（三维）','n':'思虑过重','d':'需要放松思维','t':'思维能力','m':'减少思虑','n2':'需放松'},
    '9325':{'s':'★☆☆☆☆','l':'特殊课题组','n':'9325系列','d':'需重点清理','t':'清理任务','m':'重点清理','n2':'需重点清理'},
    '1325':{'s':'★☆☆☆☆','l':'特殊课题组','n':'1325系列','d':'需重点清理','t':'需大量清理','m':'深度清理','n2':'需重点清理'},
    '1268':{'s':'★☆☆☆☆','l':'特殊课题组','n':'1268系列','d':'需重点清理','t':'需清理','m':'清理课题','n2':'需重点清理'},
    '0268':{'s':'★☆☆☆☆','l':'特殊课题组','n':'0268系列','d':'需重点清理','t':'需清理','m':'清理修行','n2':'需重点清理'},
    '0314':{'s':'★☆☆☆☆','l':'特殊课题组','n':'0314系列','d':'需重点清理与腰椎相关','t':'需清理','m':'清理+腰椎','n2':'需重点清理'},
}

def lookupSoul(grid):
    if grid in SOUL_DB: return SOUL_DB[grid]
    for k in SOUL_DB:
        if grid.startswith(k) or k.startswith(grid): return SOUL_DB[k]
    if len(grid) >= 4:
        p = grid[:4]
        for k in SOUL_DB:
            if k.startswith(p[:3]): return SOUL_DB[k]
    return None

def calc_soul_detail(yang, po, up):
    """计算灵魂详细信息 - 主魂/辅魂/魄详解/UP说明"""
    if not yang: return {}
    
    # 主魂 = 最后一位
    main_soul = yang[-1]
    
    # 辅魂 = 阳格去掉主魂后的前面部分
    aux_soul = yang[:-1] if len(yang) > 1 else ''
    
    # UP说明
    from collections import Counter
    cnt = Counter(po)
    up_detail = []
    for num, c in sorted(cnt.items()):
        if c >= 3:
            up_detail.append(f"{num}出现{c}次→升级为辅魂{num}")
    
    return {
        '主魂': main_soul,
        '辅魂': aux_soul,
        '辅魂说明': f"共{len(aux_soul)}位辅助能量" if aux_soul else "无辅魂",
        'UP': up,
        'UP说明': '; '.join(up_detail) if up_detail else "无魄升级为辅魂",
        '魄数': len(po),
        '魄列表': list(po)
    }

def ds(n): return sum(int(c) for c in str(n) if c.isdigit())
def rds(n):
    s = n
    while s >= 10: s = ds(s)
    return s

def getUpgraded(po):
    cnt = Counter(po)
    up = []
    for d, c in sorted(cnt.items()):
        if c >= 3: up.extend([d] * (c // 3))
    return up

def yangCalc(y, m, d):
    po = [int(c) for c in str(y)] + [int(c) for c in str(m).zfill(2)] + [int(c) for c in str(d).zfill(2)]
    tot = sum(po)
    up = getUpgraded(po)
    if tot < 10:
        main = tot
        base = [ds(y), ds(m), ds(d)]
        s = ''.join(str(x) for x in up + base + [main])
        cnt2 = Counter(s)
        new = [int(d) for d, c in cnt2.items() if c >= 3 and int(d) != main]
        parts = up + base + [main] + new
        return ''.join(str(p) for p in parts), po, up, 'B'
    main = rds(tot)
    ivs = []
    if tot >= 10: ivs.append(tot)
    s = tot
    while s >= 10:
        s = ds(s)
        if s >= 10: ivs.append(s)
    if tot == 10 and len(up) >= 2:
        ds_y = ds(y); ds_m = ds(m); ds_d = ds(d)
        day1 = int(str(d).zfill(2)[0])
        iv_f = int(str(ivs[0])[0]) if ivs else 0
        res = str(up[0]) + str(up[1]) + str(ds_y) + str(ds_m) + str(day1) + str(main) + str(up[0]) + str(iv_f) + str(ds_d)
        return res, po, up, 'MultiSoul'
    parts = up + ivs + [main]
    s = ''.join(str(x) for x in parts)
    cnt2 = Counter(s)
    new = [int(d) for d, c in cnt2.items() if c >= 3 and int(d) != main]
    parts.extend(new)
    return ''.join(str(p) for p in parts), po, up, 'A'

def yinCalc(y, m, d):
    if not HAS_LUNAR: return '0', []
    try:
        sol = Solar(y, m, d)
        lun = Converter().Solar2Lunar(sol)
        ly, lm, ld = lun.year, abs(lun.month), lun.day
        leap = lun.month < 0
        po = [int(c) for c in str(ly)] + [int(c) for c in str(lm).zfill(2)] + [int(c) for c in str(ld).zfill(2)]
        res, _, _, _ = yangCalc(ly, lm, ld)
        if leap: res = '1' + res
        return res, po
    except: return '0', []

def missingNum(g, po_set=None):
    if not g or g == '0': return '0123456789'
    p = set(int(c) for c in g if c.isdigit())
    if po_set: p |= po_set
    return ''.join(str(x) for x in sorted({0,1,2,3,4,5,6,7,8,9} - p))

HB_MAP = {'申时':'12','酉时':'12','寅时':'45','卯时':'45','亥时':'06','子时':'06','前子时':'06','后子时':'06','巳时':'3','午时':'3','辰时':'789','戌时':'789','丑时':'789','未时':'789'}

def halfSup(s):
    if not s or s in ['未知时辰','','unknown']: return None
    return HB_MAP.get(s)

def calc(date_str, shichen=None, gender=None, is_qianz=True):
    """
    计算九宫格
    
    参数:
        date_str: 日期字符串
        shichen: 时辰
        gender: 性别 'male' 或 'female'（必需）
        is_qianz: 是否前子时
    """
    try:
        dt = datetime.strptime(date_str.replace('/','-'), '%Y-%m-%d')
    except:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    y, m, d = dt.year, dt.month, dt.day
    is_zishi = shichen and '子时' in shichen
    is_qian = shichen and '前子时' in shichen
    res = {
        '日期':date_str,
        '时辰':shichen or '未知',
        '性别':gender or '未指定',
        '类型':'子时双格' if is_zishi else '普通阴阳双格'
    }

    def calcOne(yr, mo, da):
        yang, po, up, route = yangCalc(yr, mo, da)
        yin, yin_po = yinCalc(yr, mo, da)
        soul = lookupSoul(yang)
        return {
            '阳格':yang,
            '阴格':yin,
            '阳缺':missingNum(yang,set(po)),
            '阴缺':missingNum(yin,set(yin_po) if yin_po else None),
            '半补':halfSup(shichen),
            '灵魂':soul,
            '灵魂详情': calc_soul_detail(yang, po, up),
            '魄':po,
            'up':up,
            '路线':route,
            '阳格阴阳分析':analyze_grid_yin_yang(yang),
            '阴格阴阳分析':analyze_grid_yin_yang(yin)
        }

    if is_zishi:
        r1 = calcOne(y, m, d)
        if is_qian:
            adj = dt - timedelta(days=1)
            adj_str = '%d/%02d/%02d' % (adj.year, adj.month, adj.day)
        else:
            adj = dt + timedelta(days=1)
            adj_str = '%d/%02d/%02d' % (adj.year, adj.month, adj.day)
        r2 = calcOne(adj.year, adj.month, adj.day)
        res.update({
            '阳格':r1['阳格'],'阴格':r1['阴格'],'阳缺':r1['阳缺'],'阴缺':r1['阴缺'],
            '半补':r1['半补'],'灵魂':r1['灵魂'],
            '阳格1':r2['阳格'],'阴格1':r2['阴格'],'阳缺1':r2['阳缺'],'阴缺1':r2['阴缺'],
            '半补1':r2['半补'],'灵魂1':r2['灵魂'],
            '调整日期':adj_str,
            '说明':'前子时实际属于前一天(%s)'%adj_str if is_qian else '后子时属于后一天(%s)'%adj_str,
            '阳格阴阳分析':r1['阳格阴阳分析'],
            '阴格阴阳分析':r1['阴格阴阳分析']
        })
    else:
        r = calcOne(y, m, d)
        res.update(r)
    
    # 计算阴阳格周期
    if gender:
        res['生命周期'] = calc_life_cycle(y, gender)
    
    return res

def fmt(res):
    o = []
    o.append('='*60)
    o.append('日期: %s  时辰: %s  性别: %s  类型: %s' % (res['日期'],res['时辰'],res['性别'],res['类型']))
    o.append('-'*60)

    def pg(label, r, note=''):
        o.append('【%s】%s' % (label, note))
        o.append('  阳格: %s  阳缺: %s' % (r['阳格'], r['阳缺']))
        o.append('  阴格: %s  阴缺: %s' % (r['阴格'], r['阴缺']))
        o.append('  半补: %s' % (r['半补'] or 'null'))
        
        # 阴阳分析
        if '阳格阴阳分析' in r:
            yy = r['阳格阴阳分析']
            o.append('  阳格阴阳: 阴%d个(%s) 阳%d个(%s) → %s' % (
                yy['阴数'], ' '.join(yy['阴数字']), 
                yy['阳数'], ' '.join(yy['阳数字']),
                yy['阴阳倾向']
            ))
        
        if r.get('灵魂'):
            s = r['灵魂']
            o.append('  灵魂: %s %s' % (s['s'], s['n']))
            o.append('      %s' % s['l'])
            if s.get('d'): o.append('      %s' % s['d'][:40])
            if s.get('t'): o.append('  天赋: %s' % s['t'])
            if s.get('m'): o.append('  使命: %s' % s['m'])
            if s.get('n2') and s['n2']: o.append('  注意: %s' % s['n2'])

    if res['类型'] == '子时双格':
        r1 = dict((k, res[k]) for k in ['阳格','阴格','阳缺','阴缺','半补','灵魂','阳格阴阳分析','阴格阴阳分析'])
        r2 = dict((k.replace('1',''), res[k]) for k in ['阳格1','阴格1','阳缺1','阴缺1','半补1','灵魂1'])
        pg('当天格', r1)
        o.append('')
        pg('调整格', r2, '(%s)' % res.get('调整日期',''))
        o.append('')
        o.append('  说明: %s' % res.get('说明',''))
    else:
        pg('阴阳双格', res)
    
    o.append('')
    o.append('半补: 金12 木45 水06 火3 土789 | 申12酉12 寅45卯45 亥06子06 巳3午3 辰戌丑未789')
    
    # 生命周期
    if '生命周期' in res:
        lc = res['生命周期']
        o.append('')
        o.append('='*60)
        o.append('【阴阳格周期】%s' % lc['周期参数']['desc'])
        o.append('-'*60)
        o.append('  当前年龄: %d岁' % lc['年龄'])
        o.append('  当前阶段: %s (%.1f-%.1f岁)' % (lc['当前阶段'], lc['当前阶段开始'], lc['当前阶段结束']))
        o.append('  下次换魂: %s (%.1f岁，距今%.1f年)' % (lc['下次换魂'], lc['下次换魂年龄'], lc['距下次换魂']))
        if lc['当前类型'] == '换魂':
            o.append('  ⚠️ 当前处于换魂期！身体能量重组，需特别养护')
    
    o.append('='*60)
    return '\n'.join(o)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='慈海九宫格 v5.0（新增性别输入和阴阳格周期）')
    p.add_argument('date', help='日期 YYYY/MM/DD')
    p.add_argument('-s','--shichen', default=None, help='时辰')
    p.add_argument('-g','--gender', required=True, choices=['male','female','男','女'], help='性别（必需）：male/female 或 男/女')
    p.add_argument('--json', action='store_true', help='输出JSON格式')
    args = p.parse_args()
    
    # 处理性别输入
    gender = args.gender
    if gender in ['男', 'male']:
        gender = 'male'
    elif gender in ['女', 'female']:
        gender = 'female'
    
    r = calc(args.date, args.shichen, gender)
    if args.json:
        def conv(x):
            if isinstance(x, set): return sorted(x)
            if isinstance(x, dict): return dict((k,conv(v)) for k,v in x.items())
            return x
        print(jsonmod.dumps(conv(r), indent=2, ensure_ascii=False))
    else:
        print(fmt(r))
