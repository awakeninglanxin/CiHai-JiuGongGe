#!/usr/bin/env python3
"""
批量生成慈海九宫格缺失的大神AI肖像
使用 requests 下载，单线程但带重试和进度显示
"""
import os
import re
import json
import time
import random
import requests
import shutil
import tempfile
import threading

OUTPUT_DIR = r'D:/AAA我的文件/慈海九宫格_整合版/generated-images'
TMP_DIR = tempfile.mkdtemp(prefix='deities_gen_final_')
PROGRESS_LOCK = threading.Lock()

# Progress display thread
stop_event = threading.Event()

def progress_reporter():
    while not stop_event.is_set():
        time.sleep(2)
        try:
            with open(os.path.join(TMP_DIR, 'progress.txt'), 'r') as f:
                print(f.read().strip(), flush=True)
        except:
            pass

def save_progress(ok, fail, total, elapsed):
    pct = (ok + fail) * 100 // total
    bar_len = min(pct, 100)
    bar = '#' * bar_len + '.' * (100 - bar_len)
    total_done = max(ok + fail, 1)
    rate = total_done / max(elapsed, 0.01)
    remaining = total - total_done
    eta = remaining / rate
    text = f'[{"progress"}] {pct}% ok={ok} fail={fail} eta={int(eta//60)}m{int(eta%60)}s'
    with open(os.path.join(TMP_DIR, 'progress.txt'), 'w') as f:
        f.write(text)

def save_progress_raw(ok, fail, total, elapsed):
    # Simpler version without division issues
    total_done = max(ok + fail, 1)
    pct = total_done * 100 // total
    remaining = total - total_done
    eta_min = int(remaining * elapsed / max(total_done, 1) / 60)
    text = f'[{"progress"}] {pct}% ok={ok} fail={fail} eta={eta_min}m'
    with open(os.path.join(TMP_DIR, 'progress.txt'), 'w') as f:
        f.write(text)

# Load missing codes
with open('D:/temp/deities_missing.json', 'r', encoding='utf-8') as f:
    missing_entries = json.load(f)

total = len(missing_entries)
print(f'Target: {total} images', flush=True)
print(f'Temp: {TMP_DIR}', flush=True)

ancient = 'Ancient%20Chinese%20mythology%20divine%20deity%20portrait%2C%20majestic%20transcendent%20immortal%20sage%20with%20jade%20imperial%20headdress%2C%20flowing%20silk%20ceremonial%20robes%2C%20ethereal%20clouds%20background%2C%20traditional%20Eastern%20masterpiece%20painting'
future = 'Futuristic%20cosmic%20deity%20avatar%2C%20humanoid%20being%20in%20shimmering%20iridescent%20quantum%20armor%20with%20holographic%20energy%20shields%2C%20hovering%20anti-gravity%20disc%20platform%2C%20floating%20sacred%20geometries%20and%20Platonic%20solids%2C%20sleek%20UFO%20mothership%20silhouettes%20in%20nebula%20sky%2C%20bioluminescent%20energy%20crystals%20orbiting%2C%20cinematic%20composition%2C%20photorealistic%20digital%20painting'

ok = 0
fail = 0
failed_codes = []
start = time.time()

# Start progress reporter
pr = threading.Thread(target=progress_reporter, daemon=True)
pr.start()

for idx, entry in enumerate(missing_entries):
    code = entry['code']
    freq = entry['freq']
    style = future if freq < 5 else ancient
    seed = random.randint(1, 999999)
    ts = str(int(time.time() * 1000) + random.randint(10000, 99999))
    filename = 'code_' + code + '_' + ts + '.jpg'
    filepath = os.path.join(TMP_DIR, filename)
    
    # Clean URL - build it properly
    base_prompt = style
    params = f'?width=1024&height=1024&seed={seed}&model=flux'
    url = 'https://image.pollinations.ai/prompt/' + base_prompt + params
    
    success = False
    for attempt in range(2):
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
                print(f'  Err: {err_msg}', flush=True)
        
        if not success and attempt < 1:
            wait = 2 + (attempt + 1) * 2
            print(f'  Retry {attempt+1}/{2} for {code} in {wait}s...', flush=True)
            time.sleep(wait)
    
    elapsed_now = time.time() - start
    save_progress_raw(ok, fail, total, elapsed_now)
    
    if success:
        ok += 1
    else:
        fail += 1
        failed_codes.append(code)
    
    if (idx + 1) % 10 == 0 or idx + 1 == total:
        elapsed = time.time() - start
        pct = (idx + 1) * 100 // total
        bar_len = min(pct, 100)
        bar = '#' * bar_len + '.' * (100 - bar_len)
        rate = (idx + 1) / max(elapsed, 0.01)
        remaining = total - (idx + 1)
        eta = remaining / rate
        print(f'[{bar}] {pct}% ok={ok} fail={fail} eta={int(eta//60)}m{int(eta%60)}s', flush=True)
    
    # Small breathing room between requests
    time.sleep(0.3)

# Signal progress reporter to stop
stop_event.set()

# Move success files to output_dir
copied = 0
for fn in os.listdir(TMP_DIR):
    src = os.path.join(TMP_DIR, fn)
    dst = os.path.join(OUTPUT_DIR, fn)
    if not os.path.exists(dst):
        try:
            shutil.move(src, dst)
            copied += 1
        except Exception as e:
            print(f'Move error {fn}: {e}', flush=True)

elapsed = time.time() - start
print(f'\n=== DONE in {elapsed/60:.1f}m ===', flush=True)
print(f'OK: {ok} | Fail: {fail} | Copied: {copied}', flush=True)
print(f'Failed codes: {failed_codes[:30]}', flush=True)

# Save failed codes for next round
with open('D:/temp/deities_failed_final.json', 'w', encoding='utf-8') as f:
    json.dump({'failed': failed_codes, 'ok': ok, 'fail': fail, 'total': total}, f, indent=2)
print(f'Saved to D:/temp/deities_failed_final.json', flush=True)

# Cleanup temp
try:
    shutil.rmtree(TMP_DIR)
except:
    pass
