#!/usr/bin/env python3
"""
增量生成慈海九宫格缺失的大神AI肖像 v4
- 修正：使用 shutil.copy2 跨盘复制
- 支持中断续跑，只生成还未生成的 code
"""
import os
import json
import time
import random
import requests
import shutil
import tempfile
import threading
import re

OUTPUT_DIR = r'D:\AAA我的文件\慈海九宫格_整合版\generated-images'
TMP_DIR = tempfile.mkdtemp(prefix='deities_v4_')

# Load all missing codes
with open('D:/temp/deities_missing.json', 'r', encoding='utf-8') as f:
    all_missing = json.load(f)

print(f"Total codes to process: {len(all_missing)}")

# Extract existing codes from generated-images
existing_codes = set()
if os.path.exists(OUTPUT_DIR):
    for fn in os.listdir(OUTPUT_DIR):
        m = re.match(r'code_(.+?)_\d+\.jpg$', fn)
        if m:
            code = m.group(1)
            fp = os.path.join(OUTPUT_DIR, fn)
            try:
                if os.path.getsize(fp) >= 50000:
                    existing_codes.add(code)
            except:
                pass

print(f"Already generated: {len(existing_codes)}")

# Find codes that still need generation
need_gen = [e for e in all_missing if e['code'] not in existing_codes]
print(f"Still need generation: {len(need_gen)}")

if not need_gen:
    print("All codes already generated! Nothing to do.")
    exit(0)

# Prompt templates
ancient = 'Ancient%20Chinese%20mythology%20divine%20deity%20portrait%2C%20majestic%20transcendent%20immortal%20sage%20with%20jade%20imperial%20headdress%2C%20flowing%20silk%20ceremonial%20robes%2C%20ethereal%20clouds%20background%2C%20traditional%20Eastern%20masterpiece%20painting'
future = 'Futuristic%20cosmic%20deity%20avatar%2C%20humanoid%20being%20in%20shimmering%20iridescent%20quantum%20armor%20with%20holographic%20energy%20shields%2C%20hovering%20anti-gravity%20disc%20platform%2C%20floating%20sacred%20geometries%20and%20Platonic%20solids%2C%20sleek%20UFO%20mothership%20silhouettes%20in%20nebula%20sky%2C%20bioluminescent%20energy%20crystals%20orbiting%2C%20cinematic%20composition%2C%20photorealistic%20digital%20painting'

ok = 0
fail = 0
failed_codes = []
start = time.time()

# Progress display thread
stop_event = threading.Event()
def progress_reporter():
    while not stop_event.is_set():
        time.sleep(2)
        try:
            elapsed = time.time() - start
            total = len(need_gen)
            pct = (ok + fail) * 100 // total
            bar_len = min(pct, 100)
            bar = '#' * bar_len + '.' * (100 - bar_len)
            rate = (ok + fail) / max(elapsed, 0.01)
            remaining = total - (ok + fail)
            eta = remaining / rate
            text = f"[progress] {pct}% ok={ok} fail={fail} ETA={int(eta//60)}m{int(eta%60)}s [{bar}]"
            print(text, flush=True)
        except:
            pass

pr = threading.Thread(target=progress_reporter, daemon=True)
pr.start()

print(f"\nStarting generation of {len(need_gen)} images...")
print(f"Temp dir: {TMP_DIR}")
print("=" * 60)

for idx, entry in enumerate(need_gen):
    code = entry['code']
    freq = entry['freq']
    style = future if freq < 5 else ancient
    seed = random.randint(1, 999999)
    ts = str(int(time.time() * 1000) + random.randint(10000, 99999))
    filename = 'code_' + code + '_' + ts + '.jpg'
    filepath = os.path.join(TMP_DIR, filename)
    
    # Build URL
    base_prompt = style
    params = f'?width=1024&height=1024&seed={seed}&model=flux'
    url = 'https://image.pollinations.ai/prompt/' + base_prompt + params
    
    success = False
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=600, stream=True, proxies=None)
            if resp.status_code == 200:
                with open(filepath, 'wb') as out:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            out.write(chunk)
                
                if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
                    success = True
                    break
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception as e:
            err_msg = str(e)
            if 'timed out' not in err_msg.lower() and 'connection' not in err_msg.lower():
                print(f'  Error: {err_msg}', flush=True)
        
        if not success and attempt < 2:
            wait = 2 + (attempt + 1) * 2
            time.sleep(wait)
    
    elapsed_now = time.time() - start
    if success:
        ok += 1
    else:
        fail += 1
        failed_codes.append(code)
    
    # Show per-item progress every 5 items
    if (idx + 1) % 5 == 0 or idx + 1 == len(need_gen):
        pct = (idx + 1) * 100 // len(need_gen)
        bar_len = min(pct, 100)
        bar = '#' * bar_len + '.' * (100 - bar_len)
        rate = (idx + 1) / max(elapsed_now, 0.01)
        remaining_items = len(need_gen) - (idx + 1)
        eta = remaining_items / rate
        print(f"[{bar}] {pct}% item={idx+1}/{len(need_gen)} ok={ok} fail={fail} ETA={int(eta//60)}m{int(eta%60)}s", flush=True)
    
    time.sleep(0.3)

# Signal progress reporter to stop
stop_event.set()

# Copy success files to OUTPUT_DIR using shutil.copy2
copied = 0
moved = 0
for fn in os.listdir(TMP_DIR):
    src = os.path.join(TMP_DIR, fn)
    dst = os.path.join(OUTPUT_DIR, fn)
    if os.path.exists(dst):
        moved += 1
    else:
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as e:
            print(f'Copy error {fn}: {e}', flush=True)

elapsed = time.time() - start
print(f'\n=== DONE in {elapsed/60:.1f}m ===', flush=True)
print(f'OK: {ok} | Fail: {fail} | Total attempted: {ok+fail}', flush=True)
print(f'Copied: {copied} | Existing: {moved}', flush=True)
if failed_codes:
    print(f'Failed codes: {failed_codes}', flush=True)

# Cleanup temp
try:
    shutil.rmtree(TMP_DIR)
except:
    pass

print(f"\nFinal count in {OUTPUT_DIR}:")
total_files = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.jpg') and os.path.getsize(os.path.join(OUTPUT_DIR, f)) >= 50000])
print(f"Total valid images: {total_files}", flush=True)
