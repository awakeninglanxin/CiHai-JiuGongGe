import os
import re
import json
import time
import random
import requests
import shutil
import tempfile

output_dir = r'D:/AAA我的文件/慈海九宫格_整合版/generated-images'
tmp_dir = tempfile.mkdtemp(prefix='deities_gen_')
print(f'Temp dir: {tmp_dir}', flush=True)

# Load missing codes
with open('D:/temp/deities_missing.json', 'r', encoding='utf-8') as f:
    missing_entries = json.load(f)

total = len(missing_entries)
print(f'To generate: {total}', flush=True)

ancient = 'Ancient%20Chinese%20mythology%20divine%20deity%20portrait%2C%20majestic%20transcendent%20immortal%20sage%20with%20jade%20imperial%20headdress%2C%20flowing%20silk%20ceremonial%20robes%2C%20ethereal%20clouds%20background%2C%20traditional%20Eastern%20masterpiece%20painting'
future = 'Futuristic%20cosmic%20deity%20avatar%2C%20humanoid%20being%20in%20shimmering%20iridescent%20quantum%20armor%20with%20holographic%20energy%20shields%2C%20hovering%20anti-gravity%20disc%20platform%2C%20floating%20sacred%20geometries%20and%20Platonic%20solids%2C%20sleek%20UFO%20mothership%20silhouettes%20in%20nebula%20sky%2C%20bioluminescent%20energy%20crystals%20orbiting%2C%20cinematic%20composition%2C%20photorealistic%20digital%20painting'

ok = 0
fail = 0
failed_codes = []

start = time.time()

for idx, entry in enumerate(missing_entries):
    code = entry['code']
    freq = entry['freq']
    style = future if freq < 5 else ancient
    seed = random.randint(1, 999999)
    ts = str(int(time.time() * 1000) + random.randint(10000, 99999))
    filename = 'code_' + code + '_' + ts + '.jpg'
    filepath = os.path.join(tmp_dir, filename)
    url = 'https://image.pollinations.ai/prompt/' + style + '?width=1024&height=1024&seed=' + str(seed) + '&model=flux'
    
    success = False
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=600, stream=True, proxies=None)
            if resp.status_code == 200:
                with open(filepath, 'wb') as out:
                    for chunk in resp.iter_content(8192):
                        out.write(chunk)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
                    success = True
                    break
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception as e:
            print(f'Error for {code}: {e}', flush=True)
        if not success and attempt < 1:
            time.sleep(2)
    
    if success:
        ok += 1
    else:
        fail += 1
        failed_codes.append(code)
    
    if (idx + 1) % 30 == 0 or idx + 1 == total:
        elapsed = time.time() - start
        pct = (idx + 1) * 100 // total
        bar_len = min(pct, 100)
        bar = '#' * bar_len + '.' * (100 - bar_len)
        rate = (idx + 1) / max(elapsed, 0.1)
        remaining = total - (idx + 1)
        eta = remaining / rate
        print(f'[{bar}] {pct}% ok={ok} fail={fail} eta={int(eta//60)}m{int(eta%60)}s', flush=True)
    time.sleep(0.3)

# Move success files to output_dir
copied = 0
for fn in os.listdir(tmp_dir):
    src = os.path.join(tmp_dir, fn)
    dst = os.path.join(output_dir, fn)
    if not os.path.exists(dst):
        shutil.move(src, dst)
        copied += 1

elapsed = time.time() - start
print(f'\n=== DONE in {elapsed/60:.1f}m ===', flush=True)
print(f'OK: {ok} | Fail: {fail} | Copied: {copied}', flush=True)

# Save failed codes for next round
with open('D:/temp/deities_failed.json', 'w', encoding='utf-8') as f:
    json.dump({'failed': failed_codes, 'ok': ok, 'fail': fail, 'total': total}, f, indent=2)
print('Saved failed codes to D:/temp/deities_failed.json', flush=True)

# Cleanup temp
try:
    shutil.rmtree(tmp_dir)
except:
    pass
