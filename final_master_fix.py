#!/usr/bin/env python3
"""
final_master_fix.py - 最终修复方案：
1. 从 function 层提取短码条目移到 creation 层（origin 保持空）
2. 重新生成 409 张重复/缺失图片
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
PROGRESS_FILE = "final_master_fix_progress.json"

# ========== 风格提示词 ==========
STYLES = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry, ultra detailed digital art, masterpiece, 8k",
    "ancient mystical sage, golden halo, ornate robes, temple background, classical painting style, divine presence, highly detailed portrait",
    "cosmic entity, starfield background, quantum energy patterns, iridescent skin, visionary art, dramatic lighting, cinematic composition",
    "celestial entity, radiant light body, mandala aura, crystal throne, Buddhist thangka style, serene expression, best quality",
    "divine humanoid, bioluminescent skin, nebula background, holographic markings, sci-fi concept art, photorealistic, 8k resolution",
    "angelic entity, feathered wings, pearl white robes, sunbeam lighting, renaissance oil painting, divine grace, masterwork",
    "alien deity, purple mist background, telekinetic gaze, advanced tech armor, cyberpunk aesthetic, dramatic shadows, ultra detailed",
    "spirit guide, translucent ethereal form, rainbow auras, ancient forest, shamanic artwork, mystical energy flow, masterpiece",
]

NODE_STYLES = {
    0: "pure innocent child being, soft pastel glow, lotus petals background, divine purity",
    1: "grey alien entity, large dark almond eyes, slender frame, mysterious cosmic atmosphere, manuscript style",
    2: "sassani blue-green being, pointed ears, regal posture, ancient mesopotamian temple",
    3: "sirian entity, deep blue skin, ancient egyptian gold headdress, star syrius background",
    4: "orion warrior being, dark armor golden trim, fierce noble expression, nebula battlefield",
    5: "yahriel entity, iridescent rainbow skin, quantum shimmer energy, crystalline background",
    6: "pleiadian being, nordic golden features, crystal crown, emerald forest meadow",
    7: "annunaki being, golden skin, sumerian crown, winged disk, desert temple",
    8: "gaia earth mother, flowing green and brown robes, flower vine crown, lush garden",
    9: "arcturian entity, blue-violet geometric crystalline form, sacred geometry",
    10: "12D celestial elder, transcendent white-gold light body, intricate mandala, cosmic void",
    11: "creation guardian being, golden throne of stars, seraphic wings, divine judgment scene",
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


def download_image(code, fpath, style_idx):
    seed = (int(hashlib.md5(f"final_{code}_{style_idx}".encode()).hexdigest(), 16) +
            style_idx * 7919 + random.randint(1, 9999)) % 999999
    prompt = build_prompt(code, style_idx)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"

    for attempt in range(8):
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


def parse_layers():
    """解析 deities.js 的 LAYERS 数组为可编辑结构"""
    content = open(JS_FILE, 'r', encoding='utf-8').read()
    layers_start = content.find('LAYERS=')
    layers_bracket = content.find('[', layers_start)
    
    # Extract LAYERS content
    depth = 0
    layers_end = layers_bracket
    for i in range(layers_bracket, len(content)):
        if content[i] == '[': depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                layers_end = i + 1
                break
    
    layers_content = content[layers_bracket+1:layers_end-1]
    
    # Parse each layer object
    layers = []
    i = 0
    while i < len(layers_content):
        if layers_content[i:].startswith('{id:'):
            obj_start = i
            depth = 0
            for j in range(i, len(layers_content)):
                if layers_content[j] == '{': depth += 1
                elif layers_content[j] == '}':
                    depth -= 1
                    if depth == 0:
                        layers.append(layers_content[obj_start:j+1])
                        i = j + 1
                        break
            i += 1
        else:
            i += 1
    
    return layers, content[layers_start:layers_end]


def fix_layers():
    print("\n" + "=" * 60)
    print("STEP 1: 修复 deities.js 层级")
    print("=" * 60, flush=True)
    
    # Extract short codes from function layer
    function_start = JS_CONTENT.find('id:"function"')
    material_start = JS_CONTENT.find('id:"material"')
    function_section = JS_CONTENT[function_start:material_start]
    
    pattern = r'(\{code:"(\d{1,3})",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)",node:(\d+),races:\[(.*?)\]\})'
    matches = re.findall(pattern, function_section)
    
    origin_entries = []
    creation_entries = []
    
    for full_entry, code_str, name, role, image, node, races in matches:
        s = code_str.lstrip('0')
        if len(s) <= 2:
            origin_entries.append(full_entry)
        else:
            creation_entries.append(full_entry)
    
    # Build creation layer deities array
    if creation_entries:
        creation_deities = ',\n    '.join(creation_entries)
    else:
        creation_deities = ''
    
    new_creation = f'{{\nid:"creation",\n"title":"创世管理层 · 九至十一维",\n"color":"purple",\n"bg":"generated-images/Multi_dimensional_creation_mat_2026-07-08T09-33-15.png",\ndeities:[\n{creation_deities}\n]\n}}'
    
    # Rebuild function layer without short codes
    # Find and remove short code entries from function layer
    function_section_fixed = function_section
    for code_str, name, role, image, node, races in matches:
        entry_pattern = r'\{code:"' + re.escape(code_str) + r'",name:"[^"]+",role:"[^"]+",image:"[^"]+",node:\d+,races:\[.*?\]\}'
        function_section_fixed = re.sub(entry_pattern, '', function_section_fixed)
    
    # Reconstruct the function layer object
    function_layer_obj = re.search(r'(\{[^}]*id:"function"[^}]*deities:\[\[^\]]*\]\}\s*,\s*\{[^}]*id:"material"[^}]*(\}\s*)?)', JS_CONTENT[function_start:material_start+len('id:"material"')])
    
    print(f"Origin entries: {len(origin_entries)}", flush=True)
    print(f"Creation entries: {len(creation_entries)}", flush=True)
    print(f"Function section cleaned length: {len(function_section_fixed)}", flush=True)


# Actually, let me do a simpler approach - just write the corrected deities.js directly
def do_it_properly():
    """Direct manipulation approach"""
    content = open(JS_FILE, 'r', encoding='utf-8').read()
    
    # Extract all entries from function layer
    function_start = content.find('id:"function"')
    material_start = content.find('id:"material"')
    function_section = content[function_start:material_start]
    
    # Match ALL deity entries (not just short ones)
    all_entries = re.findall(r'\{code:"(\d+)",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)",node:(\d+),races:\[(.*?)\]\}', function_section)
    print(f"Total entries in function: {len(all_entries)}", flush=True)
    
    # Extract short code entries (1-3 digits)
    short_pattern = r'(\{code:"(\d{1,3})",name:"[^"]+",role:"[^"]+",image:"generated-images/(code_\d+\.jpg)",node:\d+,races:\[.*?\]\})'
    short_entries_matches = re.findall(short_pattern, function_section)
    print(f"Short entries to move: {len(short_entries_matches)}", flush=True)
    
    origin_entries_list = []
    creation_entries_list = []
    
    for full, code_str, img in short_entries_matches:
        s = code_str.lstrip('0')
        if len(s) <= 2:
            origin_entries_list.append(full)
        else:
            creation_entries_list.append(full)
    
    print(f"Origin: {len(origin_entries_list)}, Creation: {len(creation_entries_list)}", flush=True)
    
    # Reconstruct function layer content without short entries
    function_layer_start = content.find('id:"function"')
    material_layer_start = content.find('id:"material"')
    
    # Get the full function layer object
    function_layer_end = content.find('}},', function_layer_start)
    if function_layer_end == -1:
        function_layer_end = content.find('}', function_layer_start + 100)
    
    # Actually the structure is complex. Let me just replace the function layer's deities array
    # Find the function layer's opening
    func_obj_start = content.rfind('{', 0, function_layer_start)
    func_obj_end_marker = content.find('id:"material"', function_layer_start)
    function_full_obj = content[func_obj_start:func_obj_end_marker]
    
    # Extract remaining entries (longer codes)
    remaining_pattern = r'\{code:"(\d{4,})",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)",node:(\d+),races:\[(.*?)\]\}'
    remaining_matches = re.findall(remaining_pattern, function_section)
    print(f"Remaining function entries: {len(remaining_matches)}", flush=True)
    
    # Build new function layer
    if remaining_matches:
        new_function_deities = ',\n    '.join([m[0] for m in remaining_matches])
        function_deities_block = f'\n    {new_function_deities}\n  ]'
    else:
        function_deities_block = '[]'
    
    # Rebuild the function layer section
    # Find where function deities starts
    func_deities_start = function_full_obj.find('deities:[')
    func_deities_end_marker = function_full_obj.find(']},', func_deities_start)
    if func_deities_end_marker == -1:
        func_deities_end_marker = function_full_obj.find('}', func_deities_start + 10)
    
    print(f"Function layer structure OK: {func_deities_end_marker > func_deities_start}", flush=True)


# Actually, the simplest approach: write a Python script that does the fix correctly
import shutil
shutil.copy(JS_FILE, JS_FILE + ".original")

# Let me do the simplest possible fix
content = open(JS_FILE, 'r', encoding='utf-8').read()

# Extract short code entries
function_start = content.find('id:"function"')
material_start = content.find('id:"material"')
function_section = content[function_start:material_start]

pattern = r'\{code:"(\d+)",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)",node:(\d+),races:\[(.*?)\]\}'
all_entries = re.findall(pattern, function_section)

short_entries = []
for code, name, role, image, node, races in all_entries:
    if len(code.lstrip('0')) <= 3:
        # Reconstruct the full entry
        entry = '{code:"{}",name:"{}",role:"{}",image:"{}",node:{},races:[{}]}'.format(
            code, name, role, image, node, races.strip()
        )
        short_entries.append(entry)

origin_entries = [e for e in short_entries if len(e.split('"')[1].lstrip('0')) <= 2]
creation_entries = [e for e in short_entries if len(e.split('"')[1].lstrip('0')) > 2]

print(f"\nFinal counts:")
print(f"Short entries total: {len(short_entries)}")
print(f"Origin (1-2 digits): {len(origin_entries)}")
print(f"Creation (3 digits): {len(creation_entries)}")

# Now reconstruct the function layer
remaining_entries = []
for code, name, role, image, node, races in all_entries:
    if len(code.lstrip('0')) > 3:
        entry = '{code:"{}",name:"{}",role:"{}",image:"{}",node:{},races:[{}]}'.format(
            code, name, role, image, node, races.strip()
        )
        remaining_entries.append(entry)

print(f"Remaining in function: {len(remaining_entries)}")

# Replace function layer deities
func_obj_start = content.rfind('{', 0, function_start)
material_obj_start = content.find('{id:"material"', material_start)

old_function_section = content[func_obj_start:material_obj_start]

# Find deities:[ and its end
deities_open = old_function_section.find('deities:[')
# Find the closing ]},
deities_end = old_function_section.find(']},', deities_open)
if deities_end == -1:
    deities_end = old_function_section.find('}', deities_open + 10)

if deities_open >= 0 and deities_end >= 0:
    old_deities = old_function_section[deities_open+9:deities_end]
    new_deities = ''
    if remaining_entries:
        new_deities = '\n  ' + ',\n  '.join(remaining_entries)
    
    new_function_section = old_function_section[:deities_open+9] + new_deities + old_function_section[deities_end:]
    
    # Reconstruct the full content
    new_content = content[:func_obj_start] + new_function_section + content[material_obj_start:]
    
    # Write back
    with open(JS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\n✓ Function layer updated: removed {len(short_entries)} entries, {len(remaining_entries)} remain")
    
    # Now update origin and creation layers
    # Find origin layer
    origin_idx = new_content.find('id:"origin"')
    creation_idx = new_content.find('id:"creation"')
    
    origin_obj_start = new_content.rfind('{', 0, origin_idx)
    origin_section = new_content[origin_obj_start:creation_idx]
    
    if creation_entries:
        new_creation_deities = '\n  ' + ',\n  '.join(creation_entries)
    else:
        new_creation_deities = ''
    
    creation_deities_open = origin_section.find('id:"creation"', origin_idx)
    creation_actual_start = new_content.find('id:"creation"')
    creation_obj_start = new_content.rfind('{', 0, creation_actual_start)
    creation_obj_end = new_content.find('id:"innate"', creation_actual_start)
    creation_section = new_content[creation_obj_start:creation_obj_end]
    
    creation_deities_pos = creation_section.find('deities:[')
    creation_deities_end = creation_section.find(']},', creation_deities_pos)
    if creation_deities_pos >= 0 and creation_deities_end >= 0:
        new_content = (new_content[:creation_obj_start] + creation_section[:creation_deities_pos+9] + 
                      new_creation_deities + creation_section[creation_deities_end:] + 
                      new_content[creation_obj_end:])
        
        with open(JS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Creation layer updated with {len(creation_entries)} entries")
    
    # Verify
    verify_content = open(JS_FILE, 'r', encoding='utf-8').read()
    for layer in ['origin', 'creation', 'innate', 'elite', 'function']:
        idx = verify_content.find(f'id:"{layer}"')
        section = verify_content[idx:idx+500]
        code_count = section.count('code:')
        print(f"{layer}: {code_count} deities")
else:
    print("Failed to find deities array in function layer")
