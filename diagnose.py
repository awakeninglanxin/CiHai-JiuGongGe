import re, os, json

ROOT = r"D:\AAA我的文件\慈海九宫格_整合版"
js = os.path.join(ROOT, "deities.js")
html = os.path.join(ROOT, "game-roster.html")

with open(js, 'r', encoding='utf-8') as f:
    content = f.read()

# Count ALL {code:"..." entries
all_entries = re.findall(r'\{code:"[^"]+",name:"[^"]*",role:"[^"]*",image:"generated-images/[^"]*",node:\d+,\s*races:(?:\[.*?\]|\w+)', content, re.DOTALL)
print(f"=== deities.js 全文件统计 ===")
print(f"总条目数: {len(all_entries)}")

# Extract LAYERS structure precisely
layers_found = ['origin','creation','innate','elite','function','material']
total = 0
for layer_name in layers_found:
    # Find the layer opening
    pattern = re.compile(
        rf'{{\s*id\s*:\s*"{layer_name}"[^}}]*deities\s*:\s*\[(.*?)(?=\n\s*\}},|\n\s*\]\}})',
        re.DOTALL
    )
    m = pattern.search(content)
    if not m:
        print(f"\n{layer_name}: ❌ 未找到层结构")
        continue

    inner = m.group(1)
    entries = re.findall(r'\{code:"([^"]+)"', inner)
    total += len(entries)
    print(f"\n{layer_name}: {len(entries)} 个条目")
    if entries:
        # Check first and last entry images exist
        for code in entries[:2]:
            img = f"generated-images/code_{code}.jpg"
            exists = os.path.exists(os.path.join(ROOT, img))
            print(f"  code={code} image_exists={exists}")
        if len(entries) > 2:
            print(f"  ... ({len(entries)-4} more)")
        for code in entries[-2:]:
            img = f"generated-images/code_{code}.jpg"
            exists = os.path.exists(os.path.join(ROOT, img))
            print(f"  code={code} image_exists={exists}")

print(f"\n=== 汇总: {total} 个条目 ===")

# Check JS syntax - try parsing with minimal approach
# Look for window.LAYERS assignment
ll_start = content.find("window.LAYERS=")
print(f"\nwindow.LAYERS= 出现在位置: {ll_start}")
if ll_start >= 0:
    snippet = content[ll_start:ll_start+100]
    print(f"窗口内容: {snippet[:100]}")

# Also check: are there any syntax errors before window.LAYERS?
# Try to find unbalanced braces between LAYERS=[ and window.LAYERS=
start = content.find("const LAYERS=[")
end = ll_start if ll_start > 0 else len(content)
substr = content[start:end]

braces = 0
parens = 0
brackets = 0
errors = []
for i, ch in enumerate(substr):
    if ch == '{': braces += 1
    elif ch == '}': braces -= 1
    elif ch == '(': parens += 1
    elif ch == ')': parens -= 1
    elif ch == '[': brackets += 1
    elif ch == ']': brackets -= 1

    if braces < 0:
        errors.append(f"extra '}}' at pos {i}")
        braces = 0
    if parens < 0:
        errors.append(f"extra ')' at pos {i}")
        parens = 0
    if brackets < 0:
        errors.append(f"extra ']' at pos {i}")
        brackets = 0

print(f"\n=== 括号平衡检查 ===")
print(f"最终 braces: {braces}, parens: {parens}, brackets: {brackets}")
if errors:
    for e in errors[:10]:
        print(f"  ERROR: {e}")
else:
    print("✅ 所有括号/花括号/方括号平衡")

# Check race data in BASHAR_RACES
rr_start = content.find("BASHAR_RACES")
print(f"\n=== BASHAR_RACES 检查 ===")
print(f"BASHAR_RACES 位置: {rr_start}")
