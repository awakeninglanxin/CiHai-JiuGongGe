"""
慈海九宫格 - v15 新时代童子画风版
专门用于替代以0开头的先天童子类型（原来为老头道士形象）
新风格：空灵发光的小天使/光之守护者/新纪元艺术风格
单线程、断点续传、429智能退避、自动更新deities.js
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v15_done.txt')

# ============================================================
# 新时代童子画风 - 基于参考图片的风格定义
# 特征：小天使/光之守护者儿童形象、空灵发光、粉彩梦幻、宇宙星云背景
# ============================================================

# 共享的儿童/童子特征
CHILD_FEATURES = [
    "adorable young child boy, luminous glowing white hair, big innocent luminous blue eyes, chubby cheeks, soft radiant smile, ethereal innocence, youthful divine purity, childlike wonder",
    "cute young celestial child girl, flowing silver-white hair with starlight shimmer, large luminous violet eyes, gentle loving expression, youthful ethereal grace, sweet innocent smile, angelic beauty",
    "young radiant angel child, short fluffy luminous hair glowing softly, wide curious sparkling eyes, adorable cherubic face, youthful joyful expression, divine child energy, pure innocence radiance",
    "lovely youthful deity child, bright luminous golden-white hair, big luminous azure eyes, sweet innocent expression, delicate features of a precious child, ethereal charm, radiant youthful divinity",
    "precious young angelic child, soft flowing white hair with rainbow iridescence, luminous jewel-toned eyes (blue/green/purple), cherubic rosy-cheeked face, gentle peaceful expression, youthful divine radiance",
]

# 共享的翅膀/光晕
ACCESSORIES_OPTIONS = [
    "small translucent iridescent fairy wings folded gently, delicate glowing light halo above head",
    "subtle golden divine aura surrounding entire body, soft luminous particle sparkles floating around",
    "glowing star-shaped birthmark on forehead, ethereal light tendrils flowing from hands",
    "small crystalline butterfly wings, gentle luminescent glow emanating from chest area",
    "translucent dove wings, warm golden divine light wrapping around small form",
    "no wings, just soft luminous body aura and floating golden sparkles around",
    "delicate iridescent dragonfly wings, rainbow light halo orbiting above head",
    "subtle golden energy wings formed by light particles, glowing om symbol on forehead",
]

# 共享的服装
CLOTHING_OPTIONS = [
    "wearing simple luminous white silk robe flowing loosely, delicate golden thread trim, barefoot",
    "draped in soft pastel pink and lavender flowing tunic with ethereal silk ribbons, barefoot",
    "wearing cloud-white sleeveless tunic with celestial star patterns woven in gold thread",
    "clothed in luminous pale gold robe with gentle iridescent shimmer, simple pearl cord belt",
    "wearing layered translucent ethereal robes in pearl white and soft lilac, starlight embroidered",
    "draped in simple luminous white sheet-like garment wrapped elegantly, barefoot on clouds",
    "wearing celestial baby blue robe with golden lotus patterns and flowing silk sash",
    "clothed in soft cream-colored flowing tunic with rainbow iridescent shimmer, gentle pearl necklace",
]

# 共享的背景
BACKGROUND_OPTIONS = [
    "dreamy cosmic space background with swirling nebula in pastel pink purple and blue, distant glowing planets and shooting stars, infinite universe feeling",
    "ethereal cloud kingdom floating above earth at golden hour, pastel clouds glowing warm pink and lavender, magical floating crystal towers in distance",
    "celestial starfield with rainbow light beams, galaxies of pink and purple swirling around, shooting stars and twinkling constellations",
    "floating island paradise in the clouds, pastel sunset sky with golden light rays, enchanted garden with luminous flowers and crystal streams",
    "cosmic egg of creation with rainbow aura, golden light spiraling upward into infinity, ethereal energy vortex surrounding everything",
    "pastel aurora borealis sky with rainbow light ribbons dancing, stars and planets visible, divine feminine energy flowing",
    "enchanted forest at dawn with glowing fireflies and rainbow mist, crystalline waterfall, ancient luminous trees with golden leaves",
    "heavenly palace of light with rainbow crystal archways, floating gardens, golden sunset radiance, angelic cityscape in clouds",
]

# 共享的姿势
POSES = [
    "reaching small hands outward invitingly, holding a glowing heart-shaped orb of light in palms",
    "sitting cross-legged in meditation pose on floating luminous lotus flower, hands in child dhyana mudra",
    "standing gracefully on rainbow light bridge, arms spread wide embracing all beings with love",
    "floating peacefully among clouds with closed eyes and gentle smile, tiny rainbow halo above head",
    "holding a glowing crystal lotus bloom in one hand, other hand making blessing gesture",
    "crouching gently observing a tiny glowing planet in cupped hands with wide wonder-eyed curiosity",
    "reclining on a fluffy pink cloud, one arm raised holding a star, peaceful meditative expression",
    "standing with back to viewer looking at a magnificent cosmic sunrise, arms slightly spread",
]

random.seed(42)

def pick(lst):
    return random.choice(lst)

def build_prompt(code, idx):
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    
    child = CHILD_FEATURES[code_hash % len(CHILD_FEATURES)]
    accessory = ACCESSORIES_OPTIONS[code_hash % len(ACCESSORIES_OPTIONS)]
    clothing = CLOTHING_OPTIONS[code_hash % len(CLOTHING_OPTIONS)]
    bg = BACKGROUND_OPTIONS[code_hash % len(BACKGROUND_OPTIONS)]
    pose = POSES[code_hash % len(POSES)]
    
    prompt = (f"portrait of a {child}, {accessory}, {clothing}, {pose}, {bg}, "
              f"masterpiece, best quality, 8k ultra detailed, "
              f"New Age art style, ethereal sacred geometry aesthetic, "
              f"Luminous pastel color palette, divine feminine energy, "
              f"gloating particles floating gently, "
              f"soft romantic volumetric lighting, subsurface scattering on skin, "
              f"dreamy atmospheric perspective, magical fantasy illustration, "
              f"trending on ArtStation, spiritual awakening theme, "
              f"pure innocent divine child energy, transcendent beauty")
    
    seed = int(code_hash)
    return prompt, seed

def generate_one(code, prompt, seed):
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=1024&seed={seed}&model=flux&nologo=true"
    
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200 and len(resp.content) > 50000:
                with open(os.path.join(IMG_DIR, f'code_{code}.jpg'), 'wb') as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f'  ⏳ 429限速, 等{wait}秒...', flush=True)
                time.sleep(wait)
            else:
                time.sleep(5 + attempt * 3)
        except Exception as e:
            time.sleep(5 + attempt * 3)
    return False

# === 断点恢复 ===
done_set = set()
if os.path.exists(DONE_LOG):
    with open(DONE_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^(\d+)$', line.strip())
            if m:
                done_set.add(m.group(1))

# 扫描实际已有图片（只在generated-images中找0开头的）
existing = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        code_val = m.group(1)
        if code_val.startswith('0'):
            existing.add(code_val)

with open(DEITIES_FILE, encoding='utf-8') as f:
    js = f.read()
all_codes = sorted(set(re.findall(r'code:\s*"(\d+)"', js)))

# 只处理0开头的code
zero_codes = [c for c in all_codes if c.startswith('0')]
complete = existing | done_set
need = [c for c in zero_codes if c not in complete]

print("=" * 70)
print("慈海九宫格 v15 - 新时代童子画风版 (空灵发光小天使/光之守护者)")
print(f"0开头codes总数: {len(zero_codes)} | 已完成: {len(complete & set(zero_codes))} | 需生成: {len(need)}")
print("风格: 新纪元艺术、空灵发光、粉彩梦幻、宇宙星云背景、可爱童子形象")
print("=" * 70)

success = 0
fail = 0
start = time.time()

with open(DONE_LOG, 'a', encoding='utf-8') as log_f:
    for i, code in enumerate(need):
        elapsed = time.time() - start
        rate = (i + 1) / max(elapsed, 0.1)
        remain_sec = (len(need) - i - 1) / max(rate, 0.01)
        
        print(f'[{i+1}/{len(need)}] code={code} | {remain_sec/60:.0f}min剩余', flush=True)
        
        prompt, seed = build_prompt(code, i)
        ok = generate_one(code, prompt, seed)
        
        if ok:
            success += 1
            log_f.write(f'{code}\n')
            log_f.flush()
            print(f'  ✓ done', flush=True)
        else:
            fail += 1
            print(f'  ✗ FAILED', flush=True)
        
        time.sleep(1.5)

total = time.time() - start
print(f"\n生成完成: 成功{success} 失败{fail} 耗时{total/60:.1f}分钟")

# 更新deities.js
print("更新 deities.js...", flush=True)
with open(DEITIES_FILE, encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
changed = 0
new_lines = []
for line in lines:
    cm = re.search(r'code:\s*"(\d+)"', line)
    im = re.search(r'image:\s*"([^"]*)"', line)
    if cm and im:
        c = cm.group(1)
        if not c.startswith('0'):
            new_lines.append(line)
            continue
        old = im.group(1)
        new = f'generated-images/code_{c}.jpg'
        if os.path.exists(os.path.join(IMG_DIR, f'code_{c}.jpg')) and old != new:
            new_lines.append(line.replace(old, new))
            changed += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

shutil.copy2(DEITIES_FILE, DEITIES_FILE + '.bak_v15')
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新", flush=True)

# 最终统计
final_zero_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(0\d+)\.jpg$', f)
    if m:
        final_zero_codes.add(m.group(1))
matching = len(final_zero_codes)
missing = len(zero_codes) - matching
print(f"\n=== 童子版最终: {matching}/{len(zero_codes)} | 缺失: {missing} ===", flush=True)
