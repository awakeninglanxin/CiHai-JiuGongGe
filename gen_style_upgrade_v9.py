"""
慈海九宫格 - 风格升级重生脚本 v9
目标: 为 deities.js 中尚未生成新风格图片的681个code生成图片，完成后自动复制到顶层并替换路径
风格: Tensor.Art LORA唯美风格 - 水晶质感、精灵耳、粉紫调、梦幻光效
流程: 
  1. 读取deities.js找出需要生成的code（排除已生成新风格的）
  2. 逐个生成保存图片到 individual 目录
  3. 完成后自动将新版图片移到顶层生成的-images/ 目录
  4. 自动替换 deities.js 中对应code的图片路径
"""
import os
import sys
import time
import random
import hashlib
import requests
import re
import shutil
from pathlib import Path

# 强制flush
sys.stdout.reconfigure(line_buffering=True)

# 配置
PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
BACKUP_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual_backup_v9")
IMG_DIR = os.path.join(PROJECT_DIR, "generated-images")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")
os.makedirs(INDIVIDUAL_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

print("=" * 60)
print("慈海九宫格 - 风格升级重生 v9")
print("=" * 60)

# ==================== Step 1: 读取已生成图片 ====================
print("\n步骤1: 读取已生成的新风格图片...")
existing_new_codes = set()
for f in os.listdir(IMG_DIR):
    if f.startswith('code_') and f.endswith('.jpg'):
        existing_new_codes.add(f.replace('code_', '').replace('.jpg', ''))
print(f"  已生成新风格图片: {len(existing_new_codes)} 个code")

# ==================== Step 2: 找出需要生成的code ====================
print("\n步骤2: 读取 deities.js 找出未生成的code...")
with open(DEITIES_FILE, encoding='utf-8') as f:
    js_content = f.read()

all_js_codes = set(re.findall(r'code:\s*"(\d+)"', js_content))
need_gen = sorted(all_js_codes - existing_new_codes)
print(f"  总code数: {len(all_js_codes)}")
print(f"  未生成新风格的code数: {len(need_gen)}")
if need_gen:
    print(f"  第一批: {need_gen[:5]}")
    print(f"  最后一批: {need_gen[-5:]}")

# 读取已生成图片的备份
print(f"\n步骤3: 备份 existing individual 图片...")
jpg_files = [f for f in os.listdir(INDIVIDUAL_DIR) if f.endswith(('.jpg', '.png'))]
backup_count = 0
for f in jpg_files:
    try:
        shutil.copy2(os.path.join(INDIVIDUAL_DIR, f), os.path.join(BACKUP_DIR, f))
        backup_count += 1
    except:
        pass
print(f"  已备份 {backup_count} 张")

# ==================== Step 4: 风格模板 ====================
STYLE_TEMPLATES = [
    dict(
        base="ethereal fairy maiden, crystal pointed elf ears, glowing light-crystal embedded in flowing hair, {skin_tone} skin tone, {hair_desc}, {jewelry_desc}, {wing_desc}, pastel {bg_color} and lavender gradient background, magical sparkle particles, soft focus bokeh, dreamy atmosphere",
        modifiers=["holding a glowing crystal orb", "with floating magical rune stones", "surrounded by glowing butterflies", "with ethereal light ribbon streamers"],
        eyes_options=["gentle compassionate crystal eyes", "piercing amethyst violet eyes", "warm honey amber eyes"],
        accent_colors=["ruby red", "sapphire blue", "emerald green", "amethyst purple", "golden yellow"],
        accent_tags=", ruby red crystal gem accents, ruby red flower crown",
    ),
    dict(
        base="celestial angel warrior, golden pointed elf ears, starlight crystal crown, {hair_desc}, {jewelry_desc}, luminous radiant wings, cosmic starfield nebula background, divine golden ethereal aura, warm sunrise lighting",
        modifiers=["wielding a crystal magic sword", "with celestial staff of light", "surrounded by floating golden coins", "holding a shield of stars"],
        eyes_options=["radiant golden eyes", "piercing steel gray eyes", "deep sapphire dark eyes"],
        accent_colors=["golden amber", "silver white", "bronze copper"],
        accent_tags=", golden celestial armor accents, golden wing feather details",
    ),
    dict(
        base="lunar goddess portrait, silver crescent-pointed elf ears, moonstone hair ornaments, {hair_desc}, pearl and opal necklace, flowing white silk ethereal gown, twilight {bg_color} and midnight blue gradient background, moonlight rays, shimmering stars",
        modifiers=["holding a silver mirror of truth", "with floating moonlit lotus flowers", "surrounded by fireflies and starlight", "with ethereal water droplets"],
        eyes_options=["serene lunar silver eyes", "mystic deep indigo eyes", "gentle pearl white eyes"],
        accent_colors=["silver white", "pearl iridescent", "midnight blue"],
        accent_tags=", moonstone crystal jewelry set, silver crescent moon motifs",
    ),
    dict(
        base="floral fairy princess, petal-shaped pointed ears, {hair_accessory}, {hair_desc}, flower petal earrings and vine bracelet, dress made of overlapping translucent flower petals, enchanted garden with blooming cherry blossoms, dappled sunlight filtering through leaves",
        modifiers=["holding a magical flower bouquet", "with a butterfly companion", "surrounded by floating pollen sparkles", "playing a tiny flute"],
        eyes_options=["sweet innocent rosy eyes", "gentle spring green eyes", "warm peach amber eyes"],
        accent_colors=["pastel pink", "lavender purple", "soft mint green", "peach coral"],
        accent_tags=", pastel rose and lavender flower accents, delicate petal wing details",
    ),
    dict(
        base="ocean siren mermaid fairy, pearl-tipped pointed ears, coral crown, {hair_desc}, pearl choker and iridescent shell jewelry, shimmering translucent mermaid tail fins, deep ocean underwater scene with coral reef and caustic light rays",
        modifiers=["holding a magical pearl conch", "with sea turtle companion", "surrounded by floating ocean bubbles", "playing a nautilus shell horn"],
        eyes_options=["mysterious oceanic teal eyes", "deep sea sapphire eyes", "bright turquoise eyes"],
        accent_colors=["teal aquamarine", "pearl iridescent", "ocean turquoise"],
        accent_tags=", coral and pearl jewelry, iridescent sea-shell armor pieces",
    ),
    dict(
        base="phoenix fire spirit, flame-tipped pointed ears, {hair_accents}, crimson and amber {hair_desc}, ruby and topaz fiery jewelry, burning ethereal flame wings, magma and floating ember background with dramatic warm lighting, intense fierce expression",
        modifiers=["holding a flaming torch of eternity", "with a phoenix bird companion", "surrounded by floating fire runes", "casting fire magic spell"],
        eyes_options=["fiery determined amber eyes", "passionate crimson red eyes", "burning golden eyes"],
        accent_colors=["crimson red", "amber orange", "burning gold"],
        accent_tags=", flame crystal jewelry set, molten lava texture details, fire-wing feather patterns",
    ),
    dict(
        base="ice crystal queen, diamond-tipped pointed ears, {hair_desc} with ice crystal ornaments, sapphire tiara and diamond frost necklace, frozen crystal gown with ice shard geometric details, aurora borealis sky background with falling snowflakes and crystalline ice palace ruins",
        modifiers=["holding an ice scepter of frost", "with a white wolf companion", "surrounded by frozen snowflakes", "casting ice magic spell"],
        eyes_options=["regal icy blue eyes", "frost crystal pale eyes", "cold sapphire piercing eyes"],
        accent_colors=["ice blue", "frost silver", "diamond white"],
        accent_tags=", diamond ice crystal jewelry, frost-encrusted armor details, frozen wing patterns",
    ),
    dict(
        base="forest druid nymph, leaf-tipped pointed ears, {hair_desc} braided with living vines and wildflowers, amber pendant and jade vine bracelet, outfit of woven moss and living leaf armor, ancient magical forest with giant sequoia trees, sunbeams through canopy, floating fireflies",
        modifiers=["holding a wooden staff of nature", "with a fox companion", "surrounded by glowing mushrooms", "chanting earth magic"],
        eyes_options=["wise earth-brown eyes", "gentle forest green eyes", "warm amber soulful eyes"],
        accent_colors=["earth green", "forest brown", "leaf gold"],
        accent_tags=", vine and leaf jewelry, moss-textured cloak, flower-crown hair ornament",
    ),
    dict(
        base="time alchemist sage, glowing crystal-tipped pointed ears, {hair_desc} with golden threading, arcane clockwork amulet and golden symbol pendant, ornate robe with floating geometric runes, mystical laboratory with glowing orb crystals and floating alchemical symbols, {bg_color} cosmic nebula background",
        modifiers=["holding a floating astrolabe", "with a spectral owl companion", "surrounded by floating clock gears", "reading an ancient grimoire"],
        eyes_options=["mysterious knowing violet eyes", "arcane gold-rimmed crystal eyes", "deep cosmic purple eyes"],
        accent_colors=["mystic purple", "arcane gold", "cosmic violet"],
        accent_tags=", golden alchemy symbol jewelry, clockwork gear accessories, arcane rune embroidery",
    ),
    dict(
        base="void dream guardian, shadow-etched pointed ears, {hair_desc} with rainbow iridescent shimmer, glowing crystal half-mask, dark ethereal robes with neon energy lines, cosmic dreamscape with floating islands and surreal geometry, {bg_color} neon lighting, psychedelic surreal atmosphere",
        modifiers=["holding a dream catchers of void", "with a spectral moth companion", "surrounded by floating dream orbs", "casting void magic"],
        eyes_options=["enigmatic neon eyes", "otherworldly deep violet eyes", "mysterious rainbow iridescent eyes"],
        accent_colors=["neon purple", "cyber cyan", "void magenta"],
        accent_tags=", neon crystal jewelry, holographic fabric textures, digital art style fusion",
    ),
]

SKIN_TONES = ["porcelain pale", "warm ivory", "golden wheat", "rosy peach", "porcelain white"]
HAIR_DESCS = [
    "long flowing silken {hair_color} hair",
    "wavy cascading {hair_color} locks",
    "straight sleek {hair_color} hair",
    "intricate braided {hair_color} hairstyle",
    "romantic loose {hair_color} curls",
    "elegant {hair_color} updo hairstyle",
    "long {hair_color} hair with side braid",
    "flowing windblown {hair_color} hair",
]
HAIR_COLORS = ["silver", "rose-gold", "chestnut brown", "platinum blonde", "jet black", "auburn red", "lavender", "ice blue", "honey blonde", "deep burgundy"]
JEWELRY_OPTIONS = [
    "layered crystal choker necklace and dangling gem earrings",
    "delicate pearl strand necklace with gem pendant",
    "ornate golden torc necklace and vine leaf earrings",
    "layered leather cord and crystal bead necklace with horn earrings",
    "thin golden chain with moonstone pendant and star-drop earrings",
]
WING_OPTIONS = [
    "translucent iridescent dragonfly wings",
    "large ethereal butterfly wings with stained-glass patterns",
    "delicate feathery angel wings in pastel tones",
    "shimmering crystalline butterfly wings",
    "small sparkling fairy wings with light refraction",
]
FLOWER_ACC = [
    "wildflower vine crown of roses and lavender",
    "single white lily tucked behind ear",
    "woven rose-gold laurel wreath",
    "delicate daisy-chain headband",
    "crystal flower hair comb",
]
HAIR_ACC = [
    "twined with golden threads",
    "adorned with small gemstones",
    "with a flowing silk ribbon",
    "woven with tiny white flowers",
    "secured with a golden hair clip",
]
BG_COLOR_OPTIONS = ["lavender", "rose", "periwinkle", "pale teal", "soft peach", "mint", "coral", "lilac", "baby blue", "powder pink"]


def build_unique_prompt(code, idx):
    """为每个code构建独一无二的prompt"""
    template = STYLE_TEMPLATES[idx % len(STYLE_TEMPLATES)]
    skin = random.choice(SKIN_TONES)
    hair_desc_fmt = random.choice(HAIR_DESCS)
    hair_color = random.choice(HAIR_COLORS)
    hair_desc = hair_desc_fmt.format(hair_color=hair_color)
    jewelry = random.choice(JEWELRY_OPTIONS)
    modifier = random.choice(template["modifiers"])
    eye_var = random.choice(template["eyes_options"])
    bg = random.choice(BG_COLOR_OPTIONS)
    wing = ""
    if "wing_desc" in template["base"]:
        wing = random.choice(WING_OPTIONS)

    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    accent_idx = code_hash % len(template["accent_colors"])
    accent_color = template["accent_colors"][accent_idx]
    accent_tag = template["accent_tags"].replace("ruby red", accent_color).replace("Ruby", accent_color.title())

    hair_acc = random.choice(FLOWER_ACC) if idx % 10 == 3 else random.choice(HAIR_ACC)

    base = template["base"]
    base = base.replace("{skin_tone}", skin)
    base = base.replace("{hair_desc}", hair_desc)
    base = base.replace("{jewelry_desc}", jewelry)
    base = base.replace("{wing_desc}", wing)
    base = base.replace("{bg_color}", bg)
    base = base.replace("{hair_accessory}", hair_acc)
    base = base.replace("{hair_accents}", hair_acc)

    prompt = (
        f"Portrait of a {base}, {eye_var}, {modifier}{accent_tag}, "
        f"beautiful anime-influenced semi-realistic style, soft romantic lighting, "
        f"fine art illustration, trending on ArtStation, highly detailed, "
        f"sharp focus, 4k resolution, elegant composition, {accent_color} accent palette"
    )
    return prompt, code_hash


def generate_image(code, prompt, seed_val, output_dir, max_retries=5):
    """通过Pollinations.ai API生成图片"""
    prompt_encoded = requests.utils.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{prompt_encoded}"
        f"?width=768&height=768&seed={seed_val}&model=flux&nologo=true"
    )

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 200 and len(resp.content) > 50000:
                filename = f"code_{code}.jpg"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return True, filepath
            time.sleep(2 + attempt)
        except Exception as e:
            print(f"    重试 {attempt+1}/{max_retries}: {str(e)[:60]}")
            time.sleep(5)

    return False, None


# ==================== Step 5: 开始生成 ====================
print(f"\n{'='*60}")
print(f"步骤4: 开始生成 {len(need_gen)} 张新风格肖像...")
print(f"{'='*60}\n")

success = 0
fail = 0
start_time = time.time()

for idx, code in enumerate(need_gen):
    elapsed = time.time() - start_time
    rate = (idx + 1) / max(elapsed, 0.1)
    remaining = (len(need_gen) - idx - 1) / max(rate, 0.1)

    prompt, seed = build_unique_prompt(code, idx)
    print(f"[{idx+1}/{len(need_gen)}] code={code} | 总进度{(idx+1)/len(need_gen)*100:.0f}% | 剩余~{remaining/60:.0f}分钟", flush=True)

    ok, path = generate_image(code, prompt, seed, INDIVIDUAL_DIR)
    if ok:
        success += 1
        size_kb = os.path.getsize(path) / 1024
        print(f"  ✓ {os.path.basename(path)} ({size_kb:.0f}KB)", flush=True)
    else:
        fail += 1
        print(f"  ✗ 生成失败: {code}", flush=True)

    time.sleep(2.0)

    if (idx + 1) % 50 == 0:
        pct = (idx + 1) / len(need_gen) * 100
        print(f"\n  >> 进度: {idx+1}/{len(need_gen)} ({pct:.0f}%) 成功:{success} 失败:{fail}\n", flush=True)

total_time = time.time() - start_time
print(f"\n{'='*60}")
print(f"生成完成!")
print(f"总计: {len(need_gen)} | 成功: {success} | 失败: {fail}")
print(f"总耗时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)")
print(f"{'='*60}")

# ==================== Step 6: 移动到顶层 ====================
print(f"\n{'='*60}")
print(f"步骤5: 移动生成的图片到顶层并替换deities.js...")
print(f"{'='*60}")

# 移动文件
moved = 0
for fname in os.listdir(INDIVIDUAL_DIR):
    if fname.startswith('code_') and fname.endswith('.jpg'):
        src = os.path.join(INDIVIDUAL_DIR, fname)
        dst = os.path.join(IMG_DIR, fname)
        if os.path.exists(dst):
            continue
        shutil.move(src, dst)
        moved += 1

print(f"  已移动 {moved} 张图片到顶层 generated-images/")

# 读取deities.js，替换匹配的图片路径
print(f"\n步骤6: 更新 deities.js 中的图片路径...")
with open(DEITIES_FILE, encoding='utf-8') as f:
    lines = f.readlines()

changed = 0
new_lines = []
for line in lines:
    code_match = re.search(r'code:\s*"(\d+)"', line)
    img_match = re.search(r'image:\s*"([^"]*)"', line)
    
    if code_match and img_match:
        code = code_match.group(1)
        old_img = img_match.group(1)
        new_img = f'generated-images/code_{code}.jpg'
        
        # 检查这个code是否有对应的图片
        if f'code_{code}.jpg' in os.listdir(IMG_DIR):
            new_lines.append(line.replace(old_img, new_img))
            changed += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# 备份并写入
bak_file = DEITIES_FILE + '.bak17'
shutil.copy2(DEITIES_FILE, bak_file)
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"  已替换 {changed} 个code的图片路径")
print(f"  已创建备份: {bak_file}")

# 最终统计
final_existing = sum(1 for f in os.listdir(IMG_DIR) if f.startswith('code_') and f.endswith('.jpg') and not re.search(r'_\d{13,15}', f))
print(f"\n{'='*60}")
print(f"=== 全部完成 ===")
print(f"新风格图片总数: {final_existing}")
print(f"还需生成: {len(all_js_codes) - final_existing}")
print(f"{'='*60}")
