#!/usr/bin/env python3
"""
regen_duplicates.py v2 - 批量重新生成重复图片
优化: 缓存node映射 + 断点续传 + 唯一seed避免缓存
"""

import hashlib
import os
import re
import time
import random
import json
import urllib.request
import urllib.parse
from collections import defaultdict

IMG_DIR = "generated-images"
DEITIES_JS = "deities.js"
PROGRESS_FILE = "regen_progress.json"

# v1 风格 Node Prompt
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

# 缓存 node 映射
_node_cache = {}

def load_node_cache():
    """从 deities.js 一次性加载所有 code->node 映射"""
    global _node_cache
    with open(DEITIES_JS, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'code:"(\d+)".*?node:(\d+)'
    matches = re.findall(pattern, content)
    for code, node in matches:
        _node_cache[code] = int(node)
    print(f"已加载 {len(_node_cache)} 个 code->node 映射")

def get_node_for_code(code):
    """获取 code 对应的 node"""
    if code in _node_cache:
        return _node_cache[code]
    # 用code最后一位推断
    code_stripped = code.lstrip('0')
    if code_stripped:
        last_digit = int(code_stripped[-1])
        return last_digit if last_digit <= 13 else 0
    return 0

def generate_unique_seed(code, index):
    """为每个code生成唯一seed，加入index确保同组内不重复"""
    base_hash = int(hashlib.md5(code.encode()).hexdigest(), 16) % 100000
    return (base_hash + index * 7919 + random.randint(1, 9999)) % 999999

def download_image(code, node, seed, max_retries=3):
    """下载生成的图片"""
    prompt = f"{NODE_PROMPTS.get(node, NODE_PROMPTS[0])}, {QUALITY_SUFFIX}"
    # 加入code作为唯一标识
    prompt_with_code = f"{prompt}, divine essence {code}"
    
    encoded_prompt = urllib.parse.quote(prompt_with_code)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed}&nologo=true"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'image/*',
            })
            with urllib.request.urlopen(req, timeout=90) as response:
                img_data = response.read()
                if len(img_data) > 5000:
                    return img_data
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return None
    return None

def find_duplicate_groups():
    """找出所有重复图片组"""
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
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': []}

def save_progress(progress):
    """保存进度"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    print("=" * 70)
    print("批量重新生成重复图片 v2")
    print("=" * 70)
    
    # 加载 node 缓存
    load_node_cache()
    
    # 找出所有重复组
    dup_groups = find_duplicate_groups()
    
    # 收集需要重新生成的文件
    # 用户要求"不要这种"——所有重复组内的全部文件都要重新生成
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
    
    # 加载进度
    progress = load_progress()
    completed_files = set(progress['completed'])
    
    # 过滤已完成的（按文件名追踪）
    pending = [item for item in regen_list if item['filename'] not in completed_files]
    print(f"已完成: {len(completed_files)} 待生成: {len(pending)}")
    
    if not pending:
        print("全部完成!")
        return
    
    print(f"\n开始生成... (预计每张约6-8秒)")
    
    success_count = 0
    fail_count = 0
    
    for i, item in enumerate(pending):
        code = item['code']
        filename = item['filename']
        filepath = item['filepath']
        node = get_node_for_code(code)
        seed = generate_unique_seed(code, item['group_index'])
        
        print(f"[{i+1}/{len(pending)}] code={code} node={node} seed={seed}...", end=" ", flush=True)
        
        img_data = download_image(code, node, seed)
        
        if img_data:
            # 保存新图片
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            progress['completed'].append(filename)
            save_progress(progress)
            success_count += 1
            print("✓")
        else:
            progress['failed'].append(filename)
            save_progress(progress)
            fail_count += 1
            print("✗ (保留原图)")
        
        # 间隔等待
        time.sleep(2)
        
        # 每50张汇报
        if (i + 1) % 50 == 0:
            print(f"\n--- 进度: {i+1}/{len(pending)} 成功={success_count} 失败={fail_count} ---\n")
    
    print(f"\n{'=' * 70}")
    print(f"完成! 成功={success_count} 失败={fail_count} 总计={len(pending)}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
