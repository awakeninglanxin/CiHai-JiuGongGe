"""
慈海九宫格 - 并发批量生成 v10
用 ThreadPoolExecutor 并发生成，大幅缩短时间
"""
import os, sys, time, random, hashlib, re, shutil, concurrent.futures, requests
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')

# === 风格模板 (同v9) ===
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

def generate_one(code, idx):
    """生成一张图片，返回 (code, success)"""
    out_path = os.path.join(IMG_DIR, f'code_{code}.jpg')
    if os.path.exists(out_path):
        return (code, True, "skip")
    prompt, seed = build_prompt(code, idx)
    prompt_enc = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=768&height=768&seed={seed}&model=flux&nologo=true"
    for attempt in range(5):
        try:
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and len(resp.content) > 50000:
                with open(out_path, 'wb') as f:
                    f.write(resp.content)
                return (code, True, "gen")
            time.sleep(2 + attempt)
        except Exception as e:
            time.sleep(3 + attempt)
    return (code, False, str(attempt))

# === 主流程 ===
print("=" * 60)
print("慈海九宫格 - 并发生成 v10")
print("=" * 60)

# 1. 扫描已有图片
existing_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        existing_codes.add(m.group(1))
print(f"已有图片: {len(existing_codes)}")

# 2. 读取deities.js codes
with open(DEITIES_FILE, encoding='utf-8') as f:
    js_content = f.read()
all_codes = sorted(set(re.findall(r'code:\s*"(\d+)"', js_content)))
need_gen = [(c, i) for i, c in enumerate(all_codes) if c not in existing_codes]
print(f"总code: {len(all_codes)} | 需生成: {len(need_gen)}")

# 3. 并发生成 (3并发, 低并发避免API限流)
MAX_WORKERS = 3
print(f"\n开始并发生成 ({MAX_WORKERS}并发)...")
start_time = time.time()
success = 0
fail = 0
fail_codes = []

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {}
    for code, idx in need_gen:
        future = executor.submit(generate_one, code, idx)
        futures[future] = code
        time.sleep(0.8)  # 错开提交，避免同时发请求
    
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        code, ok, info = future.result()
        if ok:
            success += 1
        else:
            fail += 1
            fail_codes.append(code)
        
        done = i + 1
        elapsed = time.time() - start_time
        rate = done / max(elapsed, 0.1)
        remain = (len(need_gen) - done) / max(rate, 0.01)
        status = "✓" if ok else "✗"
        if done % 10 == 0 or done == len(need_gen):
            print(f"  [{done}/{len(need_gen)}] {status} code={code} | {done/len(need_gen)*100:.1f}% | ~{remain/60:.1f}min剩余 | 成功:{success} 失败:{fail}", flush=True)

total_time = time.time() - start_time
print(f"\n生成完成: 成功{success} 失败{fail} 耗时{total_time:.0f}秒 ({total_time/60:.1f}分钟)")

if fail_codes:
    print(f"失败codes: {fail_codes[:20]}")
    # 重试失败的一次
    print("\n重试失败的codes...")
    retry_success = 0
    for code in fail_codes:
        idx = all_codes.index(code)
        c, ok, info = generate_one(code, idx)
        if ok:
            retry_success += 1
            print(f"  重试成功: {code}")
        else:
            print(f"  重试失败: {code}")
        time.sleep(1)
    print(f"重试结果: {retry_success}/{len(fail_codes)} 成功")

# 4. 更新deities.js
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

bak = DEITIES_FILE + '.bak_v10'
shutil.copy2(DEITIES_FILE, bak)
with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print(f"deities.js更新: {changed}个路径修改 (备份: {bak})")

# 5. 最终统计
final_clean = sum(1 for f in os.listdir(IMG_DIR) if re.match(r'^code_\d+\.jpg$', f))
final_codes = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        final_codes.add(m.group(1))
matching = len(final_codes & set(all_codes))
missing_final = len(all_codes) - matching

print(f"\n{'='*60}")
print(f"=== 最终结果 ===")
print(f"干净图片: {final_clean}")
print(f"匹配deities.js: {matching}/{len(all_codes)}")
print(f"缺失: {missing_final}")
print(f"{'='*60}")
