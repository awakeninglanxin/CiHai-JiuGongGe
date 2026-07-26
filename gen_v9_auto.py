"""
慈海九宫格 - 批量生成新风格图片 + 自动替换脚本 v9（精简版）
目标: 一次性生成剩余681个code的新风格图片，并更新deities.js
风格: Tensor.Art LORA唯美风格 - 水晶精灵、星辰天使、月光女神等10种风格轮换
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

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
LOG_FILE = os.path.join(PROJECT, 'v9_progress.log')

# 从上次成功的位置恢复
resume_code = None
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('done='):
                parts = line.strip().split(',')
                for p in parts:
                    if p.startswith('done_'):
                        resume_code = p[5:]
    # 收集已完成的code
    done_codes = set()
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^done_(\d+)$', line.strip())
            if m:
                done_codes.add(m.group(1))
    
    if done_codes:
        print(f'检测到上次进度: {len(done_codes)} 张已完成')

print('=' * 70)
print('慈海九宫格 - 风格升级重生 v9 (精简自动版)')
print('=' * 70)

# Step 1: 读取已生成图片
print('\n步骤1: 扫描已生成的新风格图片...')
existing_codes = set()
for f in os.listdir(IMG_DIR):
    if f.startswith('code_') and f.endswith('.jpg'):
        m = re.match(r'^code_(\d+)\.jpg$', f)
        if m:
            existing_codes.add(m.group(1))
print(f'  已生成: {len(existing_codes)} 个')

# Step 2: 读取deities.js的所有code
print('\n步骤2: 读取deities.js的code...')
with open(DEITIES_FILE, encoding='utf-8') as f:
    js_content = f.read()

all_js_codes = sorted(set(re.findall(r'code:\s*"(\d+)"', js_content)))
need_gen = sorted(set(all_js_codes) - existing_codes)
print(f'  总code数: {len(all_js_codes)}')
print(f'  还需生成: {len(need_gen)} 个')

# Step 3: 风格模板 (10种)
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

random.seed(42)

def build_prompt(code, idx):
    """构建prompt"""
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
    return prompt, int(code_hash)

def generate_one(code, prompt, seed, retries=5):
    """生成一张图片"""
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=768&seed={seed}&model=flux&nologo=true"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 200 and len(resp.content) > 50000:
                out_path = os.path.join(IMG_DIR, f'code_{code}.jpg')
                with open(out_path, 'wb') as f:
                    f.write(resp.content)
                return True
            time.sleep(3 + attempt)
        except:
            time.sleep(5)
    return False

# 执行生成
print(f'\n步骤3: 开始生成 {len(need_gen)} 张新风格图片...')
print(f'每张约3秒 + 2秒间隔 ≈ 每张5秒')
print(f'预估总耗时: {len(need_gen) * 5 / 60:.0f} 分钟 ({len(need_gen) * 5 / 3600:.1f} 小时)\n')

success = 0
fail = 0
start_time = time.time()

with open(LOG_FILE, 'a', encoding='utf-8') as log:
    for i, code in enumerate(need_gen):
        t = time.time() - start_time
        rate = (i + 1) / max(t, 0.1)
        remain = (len(need_gen) - i - 1) / max(rate, 0.1)
        
        prompt, seed = build_prompt(code, i)
        print(f'[{i+1}/{len(need_gen)}] code={code} | {(i+1)/len(need_gen)*100:.1f}% | ~{remain/60:.0f}分钟剩余', flush=True)
        
        ok = generate_one(code, prompt, seed)
        if ok:
            success += 1
            print(f'  ✓ done_{code}', flush=True)
            log.write(f'done_{code}\n')
        else:
            fail += 1
            print(f'  ✗ FAILED: {code}', flush=True)
        
        log.flush()
        time.sleep(0.5)
        
        if (i + 1) % 100 == 0:
            pct = (i + 1) / len(need_gen) * 100
            print(f'\n>> [{i+1}/{len(need_gen)}] ({pct:.0f}%) 成功:{success} 失败:{fail}\n', flush=True)

# 更新deities.js
print(f'\n步骤4: 更新 deities.js...')
with open(DEITIES_FILE, encoding='utf-8') as f:
    content = f.read()

# 重建内容：遍历所有code，替换image路径
def replace_images(match):
    code = match.group(1)
    old_img = match.group(2)
    new_img = f'generated-images/code_{code}.jpg'
    if os.path.exists(os.path.join(IMG_DIR, f'code_{code}.jpg')):
        return f'code:"{code}",name:"{code}",{old_img}'.replace(old_img, new_img)
    return match.group(0)

# 更精确的方式
lines = content.split('\n')
new_lines = []
changed = 0
for line in lines:
    code_m = re.search(r'code:\s*"(\d+)"', line)
    img_m = re.search(r'image:\s*"([^"]*)"', line)
    if code_m and img_m:
        code = code_m.group(1)
        old_img = img_m.group(1)
        if os.path.exists(os.path.join(IMG_DIR, f'code_{code}.jpg')):
            new_lines.append(line.replace(old_img, f'generated-images/code_{code}.jpg'))
            changed += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

bak = DEITIES_FILE + '.bak17'
shutil.copy2(DEITIES_FILE, bak)
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

total_time = time.time() - start_time
print(f'\n{"="*70}')
print(f'=== 全部完成 ===')
print(f'生成总数: {len(need_gen)}')
print(f'成功: {success} | 失败: {fail}')
print(f'替换deities.js: {changed} 个code')
print(f'耗时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)')

final_imgs = sum(1 for f in os.listdir(IMG_DIR) if f.startswith('code_') and f.endswith('.jpg'))
final_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        final_codes.add(m.group(1))
final_matching = len(final_codes & set(all_js_codes))
print(f'最终新风格图片总数: {final_imgs} ({final_matching} 个匹配deities.js)')
print(f'还需生成: {len(all_js_codes) - final_matching}')
print(f'{"="*70}')
