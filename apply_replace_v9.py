"""
慈海九宫格 - 图片路径替换脚本 v9
功能: 检查 individual 目录中哪些code已有新版本，
      删除旧版（2小时前创建的），更新 deities.js
"""
import os
import sys
import time
from pathlib import Path

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP_DEITIES = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak9"

print("=" * 70)
print("慈海九宫格 - 图片路径替换脚本 v9")
print("=" * 70)

# 1. 扫描现有individual图片
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]
print(f"\n步骤1: 扫描 individual 目录...")
print(f"  总jpg文件: {len(jpg_files)}")

# 提取code -> 最新文件映射
code_to_latest = {}
for f in jpg_files:
    # code_XXX_TIMESTAMP.jpg
    name = f.replace('.jpg', '')
    parts = name.split('_')
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
    elif len(parts) == 2:
        code = parts[1]
    else:
        continue

    filepath = os.path.join(INDIVIDUAL_DIR, f)
    mtime = os.path.getmtime(filepath)
    age_hours = (time.time() - mtime) / 3600

    # 只保留2小时内的新文件
    if age_hours <= 2:
        if code not in code_to_latest or mtime > code_to_latest[code][1]:
            code_to_latest[code] = (f, mtime)

print(f"  2小时内新生成的code: {len(code_to_latest)}")

# 2. 删除旧文件
print(f"\n步骤2: 清理旧版图片...")
removed_count = 0
for f in jpg_files:
    name = f.replace('.jpg', '')
    parts = name.split('_')
    if len(parts) >= 3:
        code_part = '_'.join(parts[1:-1])
    else:
        code_part = parts[1]

    filepath = os.path.join(INDIVIDUAL_DIR, f)
    mtime = os.path.getmtime(filepath)
    age_hours = (time.time() - mtime) / 3600

    if age_hours > 2:
        os.remove(filepath)
        removed_count += 1

print(f"  删除了 {removed_count} 个旧文件")
print(f"  剩余 {len(os.listdir(INDIVIDUAL_DIR))} 个新文件")

# 3. 统计缺失的code
print(f"\n步骤3: 检查缺失code...")
if len(code_to_latest) < 320:
    missing = 320 - len(code_to_latest)
    print(f"  ⚠️ 仍有 {missing} 个code缺少新版图片")
    print(f"  请继续运行 gen_style_upgrade_v8.py 补生成")
else:
    print(f"  ✓ 320个code全部有新版图片!")

# 4. 更新 deities.js
print(f"\n步骤4: 更新 deities.js 图片路径...")

# 读取当前deities.js
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 备份
import shutil
shutil.copy2(DEITIES_JS, BACKUP_DEITIES)
print(f"  已备份: {BACKUP_DEITIES}")

# 逐code替换
updated = 0
for code, (filename, _) in code_to_latest.items():
    # 查找旧的图片路径模式
    # 可能是: "image": "xxx.png" 或 "image":"xxx.png"
    # 需要匹配这个code对应的任意图片
    import re

    # 构造code的正则匹配 —— 在双引号字符串中寻找
    # 旧值可能是:
    # - 默认占位图 Innate_Child_star...png
    # - 旧individual图片
    # - 或其他任何路径
    # 我们找到该code所在的行，然后替换image字段的值

# 按行处理更可靠
lines = content.split('\n')
new_lines = []
for line in lines:
    for code, (filename, _) in code_to_latest.items():
        # 匹配这一行包含这个code且包含image字段
        if f'"code": "{code}"' in line or f'"code":"{code}"' in line:
            # 找到这一行后，需要找后面的 "image": "xxx" 行
            # 暂存，稍后处理
            pass
    new_lines.append(line)

# 换一种方式：按对象块处理
# 整个deities.js是一个大的deities数组，每个条目像:
# { code: "0101", image: "...", ... }
# 或 JSON格式:
# { "code": "0101", "image": "...", ... }

# 用正则匹配每个条目
import re

# 支持两种格式: 有引号key和无引号key
# 匹配一个完整的条目
pattern = r'\{([^}]*?"code"?\s*:\s*"([^"]+)"([^}]*)\}'
matches = list(re.finditer(pattern, content))
print(f"  找到 {len(matches)} 个条目")

updated_entries = 0
for m in matches:
    full_match = m.group(0)
    code = m.group(2)

    if code in code_to_latest:
        new_filename = code_to_latest[code][0]
        # 替换image字段的值
        # 找到 "image": "xxx" 或 image: "xxx"
        img_pattern = r'("image"?\s*:\s*)"[^"]*"'
        new_img = r'\1"' + new_filename + '"'
        new_entry = re.sub(img_pattern, new_img, full_match)

        if new_entry != full_match:
            content = content[:m.start()] + new_entry + content[m.end():]
            updated_entries += 1
            # 修正后续匹配的位置
            # 由于替换可能改变长度，重新扫描
            break  # 从第一个匹配重新开始更安全

# 由于上面的方法有位置偏移问题，改用逐行替换
# 更简单直接的方式:
content_lines = open(DEITIES_JS, 'r', encoding='utf-8').read().split('\n')
final_lines = []
i = 0
while i < len(content_lines):
    line = content_lines[i]
    final_lines.append(line)

    # 检查这一行是否包含 code 定义
    code_match = re.search(r'(?:code|["\']code)["\']?\s*[:=]\s*["\'](\d+)["\']', line)
    if code_match:
        found_code = code_match.group(1)
        # 如果这个code有新的图片，找到对应的image行并替换
        if found_code in code_to_latest:
            new_filename = code_to_latest[found_code][0]
            # 查找接下来的几行是否有image字段
            for j in range(i+1, min(i+5, len(content_lines))):
                img_line = content_lines[j]
                img_match = re.search(r'(?:image|["\']image)["\']?\s*[:=]\s*["\']([^"\']+)["\']', img_line)
                if img_match:
                    # 替换这行的image值
                    old_path = img_match.group(1)
                    if 'individual' not in old_path or 'Innate_Child' in old_path:
                        # 构造替换后的行
                        if '\\"image\\"' in img_line or '"image":' in img_line:
                            # JSON格式
                            new_line = re.sub(
                                r'(["\']image["\']?\s*:\s*["\'])[^"\']+([\'\"])',
                                r'\1' + new_filename + r'\2',
                                img_line
                            )
                        else:
                            # JS格式
                            new_line = re.sub(
                                r'((?:image|["\']image["\']?)\s*[:=]\s*["\'])[^"\']+([\'\"\s,])',
                                r'\1' + new_filename + r'\2',
                                img_line
                            )
                        if new_line != img_line:
                            final_lines[-1] = '\n'.join(final_lines[-1:])
                            final_lines.append(new_line)
                            i = j  # 跳过已处理的行
                            print(f"  更新 code={found_code}: {os.path.basename(old_path)} -> {new_filename}")
                            updated_entries += 1
                        break
    i += 1

# 写回
new_content = '\n'.join(final_lines)
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\n{'=' * 70}")
print(f"完成!")
print(f"  更新了 {updated_entries} 个条目")
print(f"  deities.js 已更新")
print(f"  备份: {BACKUP_DEITIES}")
print(f"{'=' * 70}")
