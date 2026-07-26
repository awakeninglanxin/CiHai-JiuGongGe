#!/usr/bin/env python3
"""
regenerate_missing.py - 重新生成被删除/缺失的图片
支持风格选项：pristine, dark, ethereal, ancient, modern
"""

import hashlib
import os
import re
import sys
import time
import random
import json
import urllib.request

sys.stdout.reconfigure(line_buffering=True)

IMG_DIR = "generated-images"
DEITIES_JS = "deities.js"
MISSING_LIST = "missing_codes_list.txt"
PROGRESS_FILE = "regen_missing_progress.json"

# 风格提示词库 - 可以循环使用不同的风格组合
STYLE_PACKS = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry, ultra detailed digital art",
    "ancient mystical being, golden halo, ornate robes, temple background, classical painting style, divine presence, ultra detailed",
    "cosmic being, starfield background, quantum energy patterns, iridescent skin, large almond eyes, visionary art, masterpiece",
    "celestial entity, radiant light body, mandala aura, crystal throne, Buddhist art style, serene expression, highly detailed",
    "divine humanoid, bioluminescent skin, nebula background, holographic markings, sci-fi concept art, 8k resolution",
    "angelic being, feathered wings, pearl white robes, sunbeam lighting, renaissance painting style, divine grace",
    "alien deity, purple mist background, telekinetic gaze, advanced tech armor, cinematic lighting, dramatic composition",
    "spirit guide, translucent ethereal form, rainbow auras, ancient forest, shamanic artwork, mystical energy, best quality",
    "holographic being, data-stream body, cyberpunk aesthetic, neon lights, futuristic design, photorealistic, masterpiece",
    "elemental spirit, fire/water/earth/air motif, natural energy, dramatic weather background, fantasy illustration, epic art",
]

NODE_STYLES = {
    0: "innocent divine child, pure white light, pastel aura, lotus background, sacred innocence",
    1: "grey alien federation, large dark almond eyes, slender frame, mysterious cosmic atmosphere, manuscript style",
    2: "sassani hybrid, blue-green skin, pointed ears, regal posture, ancient mesopotamian background",
    3: "sirian being, deep blue skin, ancient egyptian gold headdress, star syrius background, hieroglyphic art",
    4: "orion warrior, dark armor golden trim, fierce noble expression, nebula battlefield, epic fantasy art",
    5: "yahyel being, iridescent rainbow skin, quantum shimmer, crystalline energy field, visionary art",
    6: "pleiadian being, nordic golden features, crystal crown, emerald forest, fairy tale illustration",
    7: "annunaki, golden skin, sumerian crown, winged disk, desert temple, ancient mesopotamian oil painting",
    8: "gaia earth mother, flowing green and brown robes, flower vine crown, lush garden, classical romanticism",
    9: "arcturian, blue-violet geometric crystalline form, sacred geometry patterns, star constellation, digital art",
    10: "12D celestial elder, transcendent white-gold light body, intricate mandala, cosmic void, sacred iconography",
    11: "creation guardian, golden throne of stars, seraphic wings, divine judgment scene, renaissance masterwork",
    12: "innate divine child, pure lotus light, rainbow chakra aura, buddhist thangka style, heavenly realm",
    13: "cosmic function being, living sacred geometry, fractal light patterns, star network background, data visualization art",
}

QUALITY_BOOST = ", ultra detailed, 8k, masterpiece, best quality, highly detailed face, symmetrical features, cinematic lighting"


def load_missing_codes():
    """从 missing_codes_list.txt 读取缺失的 code 列表"""
    with open(MISSING_LIST, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def get_node(code):
    """根据 code 推断所属 node (0-13)"""
    s = code.lstrip('0')
    if s:
        d = int(s[-1])
        return d if d <= 13 else 0
    return 0


def build_prompt(code, style_idx):
    """构建完整的生成 prompt"""
    node = get_node(code)
    base_style = NODE_STYLES.get(node, NODE_STYLES[0])
    style_pack = STYLE_PACKS[style_idx % len(STYLE_PACKS)]
    prompt = f"{base_style}, {style_pack}{QUALITY_BOOST}, entity signature {code}"
    return prompt


def download_image(url, filepath, timeout=120):
    """下载图片，带重试"""
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'image/*'
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if len(data) > 5000:
                with open(filepath, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e:
            time.sleep(random.uniform(2, 5))
    return False


def main():
    missing_codes = load_missing_codes()
    print(f"\n{'='*60}")
    print(f"Regenerating {len(missing_codes)} missing images")
    print(f"{'='*60}\n", flush=True)
    
    # 加载进度
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            prog = json.load(f)
    else:
        prog = {'completed': [], 'failed': [], 'total': 0, 'success_count': 0, 'fail_count': 0}
    
    done_set = set(prog['completed'])
    pending = [c for c in missing_codes if c not in done_set]
    
    prog['total'] = len(missing_codes)
    prog['success_count'] = len([c for c in missing_codes if c in done_set])
    prog['fail_count'] = len([c for c in prog['failed']])
    
    print(f"Already done: {prog['success_count']}")
    print(f"Already failed: {prog['fail_count']}")
    print(f"Pending: {len(pending)}\n", flush=True)
    
    if not pending:
        print("All missing images regenerated! Or all 5 attempts exhausted.", flush=True)
        return
    
    ok = 0
    fail = 0
    
    for i, code in enumerate(pending):
        seed = (int(hashlib.md5(code.encode()).hexdigest(), 16) % 100000 + 
                i * 7919 + random.randint(1, 9999)) % 999999
        style_idx = (i + hash(code) % 100) % len(STYLE_PACKS)  # 多样化风格
        
        prompt = build_prompt(code, style_idx)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
        
        fname = f"code_{code}.jpg"
        fpath = os.path.join(IMG_DIR, fname)
        
        print(f"[{i+1}/{len(pending)}] {code} (node={get_node(code)}, style={style_idx})...", flush=True)
        
        success = download_image(url, fpath)
        
        if success:
            prog['completed'].append(code)
            prog['success_count'] += 1
            ok += 1
            print(f"  -> OK! ({ok} success this run)", flush=True)
        else:
            prog['failed'].append(code)
            prog['fail_count'] += 1
            fail += 1
            print(f"  -> FAILED ({fail} failures this run)", flush=True)
        
        # 保存进度（每次迭代都更新）
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)
        
        # 间隔避免触发 API 限流
        time.sleep(random.uniform(1.5, 3))
    
    print(f"\n{'='*60}")
    print(f"Complete! This run: OK={ok} FAIL={fail}")
    print(f"Total progress: Success={prog['success_count']}/{len(missing_codes)}")
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    main()
