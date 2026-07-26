"""
v1 古朴风格恢复器
恢复 138 张图到 v1-v6 的早期古风长句描述风格
在 v1 基础上改善画质关键词
"""
import os, sys, time, random, hashlib, re, urllib.request

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
BASE_URL = 'https://image.pollinations.ai'
OUTPUT_DIR = os.path.join(IMG_DIR)

# ====== v1-v6 原始 NODE_PROMPTS（从 gen_individual_portraits.py 提取）=====
NODE_PROMPTS = {
    -1: [
        "A majestic cosmic entity floating in primordial void, translucent crystalline body with golden veins, ancient wisdom etched in its form, ethereal light emanating from within, divine presence radiating authority",
        "An otherworldly guardian deity emerging from nebulous darkness, robes woven from starlight, eyes holding galaxies, a being of pure consciousness standing atop cosmic waves",
        "Divine architect of reality, a luminous figure with geometric fractal patterns across its body, surrounded by floating sacred symbols, ancient cosmic energy swirling around",
        "A celestial sovereign with flowing robes of iridescent light, crown of constellations on head, standing before the fabric of spacetime itself, commanding the forces of creation",
        "Ancient cosmic librarian of the multiverse, a wise being with eyes like twin suns, holding scrolls of infinite knowledge, draped in robes of woven dark matter and starlight",
    ],
    0: [
        "A young celestial being in training, wearing robes of dawn light, holding a staff of pure energy, standing at the gateway between mortal and divine realms, aura of potential radiating outward",
        "An awakened soul in manifestation form, glowing with newborn divine power, surrounded by swirling spiritual energy, a bridge between earth and heaven",
        "A spiritual successor channeling cosmic wisdom, youthful yet ancient eyes, draped in garments of shifting light, standing on clouds of pure intention",
    ],
    1: [
        "A mysterious scaled warrior emerging from shadow, golden slit eyes gleaming with strategic intelligence, armor forged from volcanic glass, standing in an ancient reptilian temple",
        "A reptilian deity of survival and dominance, muscular form covered in iridescent scales that shift from jade to obsidian, claws that carve destiny into stone tablets",
        "Ancient guardian of primal instincts, a sleek reptilian sage with mercury-silver scales, standing amid desert ruins of a forgotten civilization",
    ],
    2: [
        "A shimmering hybrid being of extraordinary beauty, skin that shifts between gold and violet, eyes of twin flames representing two worlds united in perfect harmony",
        "A being of extraordinary synthesis, half-mortal half-divine with wings of crystallized light, standing at the convergence of all timelines",
        "An evolved consciousness manifested as a radiant humanoid with multiple pairs of arms, each holding a tool of creation",
    ],
    3: [
        "A luminous Sirius ambassador with radiant white-gold robes, standing on a crystalline platform above vast oceans, three suns visible in the sky behind, voice of cosmic music",
        "A being of pure Sirius light, tall and elegant with skin like polished silver, eyes burning with the wisdom of the Dogon star priests, surrounded by sonic frequencies",
        "A celestial musician from Sirius, holding a harp made of light beams, each string a different frequency of creation",
    ],
    4: [
        "A fierce Orion warrior-god with crimson armor studded with binary stars, twin swords of transformation crossing before him, standing atop the ruins of an old paradigm",
        "An Orion enforcer of cosmic justice, tall and imposing with blue-steel skin, eyes of burning white fire, wielding the spear of truth that pierces illusion",
        "A mystical guardian of the Orion Belt constellation, three luminous figures merged into one powerful being, robe adorned with nebula patterns",
    ],
    5: [
        "A chrononaut of immense spatial mastery, floating through folded dimensions with a compass of light pointing to parallel realities, wearing robes that show different time periods",
        "A spacetime navigator with translucent body revealing swirling galaxies within, holding a quantum anchor, standing in a corridor of infinite doorways",
        "An architect of spacetime itself, a being whose form is constantly rewriting its own geometry",
    ],
    6: [
        "A Pleiadian mother being of extraordinary grace, seven auroras of light surrounding her like a halo, wearing garments of rose-gold that shimmer with interstellar dreams",
        "A celestial healer from the Pleiades, hands emanating pulses of restorative turquoise light, eyes holding the depth of cosmic nurseries where stars are born",
        "An empathic Pleiadian diplomat, form composed of crystalline water droplets held together by love",
    ],
    7: [
        "An ancient Annunaki overseer with lapis lazuli skin and golden crown, seated on a throne of geological epochs, holding tablets of destiny inscribed with genetic codes",
        "A primordial judge of the underworld, massive and imposing with skin of living bronze, beard braided with copper wire, eyes of molten gold",
        "An Annunaki elder of deep earth wisdom, form partially crystalline revealing geological strata within",
    ],
    8: [
        "The living Earth consciousness manifested as a magnificent mother figure, hair of flowing rivers, skin of rich soil dotted with forests, eyes of glacial ice and ocean depths",
        "Gaia herself brought to human form, a being whose feet grow roots into the planet, whose breath is wind and weather, surrounded by symbiotic creatures",
        "An earth elemental sovereign with verdigris skin, crown of growing vines and blooming flowers",
    ],
    9: [
        "A wise Arcturian master of the highest octave of love, form glowing with transcendent violet-white light, eyes holding infinite compassion, robe of crystallized wisdom",
        "The cosmic dean of earthly academies, a serene being radiating golden-violet light, staff of ascension in hand, standing at the threshold of dimensional mastery",
        "An Arcturian light-weaver, fingers spinning strands of divine intelligence, form composed of pure crystalline frequency, eyes that see through all veils of illusion",
    ],
    10: [
        "A supreme Jade Emperor in cosmic court regalia, twelve-fold crown blazing with pure white light, holding the scepter of heavenly mandate, floating above a sea of clouds",
        "The Fourth Pure One, a being of immaculate white and gold, four faces representing cardinal directions, each holding a symbol of cosmic governance",
        "A celestial sovereign ascending through four dimensions, form multiplying into quadruplicate representing purity of body, mind, spirit, and essence",
    ],
    11: [
        "A grand master of the three pure realms, robes of flowing white with cloud patterns, staff topped with a triple jewel, standing between Heaven Earth and Humanity",
        "The dean of the three pure realms, an embodiment of cosmic administration, form translucent showing layers of organizational energy, holding scrolls of heavenly decrees",
        "A celestial administrator of supreme rank, crown of three stacked circles representing the unity of origin, manifestation, and dissolution",
    ],
    12: [
        "A master of duodecimal mathematics, wearing a robe divided into twelve segments each containing a sacred symbol, hands forming the number twelve in geometric perfection",
        "The twelve-fold code restorer, body composed of twelve interlocking rings forming a toroidal structure, eyes containing the infinite recursion of base-12 wisdom",
        "A cosmic accountant of the sacred dozen, scales of balanced duality hovering before a wall of twelve numbered doors, each door a different dimension",
    ],
    13: [
        "A primordial innate child deity, luminous form of perfect potential, crown of jade green light, holding a seed of creation that contains universes within its tiny frame",
        "The first innate being, a child of cosmic consciousness with mature eyes and innocent smile, surrounded by a halo of unborn possibilities",
        "An originary spirit in child form, translucent body showing embryonic starlight within, floating in the void between existence and non-existence",
    ],
}

# v1 原版后缀（每个 code 独有）
V1_SUFFIXES = [
    "with subtle fractal patterns reflecting cosmic destiny",
    "glowing with individual quantum signature energy",
    "surrounded by unique astral aura of personal vibration",
    "featuring distinctive cosmic markings of singular identity",
    "with a unique frequency pattern only this being possesses",
    "radiating a personalized energy field of one-of-a-kind resonance",
    "carrying an emblem of their singular cosmic assignment",
    "with eyes that hold a unique constellation only they represent",
]

# ====== 改善画质的全局后缀 ======
QUALITY_BOOST = "ultra detailed digital art, cinematic lighting, divine portrait, masterpiece quality, 8k resolution"


def get_prompt(code, node_id):
    """v1 风格 + 质量提升"""
    prompts = NODE_PROMPTS.get(node_id, NODE_PROMPTS[-1])
    # 用 code hash 选择 prompt 和 suffix
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    base = prompts[h % len(prompts)]
    suffix = V1_SUFFIXES[h % len(V1_SUFFIXES)]
    # 最终 prompt: base + suffix + 画质提升
    return f"{base}, {suffix}, {QUALITY_BOOST}", int(h)


def generate_image(code, prompt, seed, max_retries=5):
    """调用 Pollinations API 生成图片"""
    width, height = 1024, 1024
    prompt_enc = urllib.parse.quote(prompt)
    url = f"{BASE_URL}/prompt/{prompt_enc}?width={width}&height={height}&seed={seed}&nologo=true"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if len(data) > 50000:
                return data
        except Exception as e:
            if '429' in str(e):
                wait = random.uniform(30, 60)
                print(f"    Rate limit 429, 等待 {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f"    尝试 {attempt+1} 出错: {e}")
                time.sleep(random.uniform(5, 15))
    return None


def update_deities_js(code, new_hash):
    """更新 deities.js 中的 image 字段（通过时间戳区分新版本）"""
    if not os.path.exists(DEITIES_FILE):
        return
    with open(DEITIES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # deities.js 中的 image 格式: generated-images/code_XXX.jpg
    # 我们不改文件名，只改时间戳（用于浏览器缓存清除）
    old_img = f'generated-images/code_{code}.jpg'
    new_img = f'generated-images/code_{code}_v1restored.jpg'
    
    # 重命名文件
    old_path = os.path.join(IMG_DIR, f'code_{code}.jpg')
    new_path = os.path.join(IMG_DIR, f'code_{code}_v1restored.jpg')
    
    if os.path.exists(old_path):
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(old_path, new_path)
        print(f"    Renamed: code_{code}.jpg -> code_{code}_v1restored.jpg")
    
    # 更新 deities.js
    content = content.replace(old_img, new_img)
    
    # 备份旧 deities.js
    bak = DEITIES_FILE + '.bak_pre_v1restore'
    if not os.path.exists(bak):
        import shutil
        shutil.copy2(DEITIES_FILE, bak)
    
    with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"    Updated deities.js -> {new_img}")


def main():
    # 138 个待恢复的 code
    codes_input = '1178 1268 1358 178 17268 17358 19358 14268 14138 14178 13328 111781 114228 1152181 16268 16268 13189 14189 15319 16279 17279 115229 111891 12189 12279 123249 124149 125139 125319 126219 13249 14149 14239 14329 15229 15279 16219 18369 1279 419101 428101 124221114 124311113 124321113 125221113 125311112 15291121 18291121 18381121 19381121 111121 151171 161181 1271191 16291121 17291121 115211113 115221113 115311112 125121114 125301112 126121113 126201112 126221112 126311111 127111112 127201111 127211111 121121 1939123 13123 111231 1151281 12123 139123 14127 16129 1119101 1219101 1528101 13202 14202 18303 1319101 1419101 1628101 1728101 11202 119101 12202 128101 137101 15202 16303 19303 19404 1101 1202 1303 404 4202 4303 1252292 11121 122242 14213 15213 112131 12213 13213 123 13134 14224 15224 17314 18314 111341 949134 11224 12134 13224 16314 1134 134 14235 15235 17325 18325 111451 11235 12145 12235 13145 16235 16325 19325 1145 1325 145'
    
    codes = list(dict.fromkeys([c.strip() for c in codes_input.split() if c.strip()]))
    
    # 从 deities.js 获取 code -> node 映射
    with open(DEITIES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'code:\"(\d+)\",.*?node:\s*(\d+)'
    matches = re.findall(pattern, content)
    code_to_node = dict(matches)
    
    print("=" * 70)
    print("v1 古朴风格恢复器 — 138 张图")
    print("=" * 70)
    print(f"待恢复: {len(codes)} 张")
    print(f"输出目录: {IMG_DIR}")
    print(f"deities.js: {DEITIES_FILE}")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(codes):
        node_id = int(code_to_node.get(code, 0))
        prompt, seed = get_prompt(code, node_id)
        
        if i % 10 == 0:
            print(f"\n[{i+1}/{len(codes)}] code={code} (node={node_id})")
        else:
            print(f"  [{i+1}] code={code}")
        
        print(f"    Seed: {seed}")
        print(f"    Prompt: {prompt[:100]}...")
        
        img_data = generate_image(code, prompt, seed)
        
        if img_data:
            output_path = os.path.join(IMG_DIR, f'code_{code}_v1restored.jpg')
            with open(output_path, 'wb') as f:
                f.write(img_data)
            size_kb = len(img_data) / 1024
            print(f"    [OK] Saved ({size_kb:.0f} KB)")
            success_count += 1
            
            # 更新 deities.js
            update_deities_js(code, seed)
            
            # 删除旧文件（如果存在且不是 _v1restored 的）
            old_path = os.path.join(IMG_DIR, f'code_{code}.jpg')
            if os.path.exists(old_path) and 'v1restored' not in old_path:
                os.remove(old_path)
        else:
            print(f"    [FAIL] Could not generate")
            fail_count += 1
        
        # 间隔等待，避免限速
        if i < len(codes) - 1:
            time.sleep(random.uniform(3, 7))
    
    print("\n" + "=" * 70)
    print(f"恢复完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  总计: {len(codes)}")
    print("=" * 70)


if __name__ == '__main__':
    main()
