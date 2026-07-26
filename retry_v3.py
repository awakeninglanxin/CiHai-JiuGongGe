#!/usr/bin/env python3
"""retry_v3.py - 最终轮重试，最强策略"""

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
    "zen meditation deity, calm serene face, golden lotus petals, soft morning light, watercolor",
    "futuristic enlightened master, neon temple, holographic mandalas, cyber zen, digital art",
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


def download_single(code, fpath, seed, prompt_extra):
    """尝试单个 seed+prompt 组合"""
    node = get_node(code)
    base = NODE_STYLES.get(node, NODE_STYLES[0])
    style_idx = hash(seed) % len(STYLES)
    style = STYLES[style_idx]
    prompt = f"{base}, {style}{QUALITY}"
    if prompt_extra:
        prompt += f", {prompt_extra}"

    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'image/*'
        })
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read()
        if len(data) > 5000:
            with open(fpath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False


# ========== 主流程 ==========
print("=" * 60, flush=True)
print("RETRY V3 - FINAL ROUND", flush=True)
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

    total_seeds_per_code = 20  # 每张图试 20 个不同 seed
    timeout_base = 300  # 300s timeout per request

    for i, code in enumerate(failed):
        fpath = os.path.join(IMG_DIR, f"code_{code}.jpg")

        if i % 10 == 0:
            print(f"[{i+1}/{len(failed)}] code_{code} (trying {total_seeds_per_code} seeds)...", flush=True)

        success = False
        base_seed = int(hashlib.sha256(f"v3_{code}".encode()).hexdigest(), 16)

        for sec in range(total_seeds_per_code):
            seed = (base_seed + sec * 10009 + i * 37991) % 9999999999
            extra = f"v3_try{sec}"
            if download_single(code, fpath, seed, extra):
                success = True
                break
            else:
                time.sleep(random.uniform(5, 10))

        if success:
            if code in prog['failed']:
                prog['failed'].remove(code)
            prog['done'].append(code)
            ok += 1
            print(f"  ✓ OK ({ok})", flush=True)
        else:
            still_failed += 1
            if still_failed <= 10:
                print(f"  ✗ FINAL FAIL ({still_failed})", flush=True)

        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f, indent=2)

        time.sleep(random.uniform(4, 8))

    print(f"\n  FINAL ROUND DONE: OK={ok} STILL_FAILED={still_failed}", flush=True)
    print(f"  Total: done={len(prog['done'])} failed={len(prog['failed'])}", flush=True)

    # Save final failure list to separate file for manual review
    if still_failed > 0:
        with open("permanently_failed_codes.txt", 'w', encoding='utf-8') as f:
            f.write("These codes failed all retry attempts. Manual intervention required.\n")
            for c in prog['failed']:
                f.write(c + '\n')
        print(f"  Saved permanently failed list to: permanently_failed_codes.txt", flush=True)

print("\n" + "=" * 60, flush=True)
print("ALL DONE!", flush=True)
print("=" * 60, flush=True)
