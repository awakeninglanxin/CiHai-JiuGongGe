#!/usr/bin/env python3
"""
complete_fix.py - 正确修复 deities.js 层级 + 重新生成图片
"""

import re
import shutil
import hashlib
import os
import time
import random
import json
import urllib.request
import urllib.parse

sys = __import__('sys')
sys.stdout.reconfigure(line_buffering=True)

JS_FILE = "deities.js"
IMG_DIR = "generated-images"

# ========== 风格 ==========
STYLES = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry",
    "ancient mystical sage, golden halo, ornate robes, temple background, classical painting",
    "cosmic entity, starfield background, quantum energy patterns, iridescent skin, visionary",
    "celestial entity, radiant light body, mandala aura, crystal throne, Buddhist art",
    "divine humanoid, bioluminescent skin, nebula background, holographic markings, sci-fi",
    "angelic entity, feathered wings, pearl white robes, sunbeam lighting, renaissance",
    "alien deity, purple mist background, telekinetic gaze, advanced tech armor, cyberpunk",
    "spirit guide, translucent ethereal form, rainbow auras, ancient forest, shamanic",
]

NODE_STYLES = {
    0: "innocent divine child, pure white light, pastel aura, lotus background",
    1: "grey alien entity, large dark almond eyes, slender frame, cosmic atmosphere",
    2: "sassani blue-green being, pointed ears, regal posture, ancient temple",
    3: "sirian entity, deep blue skin, ancient egyptian gold headdress, star syrius",
    4: "orion warrior being, dark armor golden trim, fierce expression, nebula battlefield",
    5: "yahriel entity, iridescent rainbow skin, quantum shimmer, crystalline background",
    6: "pleiadian being, nordic golden features, crystal crown, emerald forest",
    7: "annunaki being, golden skin, sumerian crown, winged disk, desert temple",
    8: "gaia earth mother, flowing green robes, flower vine crown, lush garden",
    9: "arcturian entity, blue-violet geometric crystalline form, sacred geometry",
    10: "12D celestial elder, transcendent white-gold light body, mandala, cosmic void",
    11: "creation guardian, golden throne of stars, seraphic wings, divine scene",
    12: "innate divine child, pure lotus light, rainbow chakra, buddhist thangka",
    13: "cosmic function entity, living sacred geometry, fractal light patterns",
}

QUALITY = ", ultra detailed, 8k, masterpiece, best quality, highly detailed face, cinematic lighting"


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
    return f"{base}, {style}{QUALITY}"


def download_image(code, fpath, style_idx):
    seed = (int(hashlib.md5(f"fix_{code}_{style_idx}".encode()).hexdigest(), 16) +
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


# ========== STEP 1: 修复 deities.js ==========
print("=" * 60, flush=True)
print("STEP 1: 修复 deities.js 层级", flush=True)
print("=" * 60, flush=True)

shutil.copy(JS_FILE, JS_FILE + ".bak_complete")
content = open(JS_FILE, 'r', encoding='utf-8').read()

# Extract all function layer entries
function_start = content.find('id:"function"')
material_start = content.find('id:"material"')
function_section = content[function_start:material_start]

all_entries = re.findall(
    r'(\{code:"[^"]+",name:"[^"]+",role:"[^"]+",image:"generated-images/[^"]+",node:\d+,races:\[.*?\]\})',
    function_section
)

short_entries = []
long_entries = []

for entry in all_entries:
    code_match = re.search(r'code:"(\d+)"', entry)
    if code_match:
        code = code_match.group(1).lstrip('0') or '0'
        if len(code) <= 3:
            short_entries.append(entry)
        else:
            long_entries.append(entry)

print(f"  Short entries (to creation): {len(short_entries)}", flush=True)
print(f"  Long entries (stay in function): {len(long_entries)}", flush=True)

# ===== Fix creation layer =====
creation_start = content.find('id:"creation"')
innate_start = content.find('id:"innate"')
creation_section = content[creation_start:innate_start]

creation_deities_open = creation_section.find('deities:[')
# Find the closing ] that matches deities:[
depth = 0
creation_deities_close = -1
for j in range(creation_deities_open + 9, len(creation_section)):
    if creation_section[j] == '[': depth += 1
    elif creation_section[j] == ']':
        if depth == 0:
            creation_deities_close = j
            break
    elif depth > 0:
        depth -= 1

if creation_deities_open >= 0 and creation_deities_close >= 0:
    before = creation_section[:creation_deities_open + 9]
    after = creation_section[creation_deities_close:]  # includes ]},\n  {

    if short_entries:
        new_deities = '\n  ' + ',\n  '.join(short_entries) + '\n  '
    else:
        new_deities = ''

    new_creation = before + new_deities + after
    content = content[:creation_start] + new_creation + content[innate_start:]
    print(f"  ✓ creation 层已更新", flush=True)
else:
    print("  ✗ 无法解析 creation 层 deities 数组", flush=True)

# ===== Fix function layer =====
function_section_new = content[function_start:material_start]
function_deities_open = function_section_new.find('deities:[')
function_deities_close = -1
depth = 0
for j in range(function_deities_open + 9, len(function_section_new)):
    if function_section_new[j] == '[': depth += 1
    elif function_section_new[j] == ']':
        if depth == 0:
            function_deities_close = j
            break
    elif depth > 0:
        depth -= 1

if function_deities_open >= 0 and function_deities_close >= 0:
    before = function_section_new[:function_deities_open + 9]
    after = function_section_new[function_deities_close:]

    if long_entries:
        new_deities = '\n  ' + ',\n  '.join(long_entries) + '\n  '
    else:
        new_deities = ''

    new_function = before + new_deities + after
    content = content[:function_start] + new_function + content[material_start:]
    print(f"  ✓ function 层已更新", flush=True)

with open(JS_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
verify = open(JS_FILE, 'r', encoding='utf-8').read()
for layer in ['origin', 'creation', 'innate', 'elite', 'function', 'material']:
    idx = verify.find(f'id:"{layer}"')
    if idx >= 0:
        obj_start = verify.rfind('{', 0, idx)
        depth = 0
        obj_end = obj_start
        for j in range(obj_start, min(obj_start + 50000, len(verify))):
            if verify[j] == '{': depth += 1
            elif verify[j] == '}':
                depth -= 1
                if depth == 0:
                    obj_end = j + 1
                    break
        layer_obj = verify[obj_start:obj_end]
        code_count = len(re.findall(r'\{code:', layer_obj))
        print(f"  {layer}: {code_count} deities", flush=True)


# ========== STEP 2: 重新生成重复/缺失图片 ==========
print("\n" + "=" * 60, flush=True)
print("STEP 2: 重新生成 409 张图片", flush=True)
print("=" * 60, flush=True)

PROGRESS_FILE = "final_master_fix_progress.json"
if os.path.exists(PROGRESS_FILE):
    prog = json.load(open(PROGRESS_FILE))
else:
    prog = {'done': [], 'failed': []}

# Find all duplicate and missing codes
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

dup_codes = set()
for md5, codes in h2f.items():
    if len(codes) > 1:
        dup_codes.update(codes)

# Missing
all_code_entries = re.findall(r'code:"(\d+)",image:"generated-images/(code_\d+\.jpg)"', content)
missing_codes = set()
for code, image in all_code_entries:
    fpath = os.path.join(IMG_DIR, image.replace('generated-images/', ''))
    if not os.path.exists(fpath):
        missing_codes.add(code)

all_to_regen = sorted(dup_codes | missing_codes)
print(f"  Duplicate: {len(dup_codes)}, Missing: {len(missing_codes)}, Total: {len(all_to_regen)}", flush=True)

pending = [c for c in all_to_regen if c not in prog['done'] and c not in prog['failed']]
print(f"  Pending: {len(pending)}", flush=True)

if pending:
    ok = 0
    fail = 0
    for i, code in enumerate(pending):
        style_idx = (i + abs(hash(code)) % 100) % len(STYLES)
        fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")

        if i % 20 == 0:
            print(f"  [{i+1}/{len(pending)}] code_{code} style={style_idx}...", flush=True)

        if download_image(code, fpath, style_idx):
            prog['done'].append(code)
            ok += 1
            if i % 50 == 0:
                print(f"    ✓ OK ({ok})", flush=True)
        else:
            prog['failed'].append(code)
            fail += 1
            if i % 50 == 0:
                print(f"    ✗ FAIL ({fail})", flush=True)

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)

        time.sleep(random.uniform(2, 4))

    print(f"\n  REGEX DONE: OK={ok} FAIL={fail}", flush=True)
    print(f"  Total: done={len(prog['done'])} failed={len(prog['fail'])}", flush=True)
else:
    print("  All done!", flush=True)

print("\n" + "=" * 60, flush=True)
print("COMPLETE!", flush=True)
print("=" * 60, flush=True)
