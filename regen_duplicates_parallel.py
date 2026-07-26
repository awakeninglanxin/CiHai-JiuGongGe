#!/usr/bin/env python3
"""
regen_duplicates_parallel.py - 并发批量重新生成重复图片
5线程并发 + 断点续传 + 唯一seed
"""

import hashlib
import os
import re
import time
import random
import json
import urllib.request
import urllib.parse
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

IMG_DIR = "generated-images"
DEITIES_JS = "deities.js"
PROGRESS_FILE = "regen_progress.json"
PROGRESS_LOCK = threading.Lock()

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
    matches = re.findall(pattern, content)
    for code, node in matches:
        _node_cache[code] = int(node)

def get_node_for_code(code):
    if code in _node_cache:
        return _node_cache[code]
    code_stripped = code.lstrip('0')
    if code_stripped:
        last_digit = int(code_stripped[-1])
        return last_digit if last_digit <= 13 else 0
    return 0

def generate_unique_seed(code, index):
    base_hash = int(hashlib.md5(code.encode()).hexdigest(), 16) % 100000
    return (base_hash + index * 7919 + random.randint(1, 9999)) % 999999

def download_image(code, node, seed, max_retries=3):
    prompt = f"{NODE_PROMPTS.get(node, NODE_PROMPTS[0])}, {QUALITY_SUFFIX}"
    prompt_with_code = f"{prompt}, divine essence {code}"
    encoded_prompt = urllib.parse.quote(prompt_with_code)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed}&nologo=true"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'image/*',
            })
            with urllib.request.urlopen(req, timeout=120) as response:
                img_data = response.read()
                if len(img_data) > 5000:
                    return img_data
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return None
    return None

def find_duplicate_groups():
    hash_to_files = defaultdict(list)
    for fname in os.listdir(IMG_DIR):
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.isfile(fpath) and fname.lower().endswith(('.jpg', '.png', '.jpeg')):
            with open(fpath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            code_match = re.match(r'code_(.+)\.(jpg|png|jpeg)', fname)
            if code_match:
                code = code_match.group(1).replace('_v1restored', '')
                hash_to_files[file_hash].append({
                    'filename': fname,
                    'code': code,
                    'filepath': fpath,
                })
    return {h: files for h, files in hash_to_files.items() if len(files) > 1}

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': []}

def save_progress(progress):
    with PROGRESS_LOCK:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)

def process_one(item, progress, stats):
    """处理单个图片下载"""
    code = item['code']
    filename = item['filename']
    filepath = item['filepath']
    node = get_node_for_code(code)
    seed = generate_unique_seed(code, item['group_index'])
    
    img_data = download_image(code, node, seed)
    
    with PROGRESS_LOCK:
        if img_data:
            with open(filepath, 'wb') as f:
                f.write(img_data)
            progress['completed'].append(filename)
            stats['success'] += 1
            result = f"✓ {code}"
        else:
            progress['failed'].append(filename)
            stats['fail'] += 1
            result = f"✗ {code}"
        save_progress(progress)
        stats['done'] += 1
        done = stats['done']
        total = stats['total']
    
    print(f"[{done}/{total}] {result}", flush=True)
    return result

def main():
    print("=" * 70)
    print("并发批量重新生成重复图片 (5线程)")
    print("=" * 70)
    
    load_node_cache()
    dup_groups = find_duplicate_groups()
    
    regen_list = []
    for h, files in dup_groups.items():
        for i, file_info in enumerate(files):
            regen_list.append({
                'code': file_info['code'],
                'filename': file_info['filename'],
                'filepath': file_info['filepath'],
                'group_index': i,
            })
    
    print(f"重复组数: {len(dup_groups)}")
    print(f"需要重新生成: {len(regen_list)} 张图片")
    
    progress = load_progress()
    completed_files = set(progress['completed'])
    pending = [item for item in regen_list if item['filename'] not in completed_files]
    print(f"已完成: {len(completed_files)} 待生成: {len(pending)}")
    
    if not pending:
        print("全部完成!")
        return
    
    print(f"\n开始并发生成 (5线程, 预计 {len(pending) * 4 / 60:.0f} 分钟)...")
    
    stats = {'success': 0, 'fail': 0, 'done': 0, 'total': len(pending)}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_one, item, progress, stats): item 
                   for item in pending}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with PROGRESS_LOCK:
                    stats['fail'] += 1
                    stats['done'] += 1
                print(f"异常: {e}", flush=True)
    
    print(f"\n{'=' * 70}")
    print(f"完成! 成功={stats['success']} 失败={stats['fail']} 总计={stats['total']}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
