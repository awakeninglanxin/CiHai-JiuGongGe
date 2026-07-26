"""
终极简单方案：逐行读取 deities.js，对每行匹配到 code 的行直接替换 image
"""
import os, re

PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")

# Build code -> filename mapping
code_to_file = {}
for fn in os.listdir(INDIVIDUAL_DIR):
    if fn.endswith('.jpg'):
        parts = fn.split('_', 2)
        if len(parts) >= 2:
            code_to_file[parts[1]] = fn

print(f"Generated files: {len(code_to_file)}")

with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

updated = 0
processed = 0
for i in range(len(lines)):
    line = lines[i]
    # Find code in this line
    code_match = re.search(r'code:"([^"]+)"', line)
    if code_match:
        code = code_match.group(1)
        if code in code_to_file:
            old_img_match = re.search(r'image:"generated-images/([^"]+)"', line)
            if old_img_match:
                old_img = old_img_match.group(1)
                # Only replace placeholder images
                if old_img.startswith("The_") or old_img.startswith("Acquired_") or old_img.startswith("Gaia_") or old_img.startswith("Innate_") or old_img.startswith("Lost_") or old_img.startswith("First_") or old_img.startswith("Celestial_") or old_img.startswith("Fourth_") or old_img.startswith("New_") or old_img.startswith("Water_") or old_img.startswith("Earth_") or old_img.startswith("Nameless_") or old_img.startswith("Yiqing_") or old_img.startswith("Erqing_") or old_img.startswith("Swaddled_") or old_img.startswith("Dao_") or old_img.startswith("Demolition_") or old_img.startswith("Sun_Wukong") or old_img.startswith("Tang_") or old_img.startswith("Mahakala") or old_img.startswith("Thoth_") or old_img.startswith("Xiantian") or old_img.startswith("Jiutian") or old_img.startswith("Nezha") or old_img.startswith("Orion_") or old_img.startswith("Xi_Wangmu") or old_img.startswith("Sanqing_") or old_img.startswith("Wealth_") or old_img.startswith("Jieyin") or old_img.startswith("Shaanxi") or old_img.startswith("Tang_") or old_img.startswith("Nameless") or old_img.startswith("Water_Wealth") or old_img.startswith("Earth_Wealth"):
                    new_img = f"generated-images/individual/{code_to_file[code]}"
                    lines[i] = line.replace(f'image:"generated-images/{old_img}"', f'image:"{new_img}"', 1)
                    updated += 1
                elif "individual/" not in old_img:
                    # Unknown placeholder pattern
                    new_img = f"generated-images/individual/{code_to_file[code]}"
                    lines[i] = line.replace(f'image:"generated-images/{old_img}"', f'image:"{new_img}"', 1)
                    updated += 1

print(f"Updated: {updated}")

with open(DEITIES_FILE, "w", encoding="utf-8") as f:
    f.writelines(lines)

# Verify
with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    content = f.read()

individual_count = content.count('generated-images/individual/')
print(f"individual/ entries: {individual_count}")

# Sample verification
samples = ['2419101', '0202', '0325', '111121', '23178', '0101']
for c in samples:
    idx = content.find(f'code:"{c}"')
    if idx >= 0:
        snippet = content[idx:idx+180]
        img = re.search(r'image:"([^"]+)"', snippet)
        if img:
            val = img.group(1)
            status = "✅" if "individual/" in val else "❌"
            print(f"  {status} {c}: {val[:55]}")
