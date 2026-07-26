"""
用最简单可靠的方式替换 deities.js 中的图片路径
"""
import os, re, json

PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")

# 1. Build code -> filename mapping
code_to_file = {}
for fn in os.listdir(INDIVIDUAL_DIR):
    if fn.endswith('.jpg'):
        parts = fn.split('_', 2)  # code_XXX_timestamp.jpg
        if len(parts) >= 2:
            code_to_file[parts[1]] = fn

print(f"Generated files: {len(code_to_file)}")

# 2. Read deities.js
with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 3. For each code, find and replace its image
# The pattern varies: sometimes "image":"...", sometimes ,"image":"..."
# Let's use a callback-based replacement

for code, filename in code_to_file.items():
    # Simpler approach: just string replace for this specific code
    old_image_match = re.search(r'code:"' + re.escape(code) + r'".*?"image":"generated-images/([^"]+)"', content, re.DOTALL)
    if old_image_match:
        old_img = old_image_match.group(1)
        if 'individual/' not in old_img:
            # Replace using exact string match
            old_str = f'"image":"generated-images/{old_img}"'
            new_str = f'"image":"generated-images/individual/{filename}"'
            content = content.replace(old_str, new_str, 1)
            print(f"Updated {code}: {old_img[:40]}... -> {filename}")

# 4. Save
with open(DEITIES_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# 5. Verify
placeholder_refs = 0
for keyword in ['The_Sanqing_Dean', 'Acquired_Child', 'The_Annunaki', 'The_Arcturus', 
                 'The_Yahyel', 'The_Pleiades', 'Gaia_the_living', 'The_Four_Pure',
                 'The_Orion', 'The_Duodecimal', 'The_Sirius', 'The_Essassani',
                 'Innate_Child_star', 'Lost_Maitreya', 'First_Pure_Innate',
                 'Celestial_innate', 'Celestial_Service', 'Innate_Purification']:
    placeholder_refs += content.count(keyword)

individual_refs = content.count('generated-images/individual/')

print(f"\nRemaining placeholders: {placeholder_refs}")
print(f"Individual references: {individual_refs}")

if individual_refs >= 300:
    print("✅ 图片替换成功！")
else:
    print("⚠️  替换不完整，需要进一步处理")
