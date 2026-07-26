#!/usr/bin/env python3
"""
master_fix.py - 一站式修复：
1. 从function层移动27个短码到origin/creation层
2. 重新生成409张重复/缺失图片
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
PROGRESS_FILE = "master_fix_progress.json"

# 8种多样化风格提示词
STYLES = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry, ultra detailed digital art, masterpiece, 8k",
    "ancient mystical sage, golden halo, ornate robes, temple background, classical painting style, divine presence, highly detailed portrait",
    "cosmic entity, starfield background, quantum energy patterns, iridescent skin, visionary art, dramatic lighting, cinematic composition",
    "celestial being, radiant light body, mandala aura, crystal throne, Buddhist thangka style, serene expression, best quality",
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

QUALITY_BOOST = ", ultra detailed, 8k, masterpiece, best quality, highly detailed face, symmetrical features, cinematic lighting"


def get_node(code):
    s = code.lstrip('0')
    if s:
        d = int(s[-1])
        return d if d <= 13 else 0
    return 0


def build_prompt(code, style_idx):
    node = get_node(code)
    base_style = NODE_STYLES.get(node, NODE_STYLES[0])
    style = STYLES[style_idx % len(STYLES)]
    return f"{base_style}, {style}{QUALITY_BOOST}, entity signature {code}"


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


# ========================
# STEP 1: 修复 deities.js 层级
# ========================
def fix_layers():
    print("\n" + "=" * 60)
    print("STEP 1: 修复 deities.js 层级分类")
    print("=" * 60, flush=True)

    # 备份
    import shutil
    shutil.copy(JS_FILE, JS_FILE + ".bak_step1")

    content = open(JS_FILE, 'r', encoding='utf-8').read()

    # 从function层提取27个短码条目
    function_start = content.find('id:"function"')
    material_start = content.find('id:"material"')
    function_section = content[function_start:material_start]

    # 匹配所有短码 (1-3位)
    pattern = r'(\{code:"(\d{1,3})",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)",node:(\d+),races:\[(.*?)\]\})'
    matches = re.findall(pattern, function_section)

    origin_items = []
    creation_items = []
    remain_in_function = []

    for full_entry, code_str, name, role, image, node, races in matches:
        s = code_str.lstrip('0')
        if len(s) <= 2:
            origin_items.append(full_entry)
        elif len(s) == 3:
            creation_items.append(full_entry)
        else:
            remain_in_function.append(full_entry)

    # 构建新origin层
    if origin_items:
        new_origin_deities = ',\n    '.join(origin_items)
        new_origin_block = f'    deities:[\n    {new_origin_deities}\n    ]'
    else:
        new_origin_block = '    deities:[]'

    # 构建新creation层
    if creation_items:
        new_creation_deities = ',\n    '.join(creation_items)
        new_creation_block = f'    deities:[\n    {new_creation_deities}\n    ]'
    else:
        new_creation_block = '    deities:[]'

    # 替换 origin 层的 deities 数组
    origin_idx = content.find('id:"origin"')
    origin_start = content.find('{', origin_idx)
    # 找到 origin 层的 deities:[ 和 closing ],
    deities_open = content.find('deities:[', origin_start)
    deities_close = content.find(']},', origin_start)
    if deities_close == -1:
        deities_close = content.find('}', origin_start + 1)

    content = content[:deities_open + 9] + '\n    ' + new_origin_block.strip() + content[deities_close:]

    # 替换 creation 层的 deities 数组
    creation_idx = content.find('id:"creation"')
    creation_start = content.find('{', creation_idx)
    deities_open2 = content.find('deities:[', creation_start)
    deities_close2 = content.find(']},', creation_start)
    if deities_close2 == -1:
        deities_close2 = content.find('}', creation_start + 1)

    content = content[:deities_open2 + 9] + '\n    ' + new_creation_block.strip() + content[deities_close2:]

    with open(JS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ origin 层添加 {len(origin_items)} 个神", flush=True)
    print(f"  ✓ creation 层添加 {len(creation_items)} 个神", flush=True)


# ========================
# STEP 2: 检测并列出所有需要重新生成的图片
# ========================
def find_codes_needing_regen():
    """MD5检测 + 缺失检测"""
    print("\n" + "=" * 60)
    print("STEP 2: 检测需要重新生成的图片")
    print("=" * 60, flush=True)

    # MD5 重复
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

    # 缺失图片
    missing_codes = set()
    content = open(JS_FILE, 'r', encoding='utf-8').read()
    all_entries = re.findall(r'code:"(\d+)",name:"([^"]+)",role:"([^"]+)",image:"generated-images/(code_\d+\.jpg)"', content)
    for code, name, role, image in all_entries:
        fpath = os.path.join(IMG_DIR, image.replace('generated-images/', ''))
        if not os.path.exists(fpath):
            missing_codes.add(code)

    # 合并
    all_to_regen = sorted(dup_codes | missing_codes)
    print(f"  重复MD5: {len(dup_codes)}", flush=True)
    print(f"  缺失图片: {len(missing_codes)}", flush=True)
    print(f"  合计需要重新生成: {len(all_to_regen)}", flush=True)

    return all_to_regen


# ========================
# STEP 3: 批量重新生成
# ========================
def regenerate_images(codes_to_regen):
    print("\n" + "=" * 60)
    print("STEP 3: 批量重新生成图片")
    print("=" * 60, flush=True)

    if os.path.exists(PROGRESS_FILE):
        prog = json.load(open(PROGRESS_FILE))
    else:
        prog = {'done': [], 'failed': []}

    pending = [c for c in codes_to_regen if c not in prog['done'] and c not in prog['failed']]
    print(f"待处理: {len(pending)} (已完成{len(prog['done'])}, 失败{len(prog['failed'])})", flush=True)

    if not pending:
        print("全部完成!", flush=True)
        return

    ok = 0
    fail = 0

    for i, code in enumerate(pending):
        style_idx = (i + hash(code) % 100) % len(STYLES)
        fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")

        if i % 10 == 0:
            print(f"[{i+1}/{len(pending)}] code_{code} style={style_idx}...", flush=True)

        success = download_image(code, fpath, style_idx)

        if success:
            prog['done'].append(code)
            ok += 1
            print(f"  ✓ OK ({ok})", flush=True)
        else:
            prog['failed'].append(code)
            fail += 1
            print(f"  ✗ FAIL ({fail})", flush=True)

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)

        time.sleep(random.uniform(2, 4))

    print(f"\n{'='*60}", flush=True)
    print(f"再生完成! 本轮: OK={ok} FAIL={fail}", flush=True)
    print(f"总体: 成功={len(prog['done'])}/{len(codes_to_regen)} 失败={len(prog['failed'])}/{len(codes_to_regen)}", flush=True)
    print(f"{'='*60}", flush=True)


# ========================
# MAIN
# ========================
def main():
    print("\n" + "#" * 60)
    print("# MASTER FIX - 层级修复 + 图片再生成")
    print("#" * 60)

    fix_layers()
    codes = find_codes_needing_regen()
    regenerate_images(codes)


if __name__ == "__main__":
    main()
