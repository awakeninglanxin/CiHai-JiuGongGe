"""
终极批量修复: 把 deities.js 中所有 generated-images/individual/ 替换为 generated-images/
"""
import os
import shutil

DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = DEITIES_JS + ".bak15"

shutil.copy2(DEITIES_JS, BACKUP)
print(f"备份: {BACKUP}")

with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计
old_count = content.count("generated-images/individual/")
print(f"待替换数: {old_count}")

# 替换
new_content = content.replace("generated-images/individual/", "generated-images/")

print(f"实际替换: {old_count - new_content.count("generated-images/individual/")} 处")

with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("done!")
