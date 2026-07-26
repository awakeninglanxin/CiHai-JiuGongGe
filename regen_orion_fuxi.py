#!/usr/bin/env python3
"""猎户座(Node 4)伏羲女娲风格重生成 - 只重生成25张Node 4问题图"""
import os, sys, time, random, hashlib, urllib.request, json, re

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
DEITIES_FILE = os.path.join(PROJECT, 'deities.js')
BASE_URL = 'https://image.pollinations.ai'

# ====== 猎户座 伏羲女娲风格 prompt ======
ORION_FEATURES = [
    "wise ancient Orion deity with warm bronze-gold skin, large luminous amber eyes with clear distinct pupils symmetrically, dignified serene expression, flowing dark hair with golden highlights, classical Chinese deity features, symmetrical face",
    "noble Orion patriarch with rich copper-bronze complexion, luminous golden-amber eyes clearly visible with bright catchlights, sharp angular but distinctly human facial features, flowing dark hair, benevolent ancient wisdom expression",
    "majestic Orion being with warm golden-bronze skin tone, large luminous eyes with clear pupils symmetrically, classical Chinese god-like features, dignified calm expression, symmetrical balanced composition",
    "Orian celestial elder with radiant bronze-gold skin, luminous amber eyes with distinct pupils, noble human-like features, flowing dark hair with golden shimmer, serene authoritative gaze",
    "ancient Orion deity with warm terracotta-bronze skin, large bright luminous eyes with clear pupils symmetrically, classical Chinese immortal features, dignified human expression, perfect symmetry",
]
ORION_ACCESSORIES = [
    "holding golden compass (gui) in right hand and square ruler (ju) in left hand symmetrically, traditional Chinese celestial symbols, sun disc above head with star constellation patterns around",
    "golden ceremonial headdress with celestial patterns, symmetrical ancient Chinese deity accessories, floating star constellation diagrams on both sides equally, sun-moon symbolism",
    "traditional Chinese celestial crown with golden ornaments, symmetrical hanging beads on both sides, sun-moon disk composition above and below head, star network patterns",
    "golden celestial crown with symmetrical ornaments, holding ancient Chinese measurement tools (compass and square) evenly in both hands, star constellation background",
    "ornate golden headdress with celestial motifs, symmetrical traditional Chinese deity regalia, sun above head and moon below, star network surrounding",
]
ORION_CLOTHING = [
    "wearing flowing ancient Chinese ceremonial robes in golden-brown and deep amber with intricate celestial patterns, symmetrical draping, traditional Hanfu-style wide sleeves, barefoot on cosmic platform",
    "draped in elegant golden-brown Hanfu-style ceremonial garment with symmetrical celestial embroidery, balanced flowing fabric design, traditional Chinese deity attire",
    "wearing ancient Chinese golden-bronze ceremonial robe with symmetrical star constellation patterns, flowing wide sleeves, traditional Hanfu design, balanced draping on both sides",
    "clothed in luminous golden-brown traditional Chinese deity robes with celestial geometric patterns, symmetrical wide sleeves, balanced ancient costume design",
    "wearing flowing ancient Chinese golden-amber ceremonial attire with symmetrical star patterns, traditional Hanfu wide sleeves, balanced dignified draping",
]
ORION_POSES = [
    "standing facing forward with perfect symmetry, TWO COMPLETE ARMS visible symmetrically, right hand holding golden compass (gui) raised, left hand holding square ruler (ju) raised, balanced classical Chinese deity posture",
    "standing dignified facing viewer, arms slightly spread symmetrically, hands holding celestial tools (compass and square) equally on both sides, serene wise expression",
    "standing upright facing forward, TWO ARMS spread symmetrically, right hand holding golden compass, left hand holding square ruler, classical Chinese god composition",
    "standing balanced facing forward, TWO COMPLETE ARMS visible, hands holding ancient Chinese celestial instruments symmetrically, dignified serene expression",
    "standing facing viewer directly, TWO ARMS holding golden compass and square ruler symmetrically, classical Chinese deity pose, balanced composition",
]
ORION_BG = [
    "background is ancient Chinese celestial chamber with golden sun disc above, silver moon below, star constellation patterns connected by lines, traditional绢本彩绘 (silk painting) aesthetic",
    "background shows cosmic temple with sun-moon composition, interconnected star patterns, ancient Chinese celestial diagram style, warm golden-amber lighting",
    "background is ancient Chinese star map chamber with sun disc and moon symbol, constellation lines connecting stars, traditional silk painting aesthetic, golden-amber tones",
    "background shows celestial Chinese cosmos with sun above, moon below, star networks, ancient绢本彩绘 style, warm golden-brown ambient light",
    "background is ancient Chinese cosmic chamber with sun-moon-star composition, interconnected constellation patterns, traditional silk painting aesthetic, golden-amber illumination",
]
ORION_SUFFIX = (
    "masterpiece, best quality, 8k ultra detailed, sharp focus, "
    "ORION ANCIENT CHINESE DEITY STYLE, classical Chinese painting aesthetic, "
    "warm golden-brown and amber color palette with red accents, "
    "smooth bronze skin with natural healthy glow, "
    "CLEAR DISTINCT AMBER EYES with bright pupils symmetrically, "
    "TWO COMPLETE ARMS visible symmetrically, holding compass and square ruler, "
    "SUN-MOON STAR CONSTELLATION BACKGROUND, interconnected star patterns, "
    "CLASSICAL CHINESE DEITY COMPOSITION, dignified serene expression, "
    "FU XI NU WA INSPIRED, ancient Chinese silk painting style, "
    "PERFECT SYMMETRY, balanced celestial imagery, traditional Hanfu robes",
    "NO MISSING LIMBS, COMPLETE BODY, classical Chinese aesthetics"
)

ORION_CODES = [
    "4303","448","404","4167","4178","4202","4224","4235","4246","426",
    "4268","428101","429112","4314","4325","4336","4347","437","415",
    "4189","419101","4213","4257","4279","459",
]

def build_prompt(code, idx):
    h = int(hashlib.md5(code.encode()).hexdigest(), 16)
    prompt = (f"portrait of a {ORION_FEATURES[h % len(ORION_FEATURES)]}, "
              f"{ORION_ACCESSORIES[h % len(ORION_ACCESSORIES)]}, "
              f"{ORION_CLOTHING[h % len(ORION_CLOTHING)]}, "
              f"{ORION_POSES[h % len(ORION_POSES)]}, "
              f"{ORION_BG[h % len(ORION_BG)]}, "
              f"{ORION_SUFFIX}")
    return prompt, int(h)

def generate_image(prompt, seed, output_path, max_retries=5):
    width, height = 768, 1024
    url = (f"{BASE_URL}/image/generate"
           f"?width={width}&height={height}"
           f"&prompt={urllib.parse.quote(prompt)}"
           f"&seed={seed}&nologo=true&model=flux")
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            if len(data) > 5000:
                with open(output_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e:
            if '429' in str(e):
                wait = random.uniform(10, 20)
                print(f"  429 rate limit, waiting {wait:.1f}s...")
                time.sleep(wait)
                continue
            print(f"  Attempt {attempt+1} error: {e}")
            time.sleep(random.uniform(3, 8))
    
    return False

def update_deities_js(code, filename):
    """更新 deities.js 中对应 code 的 image 路径"""
    if not os.path.exists(DEITIES_FILE):
        return
    
    with open(DEITIES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 codeXXX 键
    pattern = rf'("{re.escape(code)}"\s*:\s*\{{[^}}]*?"image"\s*:\s*)"[^"]*"'
    
    def replacer(m):
        prefix = m.group(1)
        return f'{prefix}"generated-images/{filename}"'
    
    new_content = re.sub(pattern, replacer, content)
    
    if new_content != content:
        with open(DEITIES_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Updated deities.js -> {filename}")

def main():
    print("=" * 60)
    print("猎户座(Node 4) 伏羲女娲风格重生成")
    print(f"待重生成: {len(ORION_CODES)} 张")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for idx, code in enumerate(ORION_CODES):
        print(f"\n[{idx+1}/{len(ORION_CODES)}] 处理 code: {code}")
        
        prompt, seed = build_prompt(code, idx)
        filename = f"{code}.webp"
        output_path = os.path.join(IMG_DIR, filename)
        
        # Pollinations 不支持 .webp，存为 .jpg
        jpg_filename = f"{code}.jpg"
        jpg_output_path = os.path.join(IMG_DIR, jpg_filename)
        
        print(f"  Seed: {seed}")
        print(f"  Prompt preview: {prompt[:120]}...")
        
        ok = generate_image(prompt, seed, jpg_output_path)
        
        if ok:
            print(f"  [OK] Saved as {jpg_filename}")
            success_count += 1
            update_deities_js(code, f"generated-images/{jpg_filename}")
            
            # 如果旧的 .webp 存在则删除
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"  Removed old {filename}")
        else:
            print(f"  [FAIL] Could not generate {code}")
            fail_count += 1
        
        # 避免限速
        if idx < len(ORION_CODES) - 1:
            time.sleep(random.uniform(2, 5))
    
    print("\n" + "=" * 60)
    print(f"猎户座重生成完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  总计: {len(ORION_CODES)}")
    print("=" * 60)
    
    # 列出更新后的图片
    print("\n更新后的猎户座图片列表:")
    for code in ORION_CODES:
        jpg_path = os.path.join(IMG_DIR, f"{code}.jpg")
        if os.path.exists(jpg_path):
            size_kb = os.path.getsize(jpg_path) / 1024
            print(f"  {code}.jpg ({size_kb:.0f} KB)")
        else:
            print(f"  {code}.jpg (MISSING!)")

if __name__ == '__main__':
    main()
