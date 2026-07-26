#!/usr/bin/env python3
"""
fix_layers_and_regenerate.py - 一次性修复：
1. 将function层中的短码(<=3位)分类到origin和creation层
2. 重新生成405张重复图片
"""

import hashlib
import os
import re
import sys
import time
import random
import json
import urllib.request
import urllib.parse

sys.stdout.reconfigure(line_buffering=True)

JS_FILE = "deities.js"
IMG_DIR = "generated-images"
PROGRESS_FILE = "fix_progress.json"

# 风格提示词库（多样化，避免再次重复）
STYLES = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry, ultra detailed digital art, masterpiece, 8k",
    "ancient mystical being, golden halo, ornate robes, temple background, classical painting style, divine presence, highly detailed portrait",
    "cosmic entity, starfield background, quantum energy patterns, iridescent skin, visionary art, dramatic lighting, cinematic composition",
    "celestial entity, radiant light body, mandala aura, crystal throne, Buddhist thangka style, serene expression, best quality",
    "divine humanoid, bioluminescent skin, nebula background, holographic markings, sci-fi concept art, photorealistic, 8k resolution",
    "angelic being, feathered wings, pearl white robes, sunbeam lighting, renaissance painting style, divine grace, masterwork",
    "alien deity, purple mist background, telekinetic gaze, advanced tech armor, cyberpunk aesthetic, dramatic shadows, ultra detailed",
    "spirit guide, translucent ethereal form, rainbow auras, ancient forest, shamanic artwork, mystical energy flow, masterpiece",
]

NODE_STYLES = {
    0: "innocent divine child, pure white light, pastel aura, lotus background, sacred innocence",
    1: "grey alien federation, large dark almond eyes, slender frame, mysterious cosmic atmosphere, manuscript style",
    2: "sassani hybrid, blue-green skin, pointed ears, regal posture, ancient mesopotamian background",
    3: "sirian being, deep blue skin, ancient egyptian gold headdress, star syrius background",
    4: "orion warrior, dark armor golden trim, fierce noble expression, nebula battlefield",
    5: "yahriel being, iridescent rainbow skin, quantum shimmer energy, crystalline background",
    6: "pleiadian being, nordic golden features, crystal crown, emerald forest, fairy tale",
    7: "annunaki being, golden skin, sumerian crown, winged disk, desert temple",
    8: "gaia earth mother, flowing green and brown robes, flower vine crown, lush garden",
    9: "arcturian entity, blue-violet geometric crystalline form, sacred geometry",
    10: "12D celestial elder, transcendent white-gold light body, intricate mandala, cosmic void",
    11: "creation guardian, golden throne of stars, seraphic wings, divine judgment scene",
    12: "innate divine child, pure lotus light, rainbow chakra aura, buddhist thangka style",
    13: "cosmic function entity, living sacred geometry, fractal light patterns",
}

QUALITY = ", ultra detailed, 8k, masterpiece, best quality, highly detailed face, symmetrical features, cinematic lighting"


def get_node(code):
    s = code.lstrip('0')
    if s:
        d = int(s[-1])
        return d if d <= 13 else 0
    return 0


def build_prompt(code, style_idx):
    node = get_node(code)
    base = NODE_STYLES.get(node, NODE_STYLES[0])
    style = STYLES[style_idx % len(STYLES)]
    return f"{base}, {style}{QUALITY}, entity signature {code}"


def download_image(prompt, seed, fpath):
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'image/*'
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            if len(data) > 5000:
                with open(fpath, 'wb') as f:
                    f.write(data)
                return True
        except Exception:
            time.sleep(random.uniform(3, 8))
    return False


def find_duplicate_codes():
    """通过MD5找到需要重新生成的code"""
    h2f = {}
    for fname in os.listdir(IMG_DIR):
        if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        if '_v1restored' in fname or 'restored' in fname:
            continue
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            m = re.match(r'code_(.+)\.(jpg|jpeg|png)', fname)
            if m:
                h2f.setdefault(md5, []).append(m.group(1))
    
    dup_codes = []
    for md5, codes in h2f.items():
        if len(codes) > 1:
            dup_codes.extend(codes)
    
    return list(set(dup_codes))


def fix_layers_file(dup_codes):
    """
    修复deities.js两层：
    1. 从function层移动短码到origin/creation层
    2. 更新重复图片的提示词（在prompt中加入unique seed标识）
    """
    print("\n=== 步骤1: 修复deities.js层级 ===", flush=True)
    
    content = open(JS_FILE, 'r', encoding='utf-8').read()
    
    # 找到function层中所有短码（<=3位有效数字）
    function_pos = content.find('id:"function"')
    elite_pos = content.find('id:"elite"', function_pos)
    material_pos = content.find('id:"material"')
    
    origin_section = content[1718:function_pos]  # origin层
    creation_section = content[function_pos:material_pos]  # 暂时只到material
    
    # 实际上我们要从function层提取短码
    # function层内容
    function_start = content.find('id:"function"')
    function_end = content.find('id:"material"')
    function_full = content[function_start:function_end]
    
    # 提取所有短码条目（code长度<=3有效位）
    pattern = r'\{code:"(\d{1,3})",name:"(\d+)",role:"([^"]+)",image:"generated-images/(code_\d+.jpg)",node:(\d+),races:\[(.*?)\]\}'
    short_entries = re.findall(pattern, function_full)
    
    origin_destinations = []  # 1-2位 → origin层（12D+）
    creation_destinations = []  # 3位 → creation层（9-11D）
    
    for code_str, name, role, image, node, races in short_entries:
        s = code_str.lstrip('0')
        if len(s) <= 2:
            origin_destinations.append((code_str, name, role, image, int(node), races))
        else:
            creation_destinations.append((code_str, name, role, image, int(node), races))
    
    print(f"  Origin层候选: {len(origin_destinations)}", flush=True)
    print(f"  Creation层候选: {len(creation_destinations)}", flush=True)
    
    # 构建要移动的新deities条目
    origin_items = []
    for code_str, name, role, image, node, races in origin_destinations:
        entry = '{{code:"{code_str}",name:"{name}",role:"{role}",image:"generated-images/{image}",node:{node},races:[{races.strip()}]}}'.format(
            code_str=code_str, name=name, role=role, image=image, node=node, races=races.strip()
        )
        origin_items.append(entry)
    
    creation_items = []
    for code_str, name, role, image, node, races in creation_destinations:
        entry = '{{code:"{code_str}",name:"{name}",role:"{role}",image:"generated-images/{image}",node:{node},races:[{races.strip()}]}}'.format(
            code_str=code_str, name=name, role=role, image=image, node=node, races=races.strip()
        )
        creation_items.append(entry)
    
    # 构建新的origin和creation层内容
    new_origin = '''  {{id:"origin",title:"本源层 · 十二维+",color:"gold",bg:"generated-images/Epic_cosmic_scene__the_primord_2026-07-08T09-32-45.png",deities:[
{deities}
  ]}}'''.format(deities=',\n'.join(origin_items))
  
    new_creation = '''  {{id:"creation",title:"创世管理层 · 九至十一维",color:"purple",bg:"generated-images/Multi_dimensional_creation_mat_2026-07-08T09-33-15.png",deities:[
{deities}
  ]}}'''.format(deities=',\n'.join(creation_items))
    
    # 替换origin层
    origin_old_start = content.find('{id:"origin"')
    origin_old_end = content.find('id:"creation"')
    content = content[:origin_old_start] + new_origin + '\n  ' + content[origin_old_end:]
    
    # 替换creation层
    creation_old_start = content.find('{id:"creation"')
    creation_old_end = content.find('id:"innate"')
    content = content[:creation_old_start] + new_creation + '\n  ' + content[creation_old_end:]
    
    # 保存
    with open(JS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ deities.js已更新", flush=True)
    return origin_items, creation_items


def main():
    print("="*60, flush=True)
    print("STEP 1: 修复 deities.js 层级分类", flush=True)
    print("="*60, flush=True)
    fix_layers()
    
    print("\n" + "="*60, flush=True)
    print("STEP 2: 检测并重新生成重复图片", flush=True)
    print("="*60, flush=True)
    step2_regenerate()


def fix_layers():
    """
    修复 deities.js: 将 function 层中的短码分类到 origin/creation 层
    """
    content = open(JS_FILE, 'r', encoding='utf-8').read()
    
    # 找出 function 层的所有 deity 条目
    function_start = content.find('id:"function"')
    material_start = content.find('id:"material"')
    function_section = content[function_start:material_start]
    
    # 匹配短码条目 (1-3位有效数字)
    pattern = r'\{code:"(\d{1,3})",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+.jpg)",node:(\d+),races:\[(.*?)\]\}'
    matches = re.findall(pattern, function_section)
    
    origin_entries = []
    creation_entries = []
    
    for code_str, name, role, image, node, races in matches:
        s = code_str.lstrip('0')
        entry_text = '{{code:"{c}",name:"{n}",role:"{r}",image:"{i}",node:{nd},races:[{race}]}}'.format(
            c=code_str, n=name, r=role, i=image, nd=node, race=races.strip()
        )
        if len(s) <= 2:
            origin_entries.append(entry_text)
        else:
            creation_entries.append(entry_text)
    
    # 构建新 origin 层
    new_origin = '''  {{
    id:"origin",
    title:"本源层 · 十二维+",
    color:"gold",
    bg:"generated-images/Epic_cosmic_scene__the_primord_2026-07-08T09-32-45.png",
    deities:[
{items}
    ]
  }}'''.format(items=','.join(origin_entries))
    
    # 构建新 creation 层
    new_creation = '''  {{
    id:"creation",
    title:"创世管理层 · 九至十一维",
    color:"purple",
    bg:"generated-images/Multi_dimensional_creation_mat_2026-07-08T09-33-15.png",
    deities:[
{items}
    ]
  }}'''.format(items=','.join(creation_entries))
    
    # 替换 origin 层（从 {id:"origin" 到下一个 {{id:）
    origin_replacement = new_origin + ','
    creation_replacement = new_creation + ','
    
    # 找到 origin 层的完整对象边界
    origin_start = content.find('{{\n  id:"origin"')
    if origin_start == -1:
        origin_start = content.find('{id:"origin"')
    
    # 查找 origin 层的 closing brace
    # 简单方法：找到 origin 部分直到 creation 部分
    origin_idx = content.find('id:"origin"')
    creation_idx = content.find('id:"creation"')
    
    content = content[:origin_idx] + origin_replacement + '\n  ' + content[creation_idx:]
    
    creation_idx2 = content.find('id:"creation"')
    innate_idx = content.find('id:"innate"')
    content = content[:creation_idx2] + creation_replacement + '\n  ' + content[innate_idx:]
    
    with open(JS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ origin 层添加 {len(origin_entries)} 个神", flush=True)
    print(f"  ✓ creation 层添加 {len(creation_entries)} 个神", flush=True)
    print(f"  ✓ deities.js 已保存", flush=True)


if __name__ == "__main__":
    main()
