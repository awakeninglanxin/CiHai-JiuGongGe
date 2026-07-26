"""
直接更新 deities.js — 对每个有新生成的code，替换其image字段
"""
import os
import json
import re

PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")

# 1. Build code -> filename mapping from individual dir
code_to_file = {}
for fn in os.listdir(INDIVIDUAL_DIR):
    if fn.endswith('.jpg'):
        parts = fn.split('_')
        if len(parts) >= 2:
            code = parts[1]
            code_to_file[code] = fn

print(f"Codes with generated files: {len(code_to_file)}")

# 2. Read deities.js
with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 3. Find all deity entries that have placeholder images
# We need to replace: image:"generated-images/XXX.png" → image:"generated-images/individual/code_XXX_timestamp.jpg"
# for codes that are in code_to_file

# Strategy: find each {code:"XXX"...image:"generated-images/PLACEHOLDER..."} and replace

replacements_made = 0
for code, filename in code_to_file.items():
    # Find the code entry in deities.js
    # Pattern: {code:"XXXX",...,image:"generated-images/OLD_NAME..."}
    pattern = r'(\{code:"' + re.escape(code) + r'".*?"image":)"generated-images/([^"]*?"(?:png|jpg)"(?=[,}]).*)'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        old_value = match.group(2)
        # Only replace if it's a placeholder (not already an individual image)
        if 'individual/' not in old_value:
            new_value = f"generated-images/individual/{filename}"
            content = content.replace(
                f'"image":"{old_value}"',
                f'"image":"{new_value}"',
                1  # only first occurrence of this exact string
            )
            replacements_made += 1

print(f"Replacements made: {replacements_made}")

# 4. Verify
placeholder_count = content.count('The_Sanqing_Dean')
placeholder_count += content.count('Acquired_Child')
placeholder_count += content.count('The_Annunaki')
placeholder_count += content.count('The_Arcturus')
placeholder_count += content.count('The_Yahyel')
placeholder_count += content.count('The_Pleiades')
placeholder_count += content.count('Gaia_the_living')
placeholder_count += content.count('The_Four_Pure')
placeholder_count += content.count('The_Orion')
placeholder_count += content.count('The_Duodecimal')
placeholder_count += content.count('The_Sirius')
placeholder_count += content.count('The_Essassani')
placeholder_count += content.count('Innate_Child_star')

print(f"Remaining placeholder references: {placeholder_count}")

individual_count = content.count('generated-images/individual/')
print(f"Entries now using individual/: {individual_count}")

# 5. Save backup and updated file
backup_file = DEITIES_FILE + '.bak5'
import shutil
shutil.copy2(DEITIES_FILE, backup_file)
print(f"Backup saved: {backup_file}")

with open(DEITIES_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ deities.js updated!")

# 6. Check if any codes still have non-individual placeholders
# by scanning for codes that should have been replaced but weren't
import json
with open(os.path.join(INDIVIDUAL_DIR, "results.json"), "r") as f:
    results = json.load(f)

success_codes = set(results['success'])
updated_codes = set(code_to_file.keys())
missing = success_codes - updated_codes

if missing:
    print(f"\n⚠️  Still missing {len(missing)} codes (not in code_to_file):")
    for c in sorted(missing)[:10]:
        print(f"   {c}")
else:
    print(f"\n✅ All {len(success_codes)} success codes now have files!")

# Also check for any remaining placeholders that SHOULD have individual images
remaining_placeholders = []
code_entries = re.findall(r'code:"([^"]+)".*?image:"generated-images/([^"]+)"', content, re.DOTALL)
for code, img in code_entries:
    if code in success_codes and 'individual/' not in img:
        remaining_placeholders.append((code, img))

if remaining_placeholders:
    print(f"\n⚠️  {len(remaining_placeholders)} codes still have placeholder images:")
    for c, i in remaining_placeholders[:10]:
        print(f"   {c}: {i[:50]}")
else:
    print("\n✅ All success codes now have individual images!")
