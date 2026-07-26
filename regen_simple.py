#!/usr/bin/env python3
"""
regen_simple.py - 简化版批量重新生成重复图片
单线程 + 无缓冲输出 + 断点续传
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
from collections import defaultdict

# 确保无缓冲输出
sys.stdout.reconfigure(line_buffering=True)

IMG_DIR = "generated-images"
DEITIES_JS = "deities.js"
PROGRESS_FILE = "regen_progress.json"

NODE_PROMPTS = {
    0: "ethereal divine child, innocent face, glowing aura, soft pastel colors, celestial background, ancient Chinese painting style",
    1: "mysterious grey alien being, large dark eyes, slender grey body, ethereal cosmic background, ancient manuscript style",
    2: "Sassani hybrid being, blue-green skin, pointed ears, serene expression, cosmic light, ancient temple background",
    3: "Sirian being, deep blue skin, ancient Egyptian attire, starry background, hieroglyphic motifs, classical painting",
    4: "Orion warrior, strong features, dark armor with golden trim, fierce but noble expression, nebula background, epic fantasy art",
    5: "Yahyel being, iridescent rainbow skin, large almond eyes, quantum energy patterns, crystalline background, visionary art",
    6: "Pleiadian being, Nordic features, blonde hair, crystal crown, natural light, forest meadow background, ethereal painting",
    7: "Anunnaki being, tall muscular figure, golden skin, ancient Sumerian crown, winged disk symbol, desert temple background",
    8: "Gaia earth goddess, flowing green robes, vine crown, nurturing expression, lush nature background, classical oil painting",
    9: "Arcturian being, blue-violet geometric form, crystalline body, sacred geometry patterns, star field background, digital art",
    10: "celestial elder, twelve dimensional being, transcendent light body, mandala aura, cosmic void background, sacred art",
    11: "creation guardian, nine to eleven dimensional being, golden light form, throne of stars, divine background, classical art",
    12: "innate divine child, pure light being, lotus throne, rainbow aura, heaven background, Buddhist art style",
    13: "cosmic function being, geometric light form, sacred geometry, star network background, digital visionary art",
}

QUALITY_SUFFIX = "ultra detailed digital art, cinematic lighting, 8k, masterpiece, best quality, highly detailed face, symmetrical features"

_node_cache = {}

def load_node_cache():
    global _node_cache
    with open(DEITIES_JS, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'code:"(\d+)".*?node:(\d+)'
    for code, node in re.findall(pattern, content):
        _node_cache[code] = int(node)
    print(f"Loaded {len(_node_cache)} code->node mappings", flush=True)

def get_node(code):
    if code in _node_cache:
        return _node_cache[code]
    s = code.lstrip('0')
    if s:
        d = int(s[-1])
        return d if d <= 13 else 0
    return 0

def find_dup_groups():
    h2f = defaultdict(list)
    for fname in os.listdir(IMG_DIR):
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.isfile(fpath) and fname.lower().endswith(('.jpg', '.png', '.jpeg')):
            with open(fpath, 'rb') as f:
                fh = hashlib.md5(f.read()).hexdigest()
            m = re.match(r'code_(.+)\.(jpg|png|jpeg)', fname)
            if m:
                code = m.group(1).replace('_v1restored', '')
                h2f[fh].append({'filename': fname, 'code': code, 'filepath': fpath})
    return {h: fs for h, fs in h2f.items() if len(fs) > 1}

def main():
    print("=" * 60, flush=True)
    print("Batch regenerate duplicate images", flush=True)
    print("=" * 60, flush=True)
    
    load_node_cache()
    groups = find_dup_groups()
    
    regen = []
    for h, files in groups.items():
        for i, fi in enumerate(files):
            regen.append({**fi, 'idx': i})
    
    # Load progress
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            prog = json.load(f)
    else:
        prog = {'completed': [], 'failed': []}
    
    done_set = set(prog['completed'])
    pending = [r for r in regen if r['filename'] not in done_set]
    
    print(f"Total: {len(regen)}, Done: {len(done_set)}, Pending: {len(pending)}", flush=True)
    
    if not pending:
        print("All done!", flush=True)
        return
    
    ok = 0
    fail = 0
    
    for i, item in enumerate(pending):
        code = item['code']
        fname = item['filename']
        fpath = item['filepath']
        node = get_node(code)
        seed = (int(hashlib.md5(code.encode()).hexdigest(), 16) % 100000 + item['idx'] * 7919 + random.randint(1, 9999)) % 999999
        
        prompt = f"{NODE_PROMPTS.get(node, NODE_PROMPTS[0])}, {QUALITY_SUFFIX}, divine essence {code}"
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&seed={seed}&nologo=true"
        
        success = False
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'image/*'})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = resp.read()
                if len(data) > 5000:
                    with open(fpath, 'wb') as f:
                        f.write(data)
                    success = True
                    break
            except Exception:
                time.sleep(3)
        
        if success:
            prog['completed'].append(fname)
            ok += 1
            print(f"[{i+1}/{len(pending)}] {code} OK", flush=True)
        else:
            prog['failed'].append(fname)
            fail += 1
            print(f"[{i+1}/{len(pending)}] {code} FAIL", flush=True)
        
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(prog, f)
        
        time.sleep(1)
        
        if (i + 1) % 100 == 0:
            print(f"--- Progress: {i+1}/{len(pending)} OK={ok} FAIL={fail} ---", flush=True)
    
    print(f"\nDone! OK={ok} FAIL={fail} Total={len(pending)}", flush=True)

if __name__ == "__main__":
    main()
