"""
最简单可靠的方式：直接替换 deities.js 中每个 placeholder 图片名
每个 placeholder 被多个 code 共用，需要把它们逐个替换为 individual 图片
"""
import os, re, json

PROJECT_DIR = r"D:\AAA我的文件\慈海九宫格_整合版"
INDIVIDUAL_DIR = os.path.join(PROJECT_DIR, "generated-images", "individual")
DEITIES_FILE = os.path.join(PROJECT_DIR, "deities.js")

# 1. Build code -> filename mapping
code_to_file = {}
for fn in os.listdir(INDIVIDUAL_DIR):
    if fn.endswith('.jpg'):
        parts = fn.split('_', 2)
        if len(parts) >= 2:
            code_to_file[parts[1]] = fn

print(f"Generated files: {len(code_to_file)}")

# Read deities.js
with open(DEITIES_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Load results to know which codes came from which group
with open(os.path.join(INDIVIDUAL_DIR, "results.json"), "r") as f:
    results = json.load(f)

# 3. For each code in individual/, do a direct string replacement in deities.js
updated = 0
failed = 0
for code, filename in code_to_file.items():
    new_img = f"generated-images/individual/{filename}"
    
    # Find and replace in deities.js
    # The pattern is always: image:"generated-images/SomeName.png"
    # We need to replace ONLY for this specific code
    
    # Strategy: find the line containing this code and replace its image
    line_pattern = r'(^\s*\{code:"' + re.escape(code) + r'"[^"]*"image":)"generated-images/[^"]+"'
    match = re.search(line_pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_image = match.group(2)
        # Verify old_image is a placeholder (not already an individual image)
        if old_image.startswith("The_") or old_image.startswith("Acquired_") or old_image.startswith("Gaia_") or old_image.startswith("Innate_") or code in ['0202', '0213', '0224', '0246']:
            old_exact = f'"image":"{old_image}"'
            new_exact = f'"image":"{new_img}"'
            content = content.replace(old_exact, new_exact, 1)
            updated += 1
        else:
            print(f"  Skipping {code} (already has correct image or non-placeholder): {old_image[:50]}")
            failed += 1
    else:
        print(f"  NOT FOUND: {code}")
        failed += 1

print(f"\nUpdated: {updated}")
print(f"Failed/Skipped: {failed}")

# 4. Save
with open(DEITIES_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# 5. Verify
individual_count = content.count('generated-images/individual/')
print(f"\nEntries with individual/: {individual_count}")

# Check a few specific codes
sample_codes = ['2419101', '0202', '0325', '0336', '111121', '23178']
for c in sample_codes:
    idx = content.find(f'code:"{c}"')
    if idx >= 0:
        snippet = content[idx:idx+150]
        img_match = re.search(r'image:"([^"]+)"', snippet)
        if img_match:
            img = img_match.group(1)
            status = "✅" if "individual/" in img else "❌"
            print(f"  {status} {c}: {img[:50]}...")
