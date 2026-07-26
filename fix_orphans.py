#!/usr/bin/env python3
"""
修复 deities.js：删除 function 层闭合后、material 层前的 164 个孤儿重复条目。
"""
import shutil, os, re

ROOT = r"D:\AAA我的文件\慈海九宫格_整合版"
JS = os.path.join(ROOT, "deities.js")
BACKUP = os.path.join(ROOT, "deities.js.bak_fix4")

shutil.copy(JS, BACKUP)
print(f"备份 -> {BACKUP}")

with open(JS, "r", encoding="utf-8") as f:
    content = f.read()

# 找 function layer block 结束位置
func_idx = content.find('{id:"function"')
depth = 0
func_end = -1
for j in range(func_idx, len(content)):
    if content[j] == '{': depth += 1
    elif content[j] == '}':
        depth -= 1
        if depth == 0: func_end = j; break

# 找 material layer start
mat_idx = content.find('{id:"material"')

# 删除 func_end+1 到 mat_idx 之间的所有内容
orphan_len = mat_idx - func_end - 1
print(f"将删除 {orphan_len} 字符的孤儿内容 ({orphan_len // 200} 行左右)")

new_content = content[:func_end+1] + "\n  " + content[mat_idx:]

# 验证
total_codes = len(re.findall(r'code:', new_content))
print(f"修复后 code 总数: {total_codes}")

# 括号平衡
braces=parens=brackets=err=0
in_layers = False
for ch in new_content:
    if 'const LAYERS=[' in new_content[new_content.index(ch) if new_content.index(ch) > 0 else 0:]:
        in_layers = True
for ch in new_content[new_content.find('const LAYERS=['):]:
    if ch == '{': braces += 1
    elif ch == '}': braces -= 1
    elif ch == '[': brackets += 1
    elif ch == ']': brackets -= 1
    elif ch == '(': parens += 1
    elif ch == ')': parens -= 1
    if braces < 0 or parens < 0 or brackets < 0: err += 1

print(f"括号: {{}}={braces}, ()={parens}, []={brackets}, 错误={err}")

with open(JS, "w", encoding="utf-8") as f:
    f.write(new_content)
print("✅ 修复完成！")
