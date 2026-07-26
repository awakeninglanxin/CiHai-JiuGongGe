# -*- coding: utf-8 -*-
"""
批量替换节点图 → AI定制图
用法: python 替换节点图.py [批次大小默认5]
     每次运行生成5张图+自动映射，可反复运行直到全部替换完。
"""
import re, os, json, sys, time

BASE = os.path.dirname(os.path.dirname(__file__))  # 慈海九宫格_整合版/
DEITIES = os.path.join(BASE, 'deities.js')
GRID = os.path.join(BASE, 'grid_frequency_data.json')

def get_priority_list():
    """返回需替换代码列表(按频率降序)"""
    with open(DEITIES, 'r', encoding='utf-8') as f: js = f.read()
    with open(GRID, 'r', encoding='utf-8') as f: grid = json.load(f)
    
    node_kw = ['Grey_alien','Essassani_hybrid','Sirius_star','Orion_constellation',
        'Yahyel_civilization','Pleiades_network','Annunaki_civilization','Gaia_the_living',
        'Arcturus_civilization','Acquired_Child_celestial','Four_Pure_Jade','Sanqing_Dean',
        'Duodecimal_Code','Innate_Child_star']
    
    entries = re.findall(r'\{code:\"(\d+)\",name:\"([^\"]*)\",role:\"([^\"]*)\",image:\"([^\"]+)\",node:(\d+)', js)
    
    priority = []
    for code, name, role, img, node in entries:
        is_node = any(k in img for k in node_kw)
        if is_node:
            freq = grid['yang_counter'].get(code,0) + grid['yin_counter'].get(code,0)
            priority.append((code, name, freq, int(node)))
    
    priority.sort(key=lambda x: -x[2])
    return priority

def auto_map():
    """扫描generated-images中新图，按文件名代码号匹配到deities.js"""
    img_dir = os.path.join(BASE, 'generated-images')
    with open(DEITIES, 'r', encoding='utf-8') as f: js = f.read()
    
    placeholders = re.findall(r'_new_(\d+)\.png', js)
    all_imgs = [f for f in os.listdir(img_dir) if f.endswith('.png') and '_new_' not in f]
    all_imgs.sort(key=lambda x: os.path.getmtime(os.path.join(img_dir, x)), reverse=True)
    
    updated = 0
    for img in all_imgs[:20]:  # 只检查最新20张
        code_nums = re.findall(r'(\d{3,8})', img)
        for code in code_nums:
            if code in placeholders:
                old = f'generated-images/_new_{code}.png'
                new = f'generated-images/{img}'
                if old in js:
                    js = js.replace(old, new)
                    updated += 1
                    placeholders.remove(code)
                    break
    
    with open(DEITIES, 'w', encoding='utf-8') as f:
        f.write(js)
    
    return updated, len(placeholders)

if __name__ == '__main__':
    priority = get_priority_list()
    remaining = len(priority)
    print(f'总待替换: {remaining} 张节点图')
    print(f'TOP 10:')
    for code, name, freq, node in priority[:10]:
        print(f'  {code} ({name}): {freq}次 N{node}')
    
    # 检查是否有新图需要映射
    u, r = auto_map()
    if u > 0:
        print(f'\n自动映射: {u} 张新图 → 剩余节点图: {r}')
    
    print(f'\n准备生成批次。请使用 WorkBuddy ImageGen 工具逐批生成。')
    print(f'建议每次生成 5 张，限流时等待 60s。')
