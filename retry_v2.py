#!/usr/bin/env python3
"""retry_v2.py - 第二轮重试失败图片，更强策略"""

import re
import os
import time
import random
import hashlib
import json
import urllib.request
import urllib.parse

sys = __import__('sys')
sys.stdout.reconfigure(line_buffering=True)

IMG_DIR = "generated-images"

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


def build_prompt(code, style_idx, extra_tag=""):
    node = get_node(code)
    base = NODE_STYLES.get(node, NODE_STYLES[0])
    style = STYLES[style_idx % len(STYLES)]
    prompt = f"{base}, {style}{QUALITY}"
    if extra_tag:
        prompt += f", {extra_tag}"
    return prompt


def download_image(code, fpath, style_idx, round_num):
    """尝试多个不同 seed + 多个 style_idx 组合"""
    base_seed = int(hashlib.sha256(f"round{round_num}_{code}".encode()).hexdigest(), 16)
    
    # 每个 code 尝试 5 个不同 seed + 2 个不同 style
    for s in range(2):
        sid = (style_idx + s * 3 + round_num) % len(STYLES)
        for sec in range(5):
            seed = (base_seed + sec * 10007 + round_num * 31337 + s * 777) % 999999999
            extra = f"version_{round_num}_sec{sec}"
            prompt = build_prompt(code, sid, extra_tag=extra)
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
            
            for attempt in range(15):
                try:
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                        'Accept': 'image/*'
                    })
                    with urllib.request.urlopen(req, timeout=240) as resp:
                        data = resp.read()
                    if len(data) > 5000:
                        with open(fpath, 'wb') as f:
                            f.write(data)
                        return True
                except Exception:
                    time.sleep(random.uniform(8, 20))
    
    return False


# ========== 主流程 ==========
print("=" * 60, flush=True)
print("RETRY V2 - ROUND 1", flush=True)
print("=" * 60, flush=True)

PROGRESS_FILE = "final_master_fix_progress.json"
prog = json.load(open(PROGRESS_FILE, 'r', encoding='utf-8'))

failed = prog.get('failed', [])
print(f"Candidates: {len(failed)}", flush=True)

if not failed:
    print("All done!", flush=True)
else:
    ok = 0
    still_failed = 0
    
    for i, code in enumerate(failed):
        style_idx = (i + round(0)) % 100
        fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")
        
        if i % 10 == 0:
            print(f"[{i+1}/{len(failed)}] code_{code}...", flush=True)
        
        if download_image(code, fpath, style_idx, round_num=0):
            if code in prog['failed']:
                prog['failed'].remove(code)
            prog['done'].append(code)
            ok += 1
            print(f"  ✓ OK ({ok})", flush=True)
        else:
            still_failed += 1
            if still_failed <= 5 or still_failed % 10 == 0:
                print(f"  ✗ Round0 ({still_failed})", flush=True)
        
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)
        
        time.sleep(random.uniform(3, 5))
    
    print(f"\n  ROUND 0 DONE: OK={ok} STILL={still_failed}", flush=True)
    print(f"  Total: done={len(prog['done'])} failed={len(prog['failed'])}", flush=True)
