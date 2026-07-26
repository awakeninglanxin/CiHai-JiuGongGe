"""
慈海九宫格 - v15-REGEN 问题童子重生成
专门重新生成质量检查中发现问题的童子图
包含: blur(模糊), half_closed(半闭眼), wing_asym(翅膀不对称)
单线程、断点续传、429智能退避、自动更新deities.js
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v15_regen_done.txt')

# 增强的童子特征 - 确保睁眼、清晰五官、对称翅膀
CHILD_FEATURES = [
    # 睁眼版本 - 强调清晰的眼睛
    "adorable young child boy, luminous glowing white hair, OPEN big innocent luminous blue eyes clearly visible with distinct pupils and whites, chubby cheeks, soft radiant smile, ethereal innocence, youthful divine purity, detailed face, sharp facial features",
    "cute young celestial child girl, flowing silver-white hair with starlight shimmer, OPEN large luminous violet eyes clearly defined with visible iris and pupil, gentle loving expression, youthful ethereal grace, sweet innocent smile, angelic beauty, sharp focused eyes",
    "young radiant angel child, short fluffy luminous hair glowing softly, OPEN wide curious sparkling luminous eyes with clear pupils, adorable cherubic face with detailed features, youthful joyful expression, divine child energy, pure innocence radiance",
    "lovely youthful deity child, bright luminous golden-white hair, OPEN big luminous azure eyes with distinct pupil and iris, sweet innocent expression, sharply detailed delicate features of a precious child, ethereal charm, radiant youthful divinity",
    "precious young angelic child, soft flowing white hair with rainbow iridescence, OPEN luminous jewel-toned eyes with clearly visible pupils and bright catchlights (blue/green/purple), cherubic rosy-cheeked face with detailed features, gentle peaceful expression, youthful divine radiance",
]

# 增强的翅膀 - 强调对称完整
ACCESSORIES_OPTIONS = [
    "two symmetrical complete translucent iridescent fairy wings, perfectly balanced left and right, delicate glowing light halo above head",
    "subtle golden divine aura surrounding entire body symmetrically, soft luminous particle sparkles floating around both sides equally",
    "glowing star-shaped birthmark on forehead, ethereal light tendrils flowing from both hands symmetrically",
    "two symmetrical complete translucent crystalline butterfly wings, perfectly mirrored left and right, gentle luminescent glow emanating from chest area",
    "two symmetrical complete translucent dove wings, perfectly balanced extending outward, warm golden divine light wrapping around small form",
    "no wings, just symmetrical soft luminous body aura and floating golden sparkles around both sides equally",
    "two symmetrical complete delicate iridescent dragonfly wings, perfectly balanced left and right, rainbow light halo orbiting above head",
    "two symmetrical complete subtle golden energy wings formed by light particles, perfectly mirrored, glowing om symbol centered on forehead",
]

# 增强的服装
CLOTHING_OPTIONS = [
    "wearing simple luminous white silk robe flowing loosely, delicate golden thread trim, symmetrically draped, barefoot",
    "draped in soft pastel pink and lavender flowing tunic with ethereal silk ribbons, symmetrically arranged, barefoot",
    "wearing cloud-white sleeveless tunic with celestial star patterns woven in gold thread, symmetrically fitted",
    "clothed in luminous pale gold robe with gentle iridescent shimmer, simple centered pearl cord belt, symmetrical draping",
    "wearing layered translucent ethereal robes in pearl white and soft lilac, starlight embroidered, balanced on both sides",
    "draped in simple luminous white sheet-like garment wrapped elegantly and symmetrically, barefoot on clouds",
    "wearing celestial baby blue robe with golden lotus patterns and flowing silk sash, symmetrically arranged",
    "clothed in soft cream-colored flowing tunic with rainbow iridescent shimmer, gentle centered pearl necklace",
]

# 增强的姿势 - 避免遮脸
POSES = [
    "standing facing forward, reaching small hands outward invitingly symmetrically, holding a glowing heart-shaped orb of light in palms",
    "sitting upright cross-legged in meditation pose on floating luminous lotus flower facing forward, hands in child dhyana mudra, eyes clearly visible",
    "standing gracefully facing forward on rainbow light bridge, arms spread wide symmetrically embracing all beings with love",
    "sitting peacefully facing forward among clouds with gentle open smile, tiny rainbow halo above head, clear visible eyes",
    "standing facing forward holding a glowing crystal lotus bloom in right hand, other hand making blessing gesture",
    "standing facing forward with gentle curiosity, hands cupped together holding a tiny glowing star",
    "sitting on a fluffy pink cloud facing forward, one arm raised holding a star above head, peaceful gentle smile visible",
    "standing facing away from viewer looking at a magnificent cosmic sunrise, arms slightly spread symmetrically",
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
    
    # 添加负面提示来强化清晰度
    prompt = (f"portrait of a {child}, {accessory}, {clothing}, {pose}, {bg}, "
              f"masterpiece, best quality, 8k ultra detailed, sharp focus, "
              f"New Age art style, ethereal sacred geometry aesthetic, "
              f"Luminous pastel color palette, divine feminine energy, "
              f"floating particles floating gently, "
              f"soft romantic volumetric lighting, subsurface scattering on skin, "
              f"dreamy atmospheric perspective, magical fantasy illustration, "
              f"trending on ArtStation, spiritual awakening theme, "
              f"pure innocent divine child energy, transcendent beauty, "
              f"clear detailed eyes, distinct pupils and iris, open eyes, symmetrical composition, sharp facial features, well-defined anatomy")
    
    seed = int(code_hash)
    return prompt, seed

# 共享的背景 (保持原样)
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

# 删除 v15_regen_done.txt 重新开始(因为它是上次运行的日志)
regen_done = os.path.join(PROJECT, 'v15_regen_done.txt')
if os.path.exists(regen_done):
    os.remove(regen_done)
print(f"已清空断点日志, 准备重新生成")

# 检查哪些已经有图片
existing = set()
for fn in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', fn)
    if m and m.group(1).startswith('0'):
        existing.add(m.group(1))

# 即使已有图片也强制覆盖(因为需要新的enhanced prompt)
need = [c for c in regen_codes if c not in done_set]

# Dry-run: show stats
print("=" * 70)
print("慈海九宫格 v15-REGEN - 问题童子增强重生成版")
print(f"待重生成: {len(need)} (原问题童子共 {len(regen_codes)} 张, 已完成 {len(done_set)} 张)")
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
