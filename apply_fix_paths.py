"""
最终补丁 - 修复4个路径含/individual/的code
"""
import os
import re
import shutil

DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"

# 重新扫描, 找出带/individual/路径的code
code_map = {}
for f in os.listdir(INDIVIDUAL_DIR):
    if not f.endswith('.jpg'):
        continue
    name = f[:-4]
    parts = name.split('_')
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
    elif len(parts) == 2:
        code = parts[1]
    else:
        continue
    try:
        ts = int(parts[-1])
    except:
        ts = 0
    if code not in code_map or ts > code_map[code][1]:
        code_map[code] = (f, ts)

with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

updated = 0
for code, (fn, ts) in sorted(code_map.items()):
    pattern = r'code:\s*"' + re.escape(code) + r'"[^}]*image:\s*"([^"]*)"'
    m = re.search(pattern, content)
    if m:
        actual = m.group(1)
        expected_path = "generated-images/individual/" + fn
        expected_simple = "generated-images/" + fn
        
        if expected_path not in actual and expected_simple not in actual:
            # 需要替换 - 不用正则, 用字符串操作
            # 找到 image:"..." 并替换
            idx_start = actual.find('"') + 1
            idx_end = actual.rfind('"')
            line_segment = actual
            # 替换
            old_str = 'image:"' + actual + '"'
            new_str = 'image:"' + fn + '"'
            # 在content中精确找到这行
            code_marker = 'code:"' + code + '"'
            line_start = content.find(code_marker)
            if line_start >= 0:
                # 找下一行的image
                line_end = content.find('},', line_start)
                if line_end < 0:
                    line_end = content.find('}', line_start)
                if line_end >= 0:
                    line_text = content[line_start:line_end+1]
                    if expected_path in line_text or expected_simple in line_text:
                        # 用新路径替换
                        line_text = line_text.replace(expected_path, fn)
                        line_text = line_text.replace(expected_simple, fn)
                        # 调整image值
                        img_idx = line_text.find('image:"')
                        if img_idx >= 0:
                            val_start = line_text.index('"', img_idx + 7)
                            val_end = line_text.index('"', val_start + 1)
                            line_text = line_text[:val_start] + fn + line_text[val_end:]
                            content = content[:line_start] + line_text + content[line_end+1:]
                            updated += 1
                            print(f"  修复: code={code} -> {fn}")

with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n共修复 {updated} 个条目")
print("done!")
