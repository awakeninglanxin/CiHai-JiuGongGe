# -*- coding: utf-8 -*-
"""查看 grid_frequency_data.json 的汇总统计"""
import json, os, sys

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'grid_frequency_data.json')

if not os.path.exists(DATA_FILE):
    print(f"数据文件尚未生成: {DATA_FILE}")
    print("请等待 batch_grid_count.py 运行完成")
    sys.exit(1)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n日期范围: {data['date_range']}")
print(f"总天数: {data['total_days']}")
print(f"阳格种类: {data['yang_total_types']}  阴格种类: {data['yin_total_types']}")
print(f"阳格失败: {data['yang_fail']}  阴格失败: {data['yin_fail']}")

# 阳格 TOP 50
yang = sorted(data['yang_counter'].items(), key=lambda x: -x[1])
print(f"\n{'='*50}")
print("阳格 TOP 50:")
for i, (code, cnt) in enumerate(yang[:50]):
    print(f"  {i+1:3d}. {code}: {cnt:5d}次")

# 阴格 TOP 50
yin = sorted(data['yin_counter'].items(), key=lambda x: -x[1])
print(f"\n{'='*50}")
print("阴格 TOP 50:")
for i, (code, cnt) in enumerate(yin[:50]):
    print(f"  {i+1:3d}. {code}: {cnt:5d}次")

# 合并去重
all_codes = set(data['yang_counter'].keys()) | set(data['yin_counter'].keys())
yang_only = set(data['yang_counter'].keys()) - set(data['yin_counter'].keys())
yin_only  = set(data['yin_counter'].keys()) - set(data['yang_counter'].keys())
both = set(data['yang_counter'].keys()) & set(data['yin_counter'].keys())

print(f"\n{'='*50}")
print(f"合并去重大神种类: {len(all_codes)}")
print(f"  仅在阳格: {len(yang_only)} 种")
print(f"  仅在阴格: {len(yin_only)} 种")
print(f"  阴阳共有: {len(both)} 种")

# 匹配 deities.js 中的 51 大神
# 在阴阳格中出现的已知大神
known_codes = [
    '033393','0123','303','213',
    '1325101','946101','939123','39123',
    '28101','37101','737101','19101','46101','336','426','1426','369','9369','1303','29112',
    '437','123','112','257','167','38112',
    '0202','9347','9459','0156','0145','156','246','02226','189','279','0279','134','404',
    '358','325','1291121','347','7437','1268','268','314','224','415','235','145'
]
print(f"\n已知51大神在格中出现情况:")
yang_hits = [c for c in known_codes if c in data['yang_counter']]
yin_hits  = [c for c in known_codes if c in data['yin_counter']]
print(f"  阳格命中: {len(yang_hits)}/51")
print(f"  阴格命中: {len(yin_hits)}/51")
if len(yang_hits) < 51:
    missing_yang = [c for c in known_codes if c not in data['yang_counter']]
    print(f"  阳格未命中: {missing_yang}")
if len(yin_hits) < 51:
    missing_yin = [c for c in known_codes if c not in data['yin_counter']]
    print(f"  阴格未命中: {missing_yin}")
