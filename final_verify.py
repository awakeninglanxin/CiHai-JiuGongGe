import re, os, json

content = open('deities.js', 'r', encoding='utf-8').read()
# 跨字段匹配：code 后任意字符直到 image
entries = re.findall(r'code:"(\d+)".*?image:"generated-images/(code_\d+\.jpg)"', content, re.DOTALL)
print(f'deities.js 中总条目: {len(entries)}')

missing = []
badsize = []
for code, img in entries:
    fp = os.path.join('generated-images', img)
    if not os.path.exists(fp):
        missing.append(code)
    elif os.path.getsize(fp) < 5000:
        badsize.append(code)

print(f'缺失图片: {len(missing)}')
print(f'过小图片: {len(badsize)}')

if missing:
    print('缺失列表(前20):', missing[:20])
if badsize:
    print('过小列表(前20):', badsize[:20])

if not missing and not badsize:
    print('✅ 所有图片完整无缺！')

# 修正进度文件：把实际已完成的移出failed
prog = json.load(open('final_master_fix_progress.json', 'r', encoding='utf-8'))
fixed = 0
for code in list(prog['failed']):
    fp = os.path.join('generated-images', f'code_{code}.jpg')
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        prog['failed'].remove(code)
        if code not in prog['done']:
            prog['done'].append(code)
        fixed += 1
json.dump(prog, open('final_master_fix_progress.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'\n进度文件已修正: 从failed移出 {fixed} 个实际已完成的code')
print(f'最终: done={len(prog["done"])} failed={len(prog["failed"])}')
