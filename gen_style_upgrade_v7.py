"""
慈海九宫格 - 风格升级重生脚本 v7
目标: 基于微信图片中的Tensor.Art LORA唯美风格，重新生成320张individual肖像
风格特征: 水晶质感、精灵耳、粉紫调、梦幻光效、飘逸长发、宝石饰品、柔焦
"""
import os
import sys
import time
import random
import requests
from pathlib import Path

# 配置
OUTPUT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 从现有文件名提取code列表
existing_files = os.listdir(OUTPUT_DIR)
codes = []
for f in existing_files:
    if f.startswith("code_") and f.endswith(".jpg"):
        # code_XXXX_timestamp.jpg
        parts = f.replace(".jpg", "").split("_")
        code = "_".join(parts[1:-1])
        codes.append(code)

codes.sort()
print(f"找到 {len(codes)} 个code，开始风格升级重生...")
print(f"样本codes: {codes[:5]}")

# ============================================================
# Tensor.Art LORA 唯美风格提示词库
# 基于微信图片分析提炼的风格体系
# ============================================================

# 基础风格前缀 - 统一应用
BASE_PROMPTS = [
    # 类型1: 水晶精灵仙子
    "ethereal fairy maiden, crystal pointy ears, glowing crystals embedded in hair, pale pink skin, flowing silver-pink long hair, crystal diamond tiara, iridescent translucent wings, moonstone necklace, dreamy pastel pink and lavender background, magical sparkles, soft focus, bokeh lights, fantasy art, beautiful portrait, delicate features, gentle smile, watercolor and oil painting hybrid style, cinematic lighting, masterpiece, ultra detailed, 4k resolution, soft romantic atmosphere, pastel color palette",
    # 类型2: 星辰天使战士
    "celestial angel warrior, golden pointed elf ears, starlight crown on forehead, flowing golden blonde hair, radiant white and gold armor with crystal gems, luminous wings, cosmic starfield background with nebula, divine golden aura, ethereal glow, fantasy portrait, majestic expression, intricate gold filigree details, warm golden hour lighting, masterpiece, ultra detailed, 4k resolution, epic fantasy art style",
    # 类型3: 月光女神
    "lunar goddess portrait, silver pointed elf ears, crescent moon hairpin, cascading silver-white long hair, pearl and opal jewelry, flowing white silk gown, twilight purple and blue gradient background, moonlight rays, shimmering stars, mystical atmosphere, serene expression, elegant posture, enchanted forest backdrop, soft silver glow, fantasy artwork, masterpiece, ultra detailed, 4k resolution",
    # 类型4: 花仙子
    "floral fairy princess, petal-pointed elf ears, flower crown wreath, flowing rose-pink wavy hair, emerald and ruby earrings, dress made of overlapping flower petals, enchanted garden background with cherry blossoms, dappled sunlight, butterflies, whimsical atmosphere, sweet innocent smile, pastel pink and green palette, romantic fantasy art, masterpiece, ultra detailed, 4k resolution",
    # 类型5: 深海人鱼仙子
    "ocean siren mermaid fairy, pearl-pointed elf ears, coral and seashell headpiece, flowing teal-blue wavy hair, pearl choker and shell jewelry, iridescent mermaid tail shimmer, underwater coral reef background, caustic light rays, aquatic bubbles, mystical oceanic atmosphere, mysterious alluring gaze, turquoise and silver color scheme, ethereal fantasy art, masterpiece, ultra detailed, 4k resolution",
    # 类型6: 凤凰火精灵
    "phoenix fire spirit, flame-shaped pointed ears, crimson and amber flowing hair with fire highlights, ruby and topaz jewelry, burning orange and red ethereal wings, magma and ember background with floating fire particles, dramatic warm lighting, fierce determined expression, Celtic knotwork armor accents, fantasy art, masterpiece, ultra detailed, 4k resolution",
    # 类型7: 冰雪精灵女王
    "ice crystal queen, diamond-shaped pointed ears, cascading platinum white hair with ice crystal ornaments, sapphire and diamond tiara, frozen blue gown with ice shard details, aurora borealis background, snowflakes falling, crystalline ice palace, cold blue and silver palette, regal commanding gaze, frost effect on skin, fantasy artwork, masterpiece, ultra detailed, 4k resolution",
    # 类型8: 森林德鲁伊仙女
    "forest druid nymph, leaf-shaped pointed ears, long chestnut hair intertwined with vines and flowers, amber and jade pendant, living bark and leaf armor, ancient magical forest background with giant trees, sunlight filtering through canopy, fireflies, earthy green and brown palette, wise serene expression, nature magic glow, fantasy art, masterpiece, ultra detailed, 4k resolution",
    # 类型9: 时光炼金术士
    "time alchemist sage, crystal-glowing pointed ears, half-white half-black flowing hair with golden threads, arcane symbols floating around, ornate golden clockwork jewelry and amulet, laboratory with floating orbs and crystals, mystical purple and gold cosmic background, arcane runes, mysterious knowing smile, steampunk fantasy elements, masterpiece, ultra detailed, 4k resolution",
    # 类型10: 虚空梦境守护者
    "void dream guardian, ethereal shadow-pointed ears, flowing dark purple hair with rainbow iridescence, glowing crystal mask half-covered face, void energy swirling around, cosmic nightmare dreamscape background with floating islands, neon purple and cyan lighting, psychedelic fantasy art, enigmatic expression, otherworldly beauty, masterpiece, ultra detailed, 4k resolution",
]

# 每个code附加的独特描述符，增加差异化
UNIQUE_MODIFIERS = [
    "holding a glowing crystal orb",
    "playing a magical harp",
    "surrounded by butterflies",
    "with floating magical runes",
    "holding a magic wand with crystal tip",
    "with ethereal ribbon streamers",
    "standing on a cloud platform",
    "with a mystical compass in hand",
    "surrounded by floating petals",
    "with a luminous sword",
    "holding a magical book with glowing pages",
    "with celestial staff",
    "with floating water droplets",
    "holding a lantern of light",
    "with a phoenix companion",
    "with a wolf companion",
    "holding a mirror of truth",
    "with a musical instrument",
    "surrounded by light ribbons",
    "holding a flower of power",
]

# 面部特征变化
FACE_VARIATIONS = [
    "gentle compassionate eyes",
    " piercing crystal blue eyes",
    "mysterious amethyst violet eyes",
    "warm amber honey eyes",
    "emerald green mystic eyes",
    "stormy gray silver eyes",
    "golden radiant eyes",
    "deep sapphire dark eyes",
    "rose pink tender eyes",
    "teal ocean bright eyes",
]

# 发型发色变化
HAIR_VARIATIONS = [
    "long flowing silken hair",
    "wavy cascading hair",
    "straight sleek hair",
    "braided intricate hairstyle",
    "messy windblown hair",
    "loose curls hair",
    "twin tails hairstyle",
    "elegant updo hairstyle",
    "half-up half-down hair",
    "ponytail hairstyle",
]

def build_prompt(code, idx):
    """构建独特的prompt，融入code特征"""
    # 基础风格从池中选取
    base = BASE_PROMPTS[idx % len(BASE_PROMPTS)]

    # 随机添加modifier
    modifier = random.choice(UNIQUE_MODIFIERS)

    # 随机面部和发型
    face = random.choice(FACE_VARIATIONS)
    hair = random.choice(HAIR_VARIATIONS)

    # 加入code作为独特seed
    unique_seed = sum(int(c) for c in code if c.isdigit())
    color_tag = ""
    if unique_seed % 5 == 0:
        color_tag = ", ruby red accent color theme"
    elif unique_seed % 5 == 1:
        color_tag = ", sapphire blue accent color theme"
    elif unique_seed % 5 == 2:
        color_tag = ", emerald green accent color theme"
    elif unique_seed % 5 == 3:
        color_tag = ", amethyst purple accent color theme"
    else:
        color_tag = ", golden yellow accent color theme"

    prompt = f"{base}, {hair}, {face}, {modifier}{color_tag}, " \
             "professional photography, portrait photography, " \
             "soft diffused lighting, high quality render, trending on artstation"

    return prompt


def generate_image(code, prompt, max_retries=5):
    """通过Pollinations生成图片"""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=768&seed={hash(code) & 0xFFFFFFFF}&model=flux"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=120, stream=True)
            if response.status_code == 200:
                img_data = response.content
                if len(img_data) > 50000:  # >50KB
                    timestamp = int(time.time() * 1000)
                    filename = f"code_{code}_{timestamp}.jpg"
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    return True, filepath
            time.sleep(3)
        except Exception as e:
            time.sleep(5)

    return False, None


def main():
    success_count = 0
    fail_count = 0
    total = len(codes)

    for idx, code in enumerate(codes):
        prompt = build_prompt(code, idx)
        print(f"[{idx+1}/{total}] 正在生成 code={code}...")

        ok, path = generate_image(code, prompt)
        if ok:
            success_count += 1
            print(f"  ✓ 已保存: {os.path.basename(path)}")
        else:
            fail_count += 1
            print(f"  ✗ 失败: code={code}")

        # 冷却时间，避免被封
        time.sleep(2)

        # 每50个保存一次进度
        if (idx + 1) % 50 == 0:
            print(f"\n--- 进度: {success_count}成功, {fail_count}失败 ---\n")

    print(f"\n=== 完成 ===")
    print(f"成功: {success_count}/{total}")
    print(f"失败: {fail_count}/{total}")


if __name__ == "__main__":
    random.seed(42)
    main()
