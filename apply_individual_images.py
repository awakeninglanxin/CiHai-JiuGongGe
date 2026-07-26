"""
将 individual/ 下的图片复制到 generated-images/ 根目录，并更新 deities.js 中的 image 路径
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
IMAGES_DIR = os.path.join(PROJECT_DIR, "generated-images")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")

# Load jobs
with open(os.path.join(INDIVIDUAL_DIR, "results.json"), "r", encoding="utf-8") as f:
    results = json.load(f)

success_codes = set(results['success'])
fail_codes = set(results['failed'])

# Scan individual dir for jpg files
existing_files = set()
for fn in os.listdir(INDIVIDUAL_DIR):
    if fn.endswith('.jpg'):
        code = fn.split('_')[1]
        existing_files.add(code)

# Find which codes have both generated file AND were in success list
generated = existing_files.intersection(success_codes)
not_generated = success_codes - existing_files
still_failed = fail_codes - existing_files

print(f"Success codes in results: {len(success_codes)}")
print(f"Actually generated files: {len(generated)}")
print(f"Missing files (success but no file): {len(not_generated)}")
print(f"Still failed: {len(still_failed)}")

# Count by node for generated
node_dist = {}
for code in generated:
    for item in results['success']:
        if item == code:
            break
    # We need to look up node from original jobs
    # Actually let's just use the results file which has success codes
    
# Read deities.js
with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    js_content = f.read()

# Build replacement map: code -> new_image_path
replacement_map = {}
for code in generated:
    # Find the matching file in individual dir
    for fn in os.listdir(INDIVIDUAL_DIR):
        if fn.startswith(f"code_{code}_") and fn.endswith('.jpg'):
            old_placeholder = f"generated-images/Innate_Child_star_beings__lumi_2026-07-10T04-41-03.png"
            new_path = f"generated-images/individual/{fn}"
            replacement_map[code] = new_path
            break

print(f"\nCodes to update in deities.js: {len(replacement_map)}")

# Now do the replacements in deities.js
# Pattern: code:"XXXX" and image:"generated-images/Innate_Child_..." or similar placeholder
# We need to replace the image for specific codes

import re

def replace_image_for_code(match):
    full = match.group(0)
    code = match.group(1)
    if code in replacement_map:
        # Replace the image part
        old_img = match.group(2)
        new_img = replacement_map[code]
        return full.replace(f'image:"{old_img}"', f'image:"{new_img}"')
    return full

# Match {code:"...", ..., image:"generated-images/Innate_Child..."}
# But also match any placeholder image
# Strategy: find all deity entries, and for those with codes in replacement_map, update image

# More precise: find each deity object and replace its image field
deity_pattern = r'(\{code:"([^"]+)".*?)"image":"generated-images/Innate_Child[^"]*"'

# Check how many placeholders exist
placeholder_count = len(re.findall(deity_pattern, js_content, re.DOTALL))
print(f"Placeholders found in deities.js: {placeholder_count}")

# Now replace
def replace_deity_image(match):
    prefix = match.group(1)
    code = match.group(2)
    if code in replacement_map:
        return prefix + f'"image":"{replacement_map[code]}"'
    return match.group(0)

new_js_content = re.sub(
    r'(\{code:"([^"]+)".*?)"image":"generated-images/([^"]*(?:Innate_Child|Sanqing_Dean|Annunaki|Arcturus|Yahyel|Pleiades|Gaia|Four_Pure|Orion|Duodecimal|Sirius|Essassani)[^"]*)"',
    replace_deity_image,
    js_content,
    flags=re.DOTALL
)

if new_js_content != js_content:
    with open(DEITIES_FILE, "w", encoding="utf-8") as f:
        f.write(new_js_content)
    print("✅ deities.js updated!")
else:
    print("❌ No replacements made - checking regex pattern...")

# Check remaining placeholders
remaining = len(re.findall(r"Innate_Child_star_beings", new_js_content))
print(f"Remaining placeholder images: {remaining}")

# Also replace other group placeholders (non-Innate_Child)
for code, path in replacement_map.items():
    old_patterns = [
        f'"image":"generated-images/The_Sanqing_Dean__',
        f'"image":"generated-images/Acquired_Child_',
        f'"image":"generated-images/The_Annunaki_',
        f'"image":"generated-images/The_Arcturus_',
        f'"image":"generated-images/The_Yahyel_',
        f'"image":"generated-images/The_Pleiades_',
        f'"image":"generated-images/Gaia_',
        f'"image":"generated-images/The_Four_Pure_',
        f'"image":"generated-images/The_Orion_',
        f'"image":"generated-images/The_Duodecimal_',
        f'"image":"generated-images/The_Sirius_',
        f'"image":"generated-images/The_Essassani_',
        f'"image":"generated-images/code_0325_',
        f'"image":"generated-images/Innate_Purification_Low_',
        f'"image":"generated-images/code_0336_',
        f'"image":"generated-images/code_0347_',
        f'"image":"generated-images/code_0358_',
        f'"image":"generated-images/Lost_Maitreya_',
        f'"image":"generated-images/First_Pure_Innate_',
        f'"image":"generated-images/Celestial_Service_',
        f'"image":"generated-images/Celestial_innate_',
        f'"image":"generated-images/code_0369_',
    ]
    for pat in old_patterns:
        if f'{code}",role:' in js_content:
            # This code exists, check if still pointing to old placeholder
            idx = new_js_content.find(f'code:"{code}"')
            if idx >= 0:
                snippet = new_js_content[idx:idx+200]
                if pat.split('"')[1] in snippet:
                    print(f"  Found {pat.split('/')[-1][:40]}... still for {code}")

# Count unique image values now
unique_images = set(re.findall(r'"image":"generated-images/(?:individual/)?[^"]*"', new_js_content))
print(f"\nUnique image entries in deities.js: {len(unique_images)}")

# Save report
report = {
    'total_codes_in_results': len(results['success']) + len(results['failed']),
    'successfully_generated': len(generated),
    'missing_files': len(not_generated),
    'still_failed': len(still_failed),
    'deities_updated': len(replacement_map),
    'updated_at': datetime.now().isoformat()
}

report_path = os.path.join(INDIVIDUAL_DIR, "final_report.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n📊 Final Report:")
for k, v in report.items():
    print(f"  {k}: {v}")
print(f"\nReport saved: {report_path}")
