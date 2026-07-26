"""
慈海九宫格 - v15-REGEN 问题童子增强重生成
专门针对质量扫描发现的205张有问题的童子图进行重新生成
增强的prompt确保: 睁眼、对称翅膀、清晰五官
单线程、429智能退避、自动更新deities.js
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v15_regen_done.txt')

# ============================================================
# 增强的童子特征 - 明确强调睁眼、清晰瞳孔
# ============================================================
CHILD_FEATURES = [
    "adorable young child boy, luminous glowing white hair, OPEN BIG INNOCENT LUMINOUS BLUE EYES with clearly visible pupils and iris, distinct eye whites, chubby cheeks, soft radiant smile, ethereal innocence, sharp facial features, detailed face",
    "cute young celestial child girl, flowing silver-white hair with starlight shimmer, OPEN LARGE LUMINOUS VIOLET EYES with clearly defined pupils, sharp focused gaze, gentle loving expression, sweet innocent smile, angelic beauty",
    "young radiant angel child, short fluffy luminous hair glowing softly, OPEN WIDE CURIOUS SPARKLING EYES with bright catchlights in pupils, adorable cherubic face, youthful joyful expression, detailed facial features",
    "lovely youthful deity child, bright luminous golden-white hair, OPEN BIG LUMINOUS AZURE EYES with distinct pupil and iris, sweet innocent expression, sharply detailed delicate features, ethereal charm",
    "precious young angelic child, soft flowing white hair with rainbow iridescence, OPEN LUMINOUS JEWEL-TONED EYES with clearly visible pupils and bright highlights (blue/green/purple), cherubic rosy-cheeked face with detailed features",
]

# 增强的翅膀 - 强调对称
ACCESSORIES_OPTIONS = [
    "two perfectly symmetrical complete translucent iridescent fairy wings extending outward, delicate glowing light halo above head",
    "subtle golden divine aura surrounding entire body, soft luminous particle sparkles floating around",
    "glowing star-shaped birthmark on forehead, ethereal light tendrils flowing symmetrically from hands",
    "two symmetrical delicate translucent crystal butterfly wings, gentle luminescent glow emanating from chest",
    "two perfectly balanced translucent dove wings extending symmetrically, warm golden divine light",
    "no wings, symmetrical soft luminous body aura and floating golden sparkles around both sides equally",
    "two symmetrical delicate iridescent dragonfly wings extending outward evenly, rainbow light halo",
    "symmetrical subtle golden energy wings formed by light particles on both sides",
]

# 服装
CLOTHING_OPTIONS = [
    "wearing simple luminous white silk robe flowing loosely with delicate golden thread trim, symmetrical draping, barefoot",
    "draped in soft pastel pink and lavender flowing tunic with ethereal silk ribbons, symmetrical arrangement, barefoot",
    "wearing cloud-white sleeveless tunic with celestial star patterns woven in gold thread, balanced fit",
    "clothed in luminous pale gold robe with gentle iridescent shimmer, simple centered pearl cord belt",
    "wearing layered translucent ethereal robes in pearl white and soft lilac, starlight embroidered, symmetrical",
    "draped in simple luminous white sheet-like garment wrapped elegantly, barefoot on clouds",
    "wearing celestial baby blue robe with golden lotus patterns and flowing silk sash, symmetrically draped",
    "clothed in soft cream-colored flowing tunic with rainbow iridescent shimmer, gentle centered pearl necklace",
]

# 背景
BACKGROUND_OPTIONS = [
    "dreamy cosmic space background with swirling nebula in pastel pink purple and blue, distant glowing planets and shooting stars",
    "ethereal cloud kingdom floating above earth at golden hour, pastel clouds glowing warm pink and lavender",
    "celestial starfield with rainbow light beams, galaxies of pink and purple swirling around, twinkling constellations",
    "floating island paradise in the clouds, pastel sunset sky with golden light rays, enchanted garden with luminous flowers",
    "cosmic egg of creation with rainbow aura, golden light spiraling upward into infinity",
    "pastel aurora borealis sky with rainbow light ribbons dancing, stars and planets visible",
    "enchanted forest at dawn with glowing fireflies and rainbow mist, crystalline waterfall",
    "heavenly palace of light with rainbow crystal archways, floating gardens, golden sunset radiance",
]

# 姿势 - 正面或半侧面, 不遮脸
POSES = [
    "facing forward, standing gracefully, reaching small hands outward invitingly, holding a glowing heart-shaped orb of light",
    "sitting upright cross-legged facing forward on floating luminous lotus flower, hands in child dhyana mudra, clear eyes visible",
    "standing facing forward on rainbow light bridge, arms spread wide symmetrically",
    "sitting peacefully facing forward among clouds with gentle open smile and clear visible eyes",
    "standing facing forward holding a glowing crystal lotus bloom in right hand, other hand making blessing gesture",
    "standing facing forward with gentle curiosity, hands cupped together holding a tiny glowing star",
    "sitting on a fluffy pink cloud facing forward, one arm raised holding a star, peaceful gentle smile",
    "standing facing viewer with arms slightly spread, radiant joyful expression",
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
              f"masterpiece, best quality, 8k ultra detailed, sharp focus, crystal clear, "
              f"New Age art style, ethereal sacred geometry aesthetic, "
              f"Luminous pastel color palette, divine feminine energy, "
              f"floating particles gently, "
              f"soft romantic volumetric lighting, subsurface scattering on skin, "
              f"dreamy atmospheric perspective, magical fantasy illustration, "
              f"trending on ArtStation, spiritual awakening theme, "
              f"pure innocent divine child energy, transcendent beauty, "
              f"clear detailed eyes, distinct pupils and iris, OPEN BRIGHT EYES, "
              f"symmetrical composition, well-defined face, sharp facial features, "
              f"high contrast eyes, visible eyelashes, bright eye catchlights, "
              f"perfect symmetry, balanced proportions")
    
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

# === 读取需要重生成的codes ===
regen_file = os.path.join(PROJECT, 'regen_v15_codes.txt')
regen_codes = []
if os.path.exists(regen_file):
    with open(regen_file, 'r', encoding='utf-8') as f:
        for line in f:
            code = line.strip()
            if code:
                regen_codes.append(code)
else:
    print(f"错误: 找不到 {regen_file}")
    sys.exit(1)

# === 断点恢复 ===
done_set = set()
if os.path.exists(DONE_LOG):
    with open(DONE_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^(\d+)$', line.strip())
            if m:
                done_set.add(m.group(1))

need = [c for c in regen_codes if c not in done_set]

print("=" * 70)
print("慈海九宫格 v15-REGEN - 问题童子增强重生成版")
print(f"待重生成: {len(need)} / {len(regen_codes)}")
print(f"增强提示词: 明确强调 OPEN BRIGHT EYES, sharp focus, symmetrical")
print("=" * 70)

success = 0
fail = 0
start = time.time()

with open(DONE_LOG, 'a', encoding='utf-8') as log_f:
    for i, code in enumerate(need):
        elapsed = time.time() - start
        rate = (i + 1) / max(elapsed, 0.1)
        remain_sec = (len(need) - i - 1) / max(rate, 0.01)
        
        print(f'[{i+1}/{len(need)}] code={code} | ~{remain_sec/60:.0f}min剩余', flush=True)
        
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
print(f"\n重生成完成: 成功{success} 失败{fail} 耗时{total/60:.1f}分钟")

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

shutil.copy2(DEITIES_FILE, DEITIES_FILE + '.bak_regen')
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新", flush=True)

# 最终验证
final_zero_codes = set()
for fn in os.listdir(IMG_DIR):
    m = re.match(r'^code_(0\d+)\.jpg$', fn)
    if m:
        final_zero_codes.add(m.group(1))
print(f"\n=== 童子版最终: {len(final_zero_codes)}/317 | 缺失: {317-len(final_zero_codes)} ===", flush=True)
