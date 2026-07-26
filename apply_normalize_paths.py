"""
终极替换 v14 - 把individual/xxx 全部搬到 generated-images/xxx
deities.js 中有大量路径为 generated-images/individual/code_XXX_X.jpg
应改为 generated-images/code_XXX_X.jpg (去掉/individual)
"""
import os
import re

DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak14"

import shutil
shutil.copy2(DEITIES_JS, BACKUP)

with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换: generated-images/individual/code_XXX.jpg -> generated-images/code_XXX.jpg
# 同时确保文件存在于 individual/ 目录
INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
individual_files = set(os.listdir(INDIVIDUAL_DIR))

fixed = 0
for f in individual_files:
    if not f.endswith('.jpg'):
        continue
    # 旧路径
    old_path = f"generated-images/individual/{f}"
    # 新路径
    new_path = f"generated-images/{f}"
    
    # 在content中查找 old_path 并替换
    count = content.count(old_path)
    if count > 0:
        content = content.replace(old_path, new_path)
        fixed += count

print(f"替换了 {fixed} 处路径引用")
print(f"从: generated-images/individual/xxx -> generated-images/xxx")

with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(content)

print("done!")
