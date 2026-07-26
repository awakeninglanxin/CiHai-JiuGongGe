"""
慈海九宫格 - v16 ALL-REGEN 全量重生成版
覆盖全部593张有问题的童子/长者图（含eye_asymmetry、blur、overexposed三类）

核心修复：
1. 面部对称性 - 左右脸亮度一致，双眼对称睁开/闭合
2. 五官清晰 - 尖锐焦点，清晰瞳孔/虹膜
3. 肢体完整 - 两只手臂、完整翅膀/光环、双脚
4. 风格一致 - 保留原版色调和构图风格

童子（0开头）：用童子版prompt
长者（1-9开头）：用长者/仙人版prompt

断点恢复、429限速退避、自动更新deities.js
"""
import os, sys, time, random, hashlib, re, shutil, requests

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
DONE_LOG = os.path.join(PROJECT, 'v16_all_regen_done.txt')

# ============================================================
# 童子版特征 - 保持v15增强版
# ============================================================
CHILD_FEATURES = [
    "adorable young child boy, luminous glowing white hair, OPEN BOTH EYES EQUALLY, clearly visible pupils and iris in both eyes, distinct eye whites, chubby cheeks, soft radiant smile, ethereal innocence, sharp facial features, symmetrical face",
    "cute young celestial child girl, flowing silver-white hair with starlight shimmer, OPEN BOTH EYES EQUAL SIZE, clearly defined pupils symmetrically, sharp focused gaze, gentle loving expression, sweet innocent smile, angelic beauty",
    "young radiant angel child, short fluffy luminous hair glowing softly, OPEN BOTH EYES IDENTICAL with bright catchlights in pupils symmetrically, adorable cherubic face, youthful joyful expression, detailed facial features",
    "lovely youthful deity child, bright luminous golden-white hair, OPEN BOTH EYES SAME SIZE with distinct pupils and iris symmetrically, sweet innocent expression, sharply detailed delicate features, symmetrical face",
    "precious young angelic child, soft flowing white hair with rainbow iridescence, OPEN BOTH EYES CLEARLY VISIBLE pupils symmetrically with bright highlights (blue/green/purple), cherubic rosy-cheeked face, detailed symmetric facial features",
]

CHILD_ACCESSORIES = [
    "two perfectly symmetrical complete translucent iridescent fairy wings, equal length and shape on both sides, delicate glowing light halo above head",
    "subtle golden divine aura surrounding entire body evenly, soft luminous particle sparkles floating around symmetrically",
    "glowing star-shaped birthmark on forehead center, ethereal light tendrils flowing symmetrically from both hands equally",
    "two symmetrical delicate translucent crystal butterfly wings, equal size and shape on both sides of body",
    "two perfectly balanced translucent dove wings extending symmetrically left and right, warm golden divine light",
    "symmetrical soft luminous body aura, no wings needed but floating golden sparkles around both sides equally",
    "two symmetrical delicate iridescent dragonfly wings, equal on both sides, rainbow light halo",
    "symmetrical subtle golden energy wings formed by light particles on both sides equally",
]

CHILD_CLOTHING = [
    "wearing simple luminous white silk robe flowing loosely with delicate golden thread trim, symmetrical draping, barefoot",
    "draped in soft pastel pink and lavender flowing tunic with ethereal silk ribbons, symmetrical arrangement, barefoot",
    "wearing cloud-white sleeveless tunic with celestial star patterns woven in gold thread, balanced fit on both sides",
    "clothed in luminous pale gold robe with gentle iridescent shimmer, simple centered pearl cord belt",
    "wearing layered translucent ethereal robes in pearl white and soft lilac, starlight embroidered, symmetrical",
    "draped in simple luminous white sheet-like garment wrapped elegantly, barefoot on clouds",
    "wearing celestial baby blue robe with golden lotus patterns and flowing silk sash, symmetrically draped",
    "clothed in soft cream-colored flowing tunic with rainbow iridescent shimmer, gentle centered pearl necklace",
]

CHILD_POSES = [
    "facing forward, standing gracefully, TWO ARMS reaching outward invitingly symmetrically, both hands holding a glowing heart-shaped orb of light",
    "sitting upright cross-legged facing forward on floating luminous lotus flower, hands in child dhyana mudra on knees, both arms clearly visible",
    "standing facing forward on rainbow light bridge, TWO ARMS spread wide symmetrically, complete body posture",
    "sitting peacefully facing forward among clouds with gentle open smile, both arms resting comfortably",
    "standing facing forward, TWO COMPLETE ARMS visible, right hand holding glowing crystal lotus, left hand making blessing gesture",
    "standing facing forward with gentle curiosity, TWO ARMS visible, hands cupped together holding a tiny glowing star",
    "sitting on a fluffy pink cloud facing forward, TWO ARMS visible, one arm raised holding a star, peaceful gentle smile",
    "standing facing viewer, TWO COMPLETE ARMS slightly spread, radiant joyful expression, symmetrical pose",
]

# ============================================================
# 长者/仙人版特征 - 全新prompt针对老者形象
# 关键：明确说明"open both eyes equally, two arms, complete body"
# ============================================================
ELDER_FEATURES = [
    "wise ancient immortal elder sage, long flowing luminous white beard and hair, OPEN BOTH EYES EQUALLY VISIBLE with clear pupils symmetrically, serene benevolent expression, wrinkled but detailed face, symmetrical facial features, two complete arms visible",
    "venerable celestial master with flowing silver-white beard, OPEN BOTH EYES IDENTICAL with bright catchlights in pupils symmetrically, wise gentle gaze, dignified serene expression, highly detailed facial features, balanced symmetrical composition",
    "noble old deity immortal, magnificent white beard and hair glowing softly, OPEN BOTH EYES CLEARLY with distinct pupils and iris symmetrically, compassionate warm smile, symmetrical aged face with deep wisdom, detailed wrinkles and features",
    "majestic elder celestial being, luminous white flowing beard, OPEN BOTH EYES SAME SIZE with clearly visible pupils in both eyes symmetrically, calm authoritative expression, sharp detailed facial contours, perfect symmetry",
    "ancient heavenly patriarch, ethereal long white beard and hair with rainbow shimmer, OPEN BOTH EYES BRIGHTLY with distinct pupils symmetrically, benevolent loving expression, highly detailed wrinkled wise face, symmetrical composition",
]

ELDER_ACCESSORIES = [
    "two perfectly symmetrical translucent ethereal wings extending evenly from shoulders, equal size and shape, delicate golden divine aura above head",
    "symmetrical golden divine halo and aura surrounding evenly, soft luminous light particles floating around both sides equally, no wings but perfectly balanced energy wings",
    "two symmetrical complete ethereal crystal wings extending outward evenly from back, equal length and breadth, delicate luminous glow",
    "symmetrical subtle golden energy wings formed by light particles on both sides equally, perfect mirror symmetry, divine light halo above head",
    "two perfectly balanced translucent fairy wings, equal on left and right shoulders, warm golden divine light surrounding symmetrically",
]

ELDER_CLOTHING = [
    "wearing flowing luminous ancient sage robe in white and gold with intricate celestial patterns, symmetrical draping, two sleeves visible, barefoot",
    "draped in majestic ethereal imperial robes with golden embroidery, symmetrical arrangement, long flowing sleeves covering two arms visibly",
    "wearing ornate ancient immortal white silk robe with golden thread trim, symmetrical design, both arms covered by sleeves visibly",
    "clothed in luminous pale gold ceremonial robes with gentle iridescent shimmer, balanced fitting, two complete sleeves and arms visible",
    "wearing layered translucent ethereal ancient robes in pearl white and soft jade green, symmetrical draping over two arms",
]

ELDER_POSES = [
    "standing facing forward, TWO COMPLETE ARMS visible symmetrically, hands clasped in blessing gesture, dignified upright posture",
    "sitting upright cross-legged facing forward on floating luminous lotus, hands in meditation mudra on both knees, both arms clearly visible",
    "standing facing forward, TWO ARMS spread slightly outward symmetrically, holding a glowing scepter of divine light in both hands",
    "standing facing forward with serene wisdom, TWO COMPLETE ARMS at sides, symmetrical balanced posture, hands in blessing gesture",
    "sitting peacefully facing forward among clouds, TWO ARMS resting on knees in dhyana mudra, clear both eyes visible",
    "standing facing viewer with arms slightly extended outward symmetrically, holding divine energy orbs in both hands",
]

# 通用增强后缀（童子+长者共用）
ENHANCED_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, crystal clear, "
    "NEW AGE art style, ethereal sacred geometry aesthetic, "
    "Luminous pastel color palette with warm golden tones, "
    "floating luminous particles gently, "
    "soft romantic volumetric lighting, subsurface scattering on skin, "
    "dreamy atmospheric perspective, magical fantasy illustration, "
    "trending on ArtStation, spiritual awakening theme, "
    "OPEN BOTH EYES EQUALLY, clearly visible pupils and iris symmetrically in both eyes, "
    "HIGH CONTRAST EYES, distinct pupils, visible eyelashes, bright eye catchlights, "
    "PERFECT SYMMETRICAL FACE, well-defined facial features, sharp detailed face, "
    "TWO COMPLETE ARMS visible symmetrically, balanced proportions, "
    "PERFECT SYMMETRY, MIRRORED LEFT AND RIGHT, face symmetry, "
    "NO MISSING LIMBS, COMPLETE BODY, balanced composition, "
    "both eyes equally open and visible, symmetrical facial expression"
)

random.seed(42)

def build_elder_prompt(code, idx):
    """为长者/仙人类构建prompt"""
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    
    feature = ELDER_FEATURES[code_hash % len(ELDER_FEATURES)]
    accessory = ELDER_ACCESSORIES[code_hash % len(ELDER_ACCESSORIES)]
    clothing = ELDER_CLOTHING[code_hash % len(ELDER_CLOTHING)]
    pose = ELDER_POSES[code_hash % len(ELDER_POSES)]
    
    prompt = (f"portrait of {feature}, {accessory}, {clothing}, {pose}, {ENHANCED_SUFFIX}")
    seed = int(code_hash)
    return prompt, seed

def build_child_prompt(code, idx):
    """为童子类构建prompt"""
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    
    child = CHILD_FEATURES[code_hash % len(CHILD_FEATURES)]
    accessory = CHILD_ACCESSORIES[code_hash % len(CHILD_ACCESSORIES)]
    clothing = CHILD_CLOTHING[code_hash % len(CHILD_CLOTHING)]
    pose = CHILD_POSES[code_hash % len(CHILD_POSES)]
    
    prompt = (f"portrait of a {child}, {accessory}, {clothing}, {pose}, {ENHANCED_SUFFIX}")
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

# ============================================================
# 读取问题codes（优先童子，再长者）
# ============================================================
regen_files = [
    os.path.join(PROJECT, 'regen_all_zero_codes.txt'),  # 童子
    os.path.join(PROJECT, 'regen_all_nonzero_codes.txt'),  # 长者
]

all_codes = []
for rf in regen_files:
    if os.path.exists(rf):
        with open(rf, 'r', encoding='utf-8') as f:
            for line in f:
                code = line.strip()
                if code:
                    all_codes.append(code)
    else:
        print(f"警告: 找不到 {rf}")

if not all_codes:
    print("错误: 没有发现任何问题codes")
    sys.exit(1)

# === 断点恢复 ===
done_set = set()
if os.path.exists(DONE_LOG):
    with open(DONE_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^(\d+)$', line.strip())
            if m:
                done_set.add(m.group(1))

need = [c for c in all_codes if c not in done_set]

print("=" * 70)
print("慈海九宫格 v16 ALL-REGEN - 全量问题图增强重生成版")
print(f"总问题数: {len(all_codes)}")
print(f"待重生成: {len(need)}")
print(f"修复重点: 双眼对称 + 面部对称 + 肢体完整 + 无断臂残肢")
print("=" * 70)

success = 0
fail = 0
start = time.time()

with open(DONE_LOG, 'a', encoding='utf-8') as log_f:
    for i, code in enumerate(need):
        elapsed = time.time() - start
        rate = (i + 1) / max(elapsed, 0.1)
        remain_sec = (len(need) - i - 1) / max(rate, 0.01)
        
        # 判断是童子还是长者
        is_elder = not code.startswith('0')
        img_type = "长者" if is_elder else "童子"
        
        print(f'[{i+1}/{len(need)}] code={code} [{img_type}] | ~{remain_sec/60:.0f}min剩余', flush=True)
        
        # 根据类型选择不同的prompt构建函数
        if is_elder:
            prompt, seed = build_elder_prompt(code, i)
        else:
            prompt, seed = build_child_prompt(code, i)
        
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
        old = im.group(1)
        new = f'generated-images/code_{c}.jpg'
        if os.path.exists(os.path.join(IMG_DIR, f'code_{c}.jpg')) and old != new:
            new_lines.append(line.replace(old, new))
            changed += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

shutil.copy2(DEITIES_FILE, DEITIES_FILE + '.bak_v16')
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新", flush=True)

# 最终验证
print("\n=== 最终图片统计 ===", flush=True)
all_code_imgs = set()
for fn in os.listdir(IMG_DIR):
    m = re.match(r'^code_(.+)\.jpg$', fn)
    if m:
        all_code_imgs.add(m.group(1))

zero_count = len([c for c in all_code_imgs if c.startswith('0')])
nonzero_count = len([c for c in all_code_imgs if not c.startswith('0')])
total = len(all_code_imgs)
print(f"童子图: {zero_count}/317", flush=True)
print(f"长者图: {nonzero_count}/{593-zero_count}", flush=True)
print(f"总计: {total} 张 code_*", flush=True)
