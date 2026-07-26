import re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "generated-images")
JS = os.path.join(ROOT, "deities.js")

content = open(JS, "r", encoding="utf-8").read()

# 找所有 restored 引用
restored_refs = re.findall(r'image:"generated-images/(code_\d+_v1restored\.jpg)"', content)
print(f"restored 引用总数: {len(restored_refs)}")

converted = 0
skipped = 0
for restored_name in set(restored_refs):
    code = restored_name.replace("_v1restored.jpg", "").replace("code_", "")
    normal_name = f"code_{code}.jpg"
    normal_path = os.path.join(IMG_DIR, normal_name)
    if os.path.exists(normal_path) and os.path.getsize(normal_path) > 5000:
        # 安全替换：只替这个具体文件名
        before = content
        content = content.replace(f'generated-images/{restored_name}', f'generated-images/{normal_name}')
        if content != before:
            converted += 1
        else:
            skipped += 1
    else:
        skipped += 1

print(f"已转换 restored->normal: {converted}")
print(f"跳过(无普通版): {skipped}")

if converted > 0:
    # 备份
    backup = JS + ".bak_phaseA"
    if not os.path.exists(backup):
        open(backup, "w", encoding="utf-8").write(open(JS, "r", encoding="utf-8").read())
    open(JS, "w", encoding="utf-8").write(content)
    print(f"已写入 deities.js（备份: {os.path.basename(backup)}）")
else:
    print("无需修改")
