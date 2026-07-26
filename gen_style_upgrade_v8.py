"""
慈海九宫格 - 风格升级重生脚本 v8
目标: 基于微信图片中的Tensor.Art LORA唯美风格，重新生成320张individual肖像
风格: 水晶质感、精灵耳、粉紫调、梦幻光效、飘逸长发、宝石饰品、柔焦
"""
import os
import sys
import time
import random
import hashlib
import requests
from pathlib import Path

# 强制flush
sys.stdout.reconfigure(line_buffering=True)

# 配置
INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
BACKUP_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual_backup_v7"
os.makedirs(INDIVIDUAL_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# 备份旧图片
print("=" * 60)
print("步骤1: 备份现有320张individual图片...")
existing_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in existing_files if f.endswith(('.jpg', '.png'))]
backup_count = 0
for f in jpg_files:
    src = os.path.join(INDIVIDUAL_DIR, f)
    dst = os.path.join(BACKUP_DIR, f)
    try:
        import shutil
        shutil.copy2(src, dst)
        backup_count += 1
    except:
        pass
print(f"  已备份 {backup_count} 张图片到: {BACKUP_DIR}")
print("=" * 60)

# 从现有文件名提取code列表
codes = []
for f in jpg_files:
    if f.startswith("code_") and f.endswith(".jpg"):
        # code_XXXX_timestamp.jpg 或 code_XXX_YYY_timestamp.jpg (code含多个数字段)
        name = f.replace(".jpg", "").replace(".png", "")
        parts = name.split("_")
        if len(parts) >= 3:
            code = "_".join(parts[1:-1])
            codes.append(code)
        elif len(parts) == 2:
            code = parts[1]
            codes.append(code)

codes = sorted(set(codes))
print(f"步骤2: 找到 {len(codes)} 个唯一code")
print(f"  样本: {codes[:10]}")
print(f"  最后10个: {codes[-10:]}")
print()

# ============================================================
# Tensor.Art LORA 唯美风格提示词库 - 10种风格类型
# ============================================================

STYLE_TEMPLATES = [
    # 1: 水晶精灵仙子
    dict(
        base="ethereal fairy maiden, crystal pointed elf ears, glowing light-crystal embedded in flowing hair, {skin_tone} skin tone, {hair_desc}, {jewelry_desc}, {wing_desc}, pastel {bg_color} and lavender gradient background, magical sparkle particles, soft focus bokeh, dreamy atmosphere",
        modifiers=["holding a glowing crystal orb", "with floating magical rune stones", "surrounded by glowing butterflies", "with ethereal light ribbon streamers"],
        eyes_options=["gentle compassionate crystal eyes", "piercing amethyst violet eyes", "warm honey amber eyes"],
        accent_colors=["ruby red", "sapphire blue", "emerald green", "amethyst purple", "golden yellow"],
        accent_tags=", ruby red crystal gem accents, ruby red flower crown",
    ),
    # 2: 星辰天使战士
    dict(
        base="celestial angel warrior, golden pointed elf ears, starlight crystal crown, {hair_desc}, {jewelry_desc}, luminous radiant wings, cosmic starfield nebula background, divine golden ethereal aura, warm sunrise lighting",
        modifiers=["wielding a crystal magic sword", "with celestial staff of light", "surrounded by floating golden coins", "holding a shield of stars"],
        eyes_options=["radiant golden eyes", "piercing steel gray eyes", "deep sapphire dark eyes"],
        accent_colors=["golden amber", "silver white", "bronze copper"],
        accent_tags=", golden celestial armor accents, golden wing feather details",
    ),
    # 3: 月光女神
    dict(
        base="lunar goddess portrait, silver crescent-pointed elf ears, moonstone hair ornaments, {hair_desc}, pearl and opal necklace, flowing white silk ethereal gown, twilight {bg_color} and midnight blue gradient background, moonlight rays, shimmering stars",
        modifiers=["holding a silver mirror of truth", "with floating moonlit lotus flowers", "surrounded by fireflies and starlight", "with ethereal water droplets"],
        eyes_options=["serene lunar silver eyes", "mystic deep indigo eyes", "gentle pearl white eyes"],
        accent_colors=["silver white", "pearl iridescent", "midnight blue"],
        accent_tags=", moonstone crystal jewelry set, silver crescent moon motifs",
    ),
    # 4: 花仙子公主
    dict(
        base="floral fairy princess, petal-shaped pointed ears, {hair_accessory}, {hair_desc}, flower petal earrings and vine bracelet, dress made of overlapping translucent flower petals, enchanted garden with blooming cherry blossoms, dappled sunlight filtering through leaves",
        modifiers=["holding a magical flower bouquet", "with a butterfly companion", "surrounded by floating pollen sparkles", "playing a tiny flute"],
        eyes_options=["sweet innocent rosy eyes", "gentle spring green eyes", "warm peach amber eyes"],
        accent_colors=["pastel pink", "lavender purple", "soft mint green", "peach coral"],
        accent_tags=", pastel rose and lavender flower accents, delicate petal wing details",
    ),
    # 5: 深海人鱼仙子
    dict(
        base="ocean siren mermaid fairy, pearl-tipped pointed ears, coral crown, {hair_desc}, pearl choker and iridescent shell jewelry, shimmering translucent mermaid tail fins, deep ocean underwater scene with coral reef and caustic light rays",
        modifiers=["holding a magical pearl conch", "with sea turtle companion", "surrounded by floating ocean bubbles", "playing a nautilus shell horn"],
        eyes_options=["mysterious oceanic teal eyes", "deep sea sapphire eyes", "bright turquoise eyes"],
        accent_colors=["teal aquamarine", "pearl iridescent", "ocean turquoise"],
        accent_tags=", coral and pearl jewelry, iridescent sea-shell armor pieces",
    ),
    # 6: 凤凰火精灵
    dict(
        base="phoenix fire spirit, flame-tipped pointed ears, {hair_accents}, crimson and amber {hair_desc}, ruby and topaz fiery jewelry, burning ethereal flame wings, magma and floating ember background with dramatic warm lighting, intense fierce expression",
        modifiers=["holding a flaming torch of eternity", "with a phoenix bird companion", "surrounded by floating fire runes", "casting fire magic spell"],
        eyes_options=["fiery determined amber eyes", "passionate crimson red eyes", "burning golden eyes"],
        accent_colors=["crimson red", "amber orange", "burning gold"],
        accent_tags=", flame crystal jewelry set, molten lava texture details, fire-wing feather patterns",
    ),
    # 7: 冰雪精灵女王
    dict(
        base="ice crystal queen, diamond-tipped pointed ears, {hair_desc} with ice crystal ornaments, sapphire tiara and diamond frost necklace, frozen crystal gown with ice shard geometric details, aurora borealis sky background with falling snowflakes and crystalline ice palace ruins",
        modifiers=["holding an ice scepter of frost", "with a white wolf companion", "surrounded by frozen snowflakes", "casting ice magic spell"],
        eyes_options=["regal icy blue eyes", "frost crystal pale eyes", "cold sapphire piercing eyes"],
        accent_colors=["ice blue", "frost silver", "diamond white"],
        accent_tags=", diamond ice crystal jewelry, frost-encrusted armor details, frozen wing patterns",
    ),
    # 8: 森林德鲁伊仙女
    dict(
        base="forest druid nymph, leaf-tipped pointed ears, {hair_desc} braided with living vines and wildflowers, amber pendant and jade vine bracelet, outfit of woven moss and living leaf armor, ancient magical forest with giant sequoia trees, sunbeams through canopy, floating fireflies",
        modifiers=["holding a wooden staff of nature", "with a fox companion", "surrounded by glowing mushrooms", "chanting earth magic"],
        eyes_options=["wise earth-brown eyes", "gentle forest green eyes", "warm amber soulful eyes"],
        accent_colors=["earth green", "forest brown", "leaf gold"],
        accent_tags=", vine and leaf jewelry, moss-textured cloak, flower-crown hair ornament",
    ),
    # 9: 时空炼金术士
    dict(
        base="time alchemist sage, glowing crystal-tipped pointed ears, {hair_desc} with golden threading, arcane clockwork amulet and golden symbol pendant, ornate robe with floating geometric runes, mystical laboratory with glowing orb crystals and floating alchemical symbols, {bg_color} cosmic nebula background",
        modifiers=["holding a floating astrolabe", "with a spectral owl companion", "surrounded by floating clock gears", "reading an ancient grimoire"],
        eyes_options=["mysterious knowing violet eyes", "arcane gold-rimmed crystal eyes", "deep cosmic purple eyes"],
        accent_colors=["mystic purple", "arcane gold", "cosmic violet"],
        accent_tags=", golden alchemy symbol jewelry, clockwork gear accessories, arcane rune embroidery",
    ),
    # 10: 虚空梦境守护者
    dict(
        base="void dream guardian, shadow-etched pointed ears, {hair_desc} with rainbow iridescent shimmer, glowing crystal half-mask, dark ethereal robes with neon energy lines, cosmic dreamscape with floating islands and surreal geometry, {bg_color} neon lighting, psychedelic surreal atmosphere",
        modifiers=["holding a dream catchers of void", "with a spectral moth companion", "surrounded by floating dream orbs", "casting void magic"],
        eyes_options=["enigmatic neon eyes", "otherworldly deep violet eyes", "mysterious rainbow iridescent eyes"],
        accent_colors=["neon purple", "cyber cyan", "void magenta"],
        accent_tags=", neon crystal jewelry, holographic fabric textures, digital art style fusion",
    ),
]

# 全局可变数据池
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
    # 选择基础风格模板
    template = STYLE_TEMPLATES[idx % len(STYLE_TEMPLATES)]

    # 随机选择变体
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

    # 根据code数字和决定accent颜色
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    accent_idx = code_hash % len(template["accent_colors"])
    accent_color = template["accent_colors"][accent_idx]
    accent_tag = template["accent_tags"].replace("ruby red", accent_color).replace("Ruby", accent_color.title())

    # 花仙子特殊处理
    hair_acc = random.choice(FLOWER_ACC) if idx % 10 == 3 else random.choice(HAIR_ACC)

    # 组装基础部分
    base = template["base"]
    base = base.replace("{skin_tone}", skin)
    base = base.replace("{hair_desc}", hair_desc)
    base = base.replace("{jewelry_desc}", jewelry)
    base = base.replace("{wing_desc}", wing)
    base = base.replace("{bg_color}", bg)
    base = base.replace("{hair_accessory}", hair_acc)
    base = base.replace("{hair_accents}", hair_acc)

    # 完整的prompt
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
                timestamp = int(time.time() * 1000)
                filename = f"code_{code}_{timestamp}.jpg"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return True, filepath
            time.sleep(2 + attempt)
        except Exception as e:
            print(f"    重试 {attempt+1}/{max_retries}: {str(e)[:60]}")
            time.sleep(5)

    return False, None


def main():
    total = len(codes)
    success = 0
    fail = 0
    start_time = time.time()

    print(f"开始批量生成 {total} 张风格升级肖像...")
    print(f"输出目录: {INDIVIDUAL_DIR}")
    print()

    for idx, code in enumerate(codes):
        elapsed = time.time() - start_time
        rate = idx / max(elapsed, 0.1)
        eta = (total - idx) / max(rate, 0.1)

        prompt, seed = build_unique_prompt(code, idx)
        print(f"[{idx+1}/{total}] code={code} | 耗时{elapsed:.0f}s | 剩余~{eta:.0f}s", flush=True)

        ok, path = generate_image(code, prompt, seed, INDIVIDUAL_DIR)
        if ok:
            success += 1
            fname = os.path.basename(path)
            size_kb = os.path.getsize(path) / 1024
            print(f"  ✓ {fname} ({size_kb:.0f}KB)", flush=True)
        else:
            fail += 1
            print(f"  ✗ 生成失败: {code}", flush=True)

        # 冷却时间
        time.sleep(2.5)

        # 每20个统计一次
        if (idx + 1) % 20 == 0:
            pct = (idx + 1) / total * 100
            print(f"\n  >> 进度: {idx+1}/{total} ({pct:.0f}%) 成功:{success} 失败:{fail}\n", flush=True)

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"=== 全部完成 ===")
    print(f"总计: {total} | 成功: {success} | 失败: {fail}")
    print(f"总耗时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)")
    print(f"平均速度: {total/max(total_time,1):.2f}张/分钟")
    print("=" * 60)


if __name__ == "__main__":
    random.seed(42)
    main()
