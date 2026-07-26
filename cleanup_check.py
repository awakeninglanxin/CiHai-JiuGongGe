"""
慈海九宫格 - 图片清理助手 v1
功能: 扫描并清理 generated-images 目录中的无效图片
  1. 读取 deities.js 中所有需要的code
  2. 扫描 generated-images 中所有 code_XXX.jpg
  3. 找出不在 deities.js 中出现的多余图片
  4. 找出 deities.js 中需要但缺少图片的code
"""
import os
import re
import sys

sys.stdout.reconfigure(line_buffering=True)

project = r'D:\AAA我的文件\慈海九宫格_整合版'
img_dir = os.path.join(project, 'generated-images')
deities_file = os.path.join(project, 'deities.js')

print('=' * 60)
print('慈海九宫格 - 图片清理助手')
print('=' * 60)

# 读取 deities.js 中的code
with open(deities_file, encoding='utf-8') as f:
    js_content = f.read()
js_codes = set(re.findall(r'code:\s*"(\d+)"', js_content))
print(f'\ndeities.js 总code数: {len(js_codes)}')

# 读取 generated-images 中的所有 code_XXX.jpg
img_files = os.listdir(img_dir)
valid_imgs = {}
for f in img_files:
    if f.startswith('code_') and f.endswith('.jpg'):
        # 跳过带timestamp的
        m = re.match(r'^code_(.+)\.jpg$', f)
        if m:
            code = m.group(1)
            if code in js_codes:
                valid_imgs[f] = os.path.join(img_dir, f)

print(f'有效的图片数(在deities.js中存在的): {len(valid_imgs)}')

# 找出多余的图片(不在deities.js中)
extra_imgs = {f: p for f, p in valid_imgs.items() if f.replace('code_', '').replace('.jpg', '') not in js_codes}
# 更准确的做法：提取code前缀，看是否在js_codes中
extra = []
for f in img_files:
    if f.startswith('code_') and f.endswith('.jpg'):
        m = re.match(r'^code_(.+)\.jpg$', f)
        if m:
            code_prefix = m.group(1)
            if code_prefix not in js_codes:
                extra.append(f)
                
print(f'多余的图片(code不在deities.js中): {len(extra)}')
if extra[:5]:
    for f in extra[:5]:
        print(f'  - {f}')

# 找出缺失图片的code
existing_codes = set()
for f in img_files:
    if f.startswith('code_') and f.endswith('.jpg'):
        m = re.match(r'^code_(.+)\.jpg$', f)
        if m:
            existing_codes.add(m.group(1))

missing = js_codes - existing_codes
print(f'\n缺失图片的code数: {len(missing)}')
print(f'部分缺失code: {sorted(missing)[:10]}')

print(f'\n{"=" * 60}')
print('汇总:')
print(f'  deities.js 总code: {len(js_codes)}')
print(f'  已有新风格图片: {len(existing_codes & js_codes)}')
print(f'  缺失图片(需再生成): {len(missing)}')
print(f'  多余图片: {len(extra)}')
print(f'{"=" * 60}')
