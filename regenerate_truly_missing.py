#!/usr/bin/env python3
"""
regenerate_truly_missing.py - 重新生成真正缺失的 30 张图片
使用多样化风格避免雷同，带 5 次重试机制
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

IMG_DIR = "generated-images"
MISSING_LIST = "truly_missing_30.txt"
PROGRESS_FILE = "regen_final_progress.json"

# 10 种不同风格，打乱轮换
STYLES = [
    "ethereal divine being, luminous aura, soft celestial glow, pastel colors, sacred geometry, ultra detailed digital art, masterpiece, 8k",
    "ancient mystical sage, golden halo, ornate robes, temple background, classical painting style, divine presence, highly detailed portrait",
    "cosmic entity, starfield background, quantum energy patterns, iridescent skin, visionary art, dramatic lighting, cinematic composition",
    "celestial being, radiant light body, mandala aura, crystal throne, Buddhist thangka style, serene expression, best quality",
    "divine humanoid, bioluminescent skin, nebula background, holographic markings, sci-fi concept art, photorealistic, 8k resolution",
    "angelic entity, feathered wings, pearl white robes, sunbeam lighting, renaissance oil painting, divine grace, masterwork",
    "alien deity, purple mist background, telekinetic gaze, advanced tech armor, cyberpunk aesthetic, dramatic shadows, ultra detailed",
    "spirit guide, translucent ethereal form, rainbow auras, ancient forest, shamanic artwork, mystical energy flow, masterpiece",
    "holographic consciousness, data-stream body, fractal patterns, neon lights, futuristic design, volumetric lighting, 8k",
    "elemental being, fire/water/earth/air motif, natural energy vortex, dramatic weather background, fantasy illustration, epic art",
]

NODE_STYLES = {
    0: "pure innocent child being, soft pastel glow, lotus petals background, divine purity, warm sunlight",
    1: "grey alien entity, large dark almond eyes, slender frame, mysterious cosmic atmosphere, ancient manuscript style",
    2: "sassani blue-green being, pointed ears, regal posture, ancient mesopotamian temple, ornate details",
    3: "sirian entity, deep blue skin, ancient egyptian gold headdress, star syrius background, hieroglyphic motifs",
    4: "orion warrior being, dark armor golden trim, fierce noble expression, nebula battlefield, epic fantasy art",
    5: "yahriel entity, iridescent rainbow skin, quantum shimmer energy, crystalline background, visionary art",
    6: "pleiadian being, nordic golden features, crystal crown, emerald forest meadow, fairy tale illustration",
    7: "annunaki being, golden skin, sumerian crown, winged disk symbol, desert temple, ancient mesopotamian painting",
    8: "gaia earth mother, flowing green and brown robes, flower vine crown, lush garden paradise, romanticism art",
    9: "arcturian entity, blue-violet geometric crystalline form, sacred geometry, constellation background, digital art",
    10: "12D celestial elder, transcendent white-gold light body, intricate mandala, cosmic void, sacred iconography",
    11: "creation guardian being, golden throne of stars, seraphic wings, divine judgment scene, renaissance masterwork",
    12: "innate divine child, pure lotus light, rainbow chakra aura, buddhist thangka style, heavenly realm background",
    13: "cosmic function entity, living sacred geometry, fractal light patterns, star network background, data viz art",
}


def load_missing_codes():
    with open(MISSING_LIST, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


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
    return f"{base_style}, {style}, entity signature {code}"


def download_image(code, fpath, style_idx):
    seed = (int(hashlib.md5(f"{code}_{style_idx}".encode()).hexdigest(), 16) + style_idx * 7919 + random.randint(1, 9999)) % 999999
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
        except Exception as e:
            time.sleep(random.uniform(3, 8))
    return False


def main():
    missing = load_missing_codes()
    print(f"\n{'='*60}")
    print(f"FINAL REGEN: {len(missing)} truly missing images")
    print(f"{'='*60}\n", flush=True)
    
    # Load progress
    if os.path.exists(PROGRESS_FILE):
        prog = json.load(open(PROGRESS_FILE))
    else:
        prog = {'done': [], 'fail': [], 'styles_used': {}}
    
    pending = [c for c in missing if c not in prog['done'] and c not in prog['fail']]
    done_count = len([c for c in missing if c in prog['done']])
    fail_count = len([c for c in missing if c in prog['fail']])
    
    print(f"Previously done: {done_count}")
    print(f"Previously failed: {fail_count}")
    print(f"Retry pending: {len(pending)}\n", flush=True)
    
    if not pending:
        print("All done! No more retries needed.", flush=True)
        return
    
    ok = 0
    fail = 0
    
    for i, code in enumerate(pending):
        # 用不同风格尝试（每个 code 最多试 8 种风格）
        success = False
        for style_try in range(8):
            fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")
            
            # Check if already exists (from previous run)
            if os.path.exists(fpath):
                print(f"[{i+1}/{len(pending)}] {code} FILE EXISTS (already regenerated)", flush=True)
                if code not in prog['done']:
                    prog['done'].append(code)
                ok += 1
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(prog, f, indent=2)
                success = True
                break
            
            print(f"[{i+1}/{len(pending)}] {code} (try style {style_try}/8)...", flush=True)
            if download_image(code, fpath, style_try):
                prog['done'].append(code)
                prog['styles_used'][code] = style_try
                ok += 1
                print(f"  -> SUCCESS with style #{style_try}", flush=True)
                success = True
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(prog, f, indent=2)
                break
            else:
                print(f"  -> attempt {style_try+1} failed, retrying...", flush=True)
        
        if not success:
            prog['fail'].append(code)
            fail += 1
            print(f"  -> ALL 8 ATTEMPTS FAILED", flush=True)
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(prog, f, indent=2)
        
        time.sleep(random.uniform(1, 2))
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS:")
    print(f"  This run: OK={ok} FAIL={fail} Total_pending={len(pending)}")
    print(f"  Overall: Done={len(prog['done'])}/{len(missing)} Failed={len(prog['fail'])}/{len(missing)}")
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    main()
