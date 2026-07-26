"""
慈海九宫格 - 智能等待+生成 v11
先检测API是否可用，可用后以保守速率(每4秒1张)生成
遇到429自动暂停60秒再重试
"""
import os, sys, time, random, hashlib, re, shutil, requests
import subprocess

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')

# === 风格模板 ===
STYLE_TEMPLATES = [
    dict(base="ethereal fairy maiden, crystal pointed elf ears, glowing light-crystal embedded in flowing hair, {skin_tone} skin tone, {hair_desc}, {jewelry_desc}, {wing_desc}, pastel {bg_color} and lavender gradient background, magical sparkle particles, soft focus bokeh, dreamy atmosphere",
         modifiers=["holding a glowing crystal orb","with floating magical rune stones","surrounded by glowing butterflies","with ethereal light ribbon streamers"],
         eyes_options=["gentle compassionate crystal eyes","piercing amethyst violet eyes","warm honey amber eyes"],
         accent_colors=["ruby red","sapphire blue","emerald green","amethyst purple","golden yellow"],
         accent_tags=", ruby red crystal gem accents, ruby red flower crown"),
    dict(base="celestial angel warrior, golden pointed elf ears, starlight crystal crown, {hair_desc}, {jewelry_desc}, luminous radiant wings, cosmic starfield nebula background, divine golden ethereal aura, warm sunrise lighting",
         modifiers=["wielding a crystal magic sword","with celestial staff of light","surrounded by floating golden coins","holding a shield of stars"],
         eyes_options=["radiant golden eyes","piercing steel gray eyes","deep sapphire dark eyes"],
         accent_colors=["golden amber","silver white","bronze copper"],
         accent_tags=", golden celestial armor accents, golden wing feather details"),
    dict(base="lunar goddess portrait, silver crescent-pointed elf ears, moonstone hair ornaments, {hair_desc}, pearl and opal necklace, flowing white silk ethereal gown, twilight {bg_color} and midnight blue gradient background, moonlight rays, shimmering stars",
         modifiers=["holding a silver mirror of truth","with floating moonlit lotus flowers","surrounded by fireflies and starlight","with ethereal water droplets"],
         eyes_options=["serene lunar silver eyes","mystic deep indigo eyes","gentle pearl white eyes"],
         accent_colors=["silver white","pearl iridescent","midnight blue"],
         accent_tags=", moonstone crystal jewelry set, silver crescent moon motifs"),
    dict(base="floral fairy princess, petal-shaped pointed ears, {hair_accessory}, {hair_desc}, flower petal earrings and vine bracelet, dress made of overlapping translucent flower petals, enchanted garden with blooming cherry blossoms, dappled sunlight filtering through leaves",
         modifiers=["holding a magical flower bouquet","with a butterfly companion","surrounded by floating pollen sparkles","playing a tiny flute"],
         eyes_options=["sweet innocent rosy eyes","gentle spring green eyes","warm peach amber eyes"],
         accent_colors=["pastel pink","lavender purple","soft mint green","peach coral"],
         accent_tags=", pastel rose and lavender flower accents, delicate petal wing details"),
    dict(base="ocean siren mermaid fairy, pearl-tipped pointed ears, coral crown, {hair_desc}, pearl choker and iridescent shell jewelry, shimmering translucent mermaid tail fins, deep ocean underwater scene with coral reef and caustic light rays",
         modifiers=["holding a magical pearl conch","with sea turtle companion","surrounded by floating ocean bubbles","playing a nautilus shell horn"],
         eyes_options=["mysterious oceanic teal eyes","deep sea sapphire eyes","bright turquoise eyes"],
         accent_colors=["teal aquamarine","pearl iridescent","ocean turquoise"],
         accent_tags=", coral and pearl jewelry, iridescent sea-shell armor pieces"),
    dict(base="phoenix fire spirit, flame-tipped pointed ears, {hair_accents}, crimson and amber {hair_desc}, ruby and topaz fiery jewelry, burning ethereal flame wings, magma and floating ember background with dramatic warm lighting, intense fierce expression",
         modifiers=["holding a flaming torch of eternity","with a phoenix bird companion","surrounded by floating fire runes","casting fire magic spell"],
         eyes_options=["fiery determined amber eyes","passionate crimson red eyes","burning golden eyes"],
         accent_colors=["crimson red","amber orange","burning gold"],
         accent_tags=", flame crystal jewelry set, molten lava texture details, fire-wing feather patterns"),
    dict(base="ice crystal queen, diamond-tipped pointed ears, {hair_desc} with ice crystal ornaments, sapphire tiara and diamond frost necklace, frozen crystal gown with ice shard geometric details, aurora borealis sky background with falling snowflakes and crystalline ice palace ruins",
         modifiers=["holding an ice scepter of frost","with a white wolf companion","surrounded by frozen snowflakes","casting ice magic spell"],
         eyes_options=["regal icy blue eyes","frost crystal pale eyes","cold sapphire piercing eyes"],
         accent_colors=["ice blue","frost silver","diamond white"],
         accent_tags=", diamond ice crystal jewelry, frost-encrusted armor details, frozen wing patterns"),
    dict(base="forest druid nymph, leaf-tipped pointed ears, {hair_desc} braided with living vines and wildflowers, amber pendant and jade vine bracelet, outfit of woven moss and living leaf armor, ancient magical forest with giant sequoia trees, sunbeams through canopy, floating fireflies",
         modifiers=["holding a wooden staff of nature","with a fox companion","surrounded by glowing mushrooms","chanting earth magic"],
         eyes_options=["wise earth-brown eyes","gentle forest green eyes","warm amber soulful eyes"],
         accent_colors=["earth green","forest brown","leaf gold"],
         accent_tags=", vine and leaf jewelry, moss-textured cloak, flower-crown hair ornament"),
    dict(base="time alchemist sage, glowing crystal-tipped pointed ears, {hair_desc} with golden threading, arcane clockwork amulet and golden symbol pendant, ornate robe with floating geometric runes, mystical laboratory with glowing orb crystals and floating alchemical symbols, {bg_color} cosmic nebula background",
         modifiers=["holding a floating astrolabe","with a spectral owl companion","surrounded by floating clock gears","reading an ancient grimoire"],
         eyes_options=["mysterious knowing violet eyes","arcane gold-rimmed crystal eyes","deep cosmic purple eyes"],
         accent_colors=["mystic purple","arcane gold","cosmic violet"],
         accent_tags=", golden alchemy symbol jewelry, clockwork gear accessories, arcane rune embroidery"),
    dict(base="void dream guardian, shadow-etched pointed ears, {hair_desc} with rainbow iridescent shimmer, glowing crystal half-mask, dark ethereal robes with neon energy lines, cosmic dreamscape with floating islands and surreal geometry, {bg_color} neon lighting, psychedelic surreal atmosphere",
         modifiers=["holding a dream catchers of void","with a spectral moth companion","surrounded by floating dream orbs","casting void magic"],
         eyes_options=["enigmatic neon eyes","otherworldly deep violet eyes","mysterious rainbow iridescent eyes"],
         accent_colors=["neon purple","cyber cyan","void magenta"],
         accent_tags=", neon crystal jewelry, holographic fabric textures, digital art style fusion"),
]

SKIN_TONES = ["porcelain pale","warm ivory","golden wheat","rosy peach","porcelain white"]
HAIR_DESCS = ["long flowing silken {hair_color} hair","wavy cascading {hair_color} locks","straight sleek {hair_color} hair","intricate braided {hair_color} hairstyle","romantic loose {hair_color} curls","elegant {hair_color} updo hairstyle","long {hair_color} hair with side braid","flowing windblown {hair_color} hair"]
HAIR_COLORS = ["silver","rose-gold","chestnut brown","platinum blonde","jet black","auburn red","lavender","ice blue","honey blonde","deep burgundy"]
JEWELRY_OPTIONS = ["layered crystal choker necklace and dangling gem earrings","delicate pearl strand necklace with gem pendant","ornate golden torc necklace and vine leaf earrings","layered leather cord and crystal bead necklace with horn earrings","thin golden chain with moonstone pendant and star-drop earrings"]
WING_OPTIONS = ["translucent iridescent dragonfly wings","large ethereal butterfly wings with stained-glass patterns","delicate feathery angel wings in pastel tones","shimmering crystalline butterfly wings","small sparkling fairy wings with light refraction"]
FLOWER_ACC = ["wildflower vine crown of roses and lavender","single white lily tucked behind ear","woven rose-gold laurel wreath","delicate daisy-chain headband","crystal flower hair comb"]
HAIR_ACC = ["twined with golden threads","adorned with small gemstones","with a flowing silk ribbon","woven with tiny white flowers","secured with a golden hair clip"]
BG_COLOR_OPTIONS = ["lavender","rose","periwinkle","pale teal","soft peach","mint","coral","lilac","baby blue","powder pink"]

random.seed(42)

def build_prompt(code, idx):
    template = STYLE_TEMPLATES[idx % len(STYLE_TEMPLATES)]
    skin = random.choice(SKIN_TONES)
    hair_desc_fmt = random.choice(HAIR_DESCS)
    hair_color = random.choice(HAIR_COLORS)
    hair_desc = hair_desc_fmt.format(hair_color=hair_color)
    jewelry = random.choice(JEWELRY_OPTIONS)
    modifier = random.choice(template["modifiers"])
    eye_var = random.choice(template["eyes_options"])
    bg = random.choice(BG_COLOR_OPTIONS)
    wing = random.choice(WING_OPTIONS) if "wing_desc" in template["base"] else ""
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    accent_idx = code_hash % len(template["accent_colors"])
    accent_color = template["accent_colors"][accent_idx]
    accent_tag = template["accent_tags"].replace("ruby red", accent_color).replace("Ruby", accent_color.title())
    hair_acc = random.choice(FLOWER_ACC) if idx % 10 == 3 else random.choice(HAIR_ACC)
    base = template["base"]
    for k, v in [("{skin_tone}", skin), ("{hair_desc}", hair_desc), ("{jewelry_desc}", jewelry),
                 ("{wing_desc}", wing), ("{bg_color}", bg), ("{hair_accessory}", hair_acc), ("{hair_accents}", hair_acc)]:
        base = base.replace(k, v)
    prompt = (f"Portrait of a {base}, {eye_var}, {modifier}{accent_tag}, "
              f"beautiful anime-influenced semi-realistic style, soft romantic lighting, "
              f"fine art illustration, trending on ArtStation, highly detailed, "
              f"sharp focus, 4k resolution, elegant composition, {accent_color} accent palette")
    return prompt, int(code_hash)

def check_api():
    """检测API是否可用"""
    try:
        url = "https://image.pollinations.ai/prompt/test?width=64&height=64&model=flux&nologo=true"
        resp = requests.get(url, timeout=15)
        return resp.status_code == 200 and len(resp.content) > 5000
    except:
        return False

def generate_one(code, prompt, seed):
    """生成一张图片，处理429"""
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=768&seed={seed}&model=flux&nologo=true"
    
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and len(resp.content) > 50000:
                out_path = os.path.join(IMG_DIR, f'code_{code}.jpg')
                with open(out_path, 'wb') as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 429:
                # 429: 等60秒再重试
                print(f'  ⏳ 429限速, 等待60秒...', flush=True)
                time.sleep(60)
            else:
                time.sleep(3 + attempt * 2)
        except Exception as e:
            time.sleep(5 + attempt * 3)
    return False

# === 主流程 ===
print("=" * 60)
print("慈海九宫格 - 智能等待+生成 v11")
print("=" * 60)

# 1. 等待API可用
print("\n检测API可用性...", flush=True)
wait_count = 0
while True:
    if check_api():
        print("  ✓ API可用!", flush=True)
        break
    wait_count += 1
    print(f"  ✗ API限速中, 等待60秒... (第{wait_count}次)", flush=True)
    time.sleep(60)

# 2. 扫描已有图片
existing_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        existing_codes.add(m.group(1))
print(f"已有图片: {len(existing_codes)}")

# 3. 读取codes
with open(DEITIES_FILE, encoding='utf-8') as f:
    js_content = f.read()
all_codes = sorted(set(re.findall(r'code:\s*"(\d+)"', js_content)))
need_gen = [(c, i) for i, c in enumerate(all_codes) if c not in existing_codes]
print(f"总code: {len(all_codes)} | 需生成: {len(need_gen)}")

# 4. 顺序生成 (保守速率, 每张间隔3.5秒)
print(f"\n开始生成 (保守模式, 每张~3.5秒)...")
print(f"预估耗时: {len(need_gen) * 4 / 60:.0f} 分钟\n")

success = 0
fail = 0
fail_codes = []
start_time = time.time()
consecutive_429 = 0

for i, (code, idx) in enumerate(need_gen):
    elapsed = time.time() - start_time
    rate = (i + 1) / max(elapsed, 0.1)
    remain = (len(need_gen) - i - 1) / max(rate, 0.01)
    
    print(f'[{i+1}/{len(need_gen)}] code={code} | {(i+1)/len(need_gen)*100:.1f}% | ~{remain/60:.0f}min剩余 | S:{success} F:{fail}', flush=True)
    
    prompt, seed = build_prompt(code, idx)
    ok = generate_one(code, prompt, seed)
    
    if ok:
        success += 1
        consecutive_429 = 0
        print(f'  ✓ done', flush=True)
    else:
        fail += 1
        fail_codes.append(code)
        consecutive_429 += 1
        print(f'  ✗ FAILED', flush=True)
        
        # 连续3次失败，可能又被限速了
        if consecutive_429 >= 3:
            print(f'  ⏳ 连续失败{consecutive_429}次, 暂停120秒...', flush=True)
            time.sleep(120)
            consecutive_429 = 0
    
    time.sleep(0.5)

total_time = time.time() - start_time
print(f"\n{'='*60}")
print(f"生成完成: 成功{success} 失败{fail} 耗时{total_time:.0f}秒 ({total_time/60:.1f}分钟)")

# 5. 重试失败的
if fail_codes:
    print(f"\n重试 {len(fail_codes)} 个失败的codes...")
    # 先检测API
    if not check_api():
        print("API仍不可用, 跳过重试")
    else:
        retry_ok = 0
        for code in fail_codes:
            idx = all_codes.index(code)
            prompt, seed = build_prompt(code, idx)
            if generate_one(code, prompt, seed):
                retry_ok += 1
                print(f"  ✓ {code}", flush=True)
            else:
                print(f"  ✗ {code}", flush=True)
            time.sleep(1)
        print(f"重试结果: {retry_ok}/{len(fail_codes)}")
        success += retry_ok

# 6. 更新deities.js
print(f"\n更新 deities.js...")
with open(DEITIES_FILE, encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
changed = 0
for line in lines:
    code_m = re.search(r'code:\s*"(\d+)"', line)
    img_m = re.search(r'image:\s*"([^"]*)"', line)
    if code_m and img_m:
        code = code_m.group(1)
        old_img = img_m.group(1)
        new_path = f'generated-images/code_{code}.jpg'
        if os.path.exists(os.path.join(IMG_DIR, f'code_{code}.jpg')):
            if old_img != new_path:
                new_lines.append(line.replace(old_img, new_path))
                changed += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

bak = DEITIES_FILE + '.bak_v11'
shutil.copy2(DEITIES_FILE, bak)
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js: {changed}个路径更新 (备份: .bak_v11)")

# 7. 最终统计
final_clean = sum(1 for f in os.listdir(IMG_DIR) if re.match(r'^code_\d+\.jpg$', f))
final_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        final_codes.add(m.group(1))
matching = len(final_codes & set(all_codes))
print(f"\n=== 最终: {matching}/{len(all_codes)} | 缺失: {len(all_codes) - matching} ===")
