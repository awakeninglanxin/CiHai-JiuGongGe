#!/usr/bin/env python3
"""
修复 deities.js：删除 function 层闭合 } 之后、material 层之前的孤儿重复条目。
"""
import os, re, shutil

ROOT = r"D:\AAA我的文件\慈海九宫格_整合版"
JS = os.path.join(ROOT, "deities.js")
BACKUP = os.path.join(ROOT, "deities.js.bak_fix2")

if not os.path.exists(BACKUP):
    shutil.copy(JS, BACKUP)
    print(f"备份 -> {BACKUP}")

with open(JS, "r", encoding="utf-8") as f:
    content = f.read()

# 找 function layer block 的结束 }
func_idx = content.find('{id:"function"')
assert func_idx >= 0
depth = 0
func_end = -1
for j in range(func_idx, len(content)):
    if content[j] == '{': depth += 1
    elif content[j] == '}':
        depth -= 1
        if depth == 0:
            func_end = j; break

print(f"function layer block end: pos {func_end}")

mat_idx = content.find('{id:"material"')
assert mat_idx >= 0

# 提取孤儿区域
orphan_zone = content[func_end+1:mat_idx]
# 清理 leading whitespace + trailing comma/newline before {id:"material"
start_skip = 0
while start_skip < len(orphan_zone) and orphan_zone[start_skip] in ' \t\n\r':
    start_skip += 1

# 如果 func_end+1 位置是 ',' 或空白，需要跳过
print(f"func_end后首个非空白字符: {repr(orphan_zone[start_skip:start_skip+5]) if start_skip < len(orphan_zone) else 'EOF'}")

# 删除孤儿区域：保留 func_end+1（即 }），然后直接接 material
new_content = content[:func_end+1] + "\n  " + content[mat_idx:]

entry_count = len(re.findall(r'code:', new_content))
print(f"修复后总 code 数: {entry_count}")

# 括号平衡检查
braces=0; parens=0; brackets=0; err=0
for ch in new_content[new_content.find('const LAYERS=['):]:
    if ch=='{': braces+=1
    elif ch=='}': braces-=1
    elif ch=='(': parens+=1
    elif ch==')': parens-=1
    elif ch=='[': brackets+=1
    elif ch==']': brackets-=1
    if braces<0 or parens<0 or brackets<0:
        err+=1
print(f"括号平衡: braces={braces}, parens={parens}, brackets={brackets}, errors={err}")

if err > 0 or entry_count != 963:
    print("ERROR! 回滚...")
    shutil.copy(BACKUP, JS)
else:
    with open(JS, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("\n✅ deities.js 已修复！")
