#!/usr/bin/env python3
"""retry_failed.py - 重试之前失败的图片生成"""

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


def build_prompt(code, style_idx):
    node = get_node(code)
    base = NODE_STYLES.get(node, NODE_STYLES[0])
    style = STYLES[style_idx % len(STYLES)]
    return f"{base}, {style}{QUALITY}"


def download_image(code, fpath, style_idx, retry_round=0):
    seed = (int(hashlib.md5(f"retry_{code}_{style_idx}_{retry_round}".encode()).hexdigest(), 16) +
            style_idx * 7919 + random.randint(1, 99999)) % 999999999
    prompt = build_prompt(code, style_idx)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
    for attempt in range(12):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'image/*'
            })
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if len(data) > 5000:
                with open(fpath, 'wb') as f:
                    f.write(data)
                return True
        except Exception:
            time.sleep(random.uniform(5, 15))
    return False


# ========== 主流程 ==========
print("=" * 60, flush=True)
print("RETRY FAILED IMAGES", flush=True)
print("=" * 60, flush=True)

PROGRESS_FILE = "final_master_fix_progress.json"
prog = json.load(open(PROGRESS_FILE, 'r', encoding='utf-8'))

failed = prog.get('failed', [])
print(f"Failed to retry: {len(failed)}", flush=True)

if not failed:
    print("Nothing to do!", flush=True)
else:
    ok = 0
    still_failed = 0
    
    for i, code in enumerate(failed):
        style_idx = (i + abs(hash(code)) % 100) % len(STYLES)
        fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")
        
        if i % 10 == 0:
            print(f"[{i+1}/{len(failed)}] code_{code}...", flush=True)
        
        if download_image(code, fpath, style_idx, retry_round=len(failed) // 60):
            if code in prog['failed']:
                prog['failed'].remove(code)
            prog['done'].append(code)
            ok += 1
            print(f"  ✓ OK ({ok})", flush=True)
        else:
            still_failed += 1
            print(f"  ✗ Still failed ({still_failed})", flush=True)
        
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)
        
        time.sleep(random.uniform(2, 4))
    
    print(f"\n  RETRY DONE: OK={ok} STILL_FAILED={still_failed}", flush=True)
    print(f"  Total: done={len(prog['done'])} failed={len(prog['failed'])}", flush=True)

print("\n" + "=" * 60, flush=True)
print("FINISHED!", flush=True)
print("=" * 60, flush=True)
