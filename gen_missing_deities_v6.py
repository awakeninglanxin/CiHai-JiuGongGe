import os, re, json, time, random, requests, shutil, tempfile, threading

OUTPUT_DIR = r'D:\AAA我的文件\慈海九宫格_整合版\generated-images'
TMP_DIR = tempfile.mkdtemp(prefix='deities_v6_')

# Load all missing codes
with open('D:/temp/deities_missing.json', 'r', encoding='utf-8') as f:
    all_missing = json.load(f)
missing_codes = set(e['code'] for e in all_missing)

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

# Find the last 14 codes that still need generation
last_14 = [e for e in all_missing if e['code'] not in existing_codes]
print(f"Last 14 codes to generate: {len(last_14)}")
for e in last_14:
    print(f"  {e['code']} (freq={e['freq']})")

if not last_14:
    print("All codes already generated!")
    exit(0)

# Prompt templates
ancient = 'Ancient%20Chinese%20mythology%20divine%20deity%20portrait%2C%20majestic%20transcendent%20immortal%20sage%20with%20jade%20imperial%20headdress%2C%20flowing%20silk%20ceremonial%20robes%2C%20ethereal%20clouds%20background%2C%20traditional%20Eastern%20masterpiece%20painting'
future = 'Futuristic%20cosmic%20deity%20avatar%2C%20humanoid%20being%20in%20shimmering%20iridescent%20quantum%20armor%20with%20holographic%20energy%20shields%2C%20hovering%20anti-gravity%20disc%20platform%2C%20floating%20sacred%20geometries%20and%20Platonic%20solids%2C%20sleek%20UFO%20mothership%20silhouettes%20in%20nebula%20sky%2C%20bioluminescent%20energy%20crystals%20orbiting%2C%20cinematic%20composition%2C%20photorealistic%20digital%20painting'

ok = 0
fail = 0
failed_codes = []
start = time.time()

for idx, entry in enumerate(last_14):
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
    for attempt in range(5):
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
        
        if not success and attempt < 4:
            wait = 5 + (attempt + 1) * 3
            print(f'  Retry {attempt+1}/5 for {code} in {wait}s...', flush=True)
            time.sleep(wait)
    
    elapsed_now = time.time() - start
    if success:
        ok += 1
    else:
        fail += 1
        failed_codes.append(code)
    
    pct = (idx + 1) * 100 // len(last_14)
    print(f'[{pct}%] item={idx+1}/{len(last_14)} ok={ok} fail={fail} code={code}', flush=True)
    
    time.sleep(1)

# Copy success files to OUTPUT_DIR using shutil.copy2
copied = 0
for fn in os.listdir(TMP_DIR):
    src = os.path.join(TMP_DIR, fn)
    dst = os.path.join(OUTPUT_DIR, fn)
    if os.path.exists(dst):
        continue
    try:
        shutil.copy2(src, dst)
        copied += 1
    except Exception as e:
        print(f'Copy error {fn}: {e}', flush=True)

elapsed = time.time() - start
print(f'\n=== DONE in {elapsed:.1f}s ===', flush=True)
print(f'OK: {ok} | Fail: {fail} | Total attempted: {ok+fail}', flush=True)
print(f'Copied: {copied}', flush=True)
if failed_codes:
    print(f'Failed codes: {failed_codes}', flush=True)

# Cleanup temp
try:
    shutil.rmtree(TMP_DIR)
except:
    pass

# Final count
total_files = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.jpg') and os.path.getsize(os.path.join(OUTPUT_DIR, f)) >= 50000])
print(f"\nFinal count in {OUTPUT_DIR}: {total_files}", flush=True)
