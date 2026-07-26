#!/usr/bin/env python3
"""
将十二维+的神祇条目从 creation 层迁移到 origin 层。

规则来自《灵魂积分排序.docx》：
- origin层（十二维+）包含最高维度代码：如033393、0123、0161181、033396
- creation层（九至十一维）包含创世管理者
- 判断依据：这些 code 在 deities.js 中当前处于 creation 层

迁移策略：读取 origin 和 creation 层内容，将属于 origin 的 code 从 creation 中移除并插入 origin。
"""
import re, os, json

ROOT = r"D:\AAA我的文件\慈海九宫格_整合版"
JS = os.path.join(ROOT, "deities.js")
BACKUP = os.path.join(ROOT, "deities.js.bak_before_origin_migrate")

with open(JS, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract ALL entries with their current layer
def get_layer_entry(content, layer_id):
    idx = content.find('{id:"' + layer_id + '"')
    if idx < 0: return [], -1, -1
    dstart = content.find('[', idx)
    depth = 0; dent = -1; started = False
    for j in range(dstart, len(content)):
        if content[j] == '[': depth += 1; started = True
        elif content[j] == ']':
            depth -= 1
            if started and depth == 0:
                dent = j; break
    block = content[dstart+1:dent] if dent > 0 else ''
    # Extract full entry (code + everything until next {code: or end)
    pattern = r'\{code:"([^"]+)",name:"([^"]+)",role:"([^"]+)",image:"([^"]+)",node:(\d+),races:(\[.*?\])\}'
    matches = re.findall(pattern, block)
    entries = []
    for match in matches:
        code, name, role, image, node_str, races = match
        nodes = [int(n.strip('"')) for n in re.findall(r'"([^"]+)"', races)]
        entries.append({
            'code': code,
            'name': name,
            'role': role,
            'image': image,
            'node': int(node_str),
            'races': nodes,
        })
    return entries, dstart, dent

origin_entries, o_start, o_end = get_layer_entry(content, 'origin')
creation_entries, c_start, c_end = get_layer_entry(content, 'creation')

print(f"origin层条目数: {len(origin_entries)}")
print(f"creation层条目数: {len(creation_entries)}")
print(f"\norigin层当前code: {[e['code'] for e in origin_entries]}")
print(f"\ncreation层所有code: {[e['code'] for e in creation_entries]}")

# Now we need to determine which creation entries belong to origin (十二维+)
# Based on the docx: 0123, 033393, 0161181, 033396 etc.
# Pattern: codes that are extremely short/unique/high-significance codes

# Let's also check what's in the docx classification
# 0123 (最强心神) -> origin (十二维+)
# 033393 (太上老君) -> origin (十二维+)
# 0161181 (玉皇) -> origin (十二维+) - likely
# 033396 -> likely origin too based on user mention

# Heuristic: origin layer codes appear to be very short, special significance codes
# Let's look at creation entries to find potential origin candidates
# They seem to be: 0xxx (very short, high-significance) codes, especially 0123, 0333xx, 0161181

origin_candidates = set()
for e in creation_entries:
    code = e['code']
    # Heuristic: ultra-short codes (<=3 significant digits) OR very distinctive origin codes
    # Known from docx: 0123, 033393, 0161181
    # But wait, there are 51 creation entries and most are standard 9-11D
    
    # Check if code appears in origin docx list context
    # From the docx: 033393, 0123, 0161181 are definitely origin
    # Others starting with 0xxxxx might be mixed
    
    # Let's identify by being in the first few (high significance) creation codes
    # Look at creation entry order - first ones are highest rank
    pass

# More robust approach: identify creation entries that match the 十二维+ pattern
# These should be codes like:
# - Starting with 0 (but NOT typical 先天童子)
# - Very specific codes: 0123, 033393, 0161181, 033396
# These are "origin level" codes because they represent primal/primordial entities

# Let's use known origin-level code patterns from the docx
origin_codes_from_docx = ['0123', '033393', '0161181', '033396']

# Also look for other likely origin-level codes in creation
# Check if any creation entry has a very distinctive pattern
for e in creation_entries:
    code = e['code']
    if code in origin_codes_from_docx:
        origin_candidates.add(code)

print(f"\n确认需要移到origin的code: {origin_candidates}")

# Now actually modify the file
# We need to remove these entries from creation array and add them to origin array
# This is more complex than simple text replacement - let's do it carefully

# Read the full creation block between dstart+1 and dent-1
creation_block = content[c_start:c_end+1]  # includes the [ ] and all entries
origin_block = content[o_start:o_end+1]

# Use regex to find and extract individual entries
entry_pattern = r'(\s*\{code:"[^"]+",name:"[^"]+",role:"[^"]+",image:"[^"]+",node:\d+,races:\[.*?\]\},?)'

# Parse creation entries into lines
creation_entries_raw = re.findall(entry_pattern, creation_block)
origin_entries_raw = []

# Find origin entries raw too
if o_start > 0 and o_end > 0:
    # origin's deities:[ ] pattern
    origin_deity_start = content.find('[', o_start)
    origin_deity_end = content.rfind(']', o_start, o_end)
    origin_entries_raw = re.findall(entry_pattern, content[origin_deity_start+1:origin_deity_end])

print(f"origin_entries_raw count: {len(origin_entries_raw)}")

# Now filter out origin candidates from creation
new_creation_entries_raw = []
for raw in creation_entries_raw:
    code_match = re.search(r'code:"([^"]+)"', raw)
    if code_match and code_match.group(1) in origin_candidates:
        print(f"  Removing from creation: {code_match.group(1)}")
        continue
    new_creation_entries_raw.append(raw)

print(f"\n移动后creation条目数: {len(new_creation_entries_raw)}")
print(f"预期origin条目数: {len(origin_entries_raw) + len(origin_candidates)}")

# Build new content
# Replace creation block
new_creation_block = '[\n' + '\n'.join(new_creation_entries_raw) + '\n  ]'
# Add origin candidates before the closing bracket of creation
for raw in creation_entries_raw:
    code_match = re.search(r'code:"([^"]+)"', raw)
    if code_match and code_match.group(1) in origin_candidates:
        # Extract the index within creation_entries_raw where this raw was located
        # to know position for insertion into new origin list
        idx = creation_entries_raw.index(raw)
        print(f"  Entry at index {idx}: {code_match.group(1)}")

# Better approach: rebuild entire LAYERS array by extracting segments
# Find the positions in the original content around each layer
# Then reconstruct

# Let's do a simpler approach: use string replacement
# Find origin layer opening and creation layer opening/end

# Origin layer start marker
origin_open_pos = content.find('{id:"origin"', o_start)
# Origin layer deities array
origin_deity_start_pos = content.find('[', origin_open_pos)
# After 'deities:[', find closing ']' for origin
# Since origin is currently empty: 'deities:[\n  ]}'
origin_close_pos = content.find('}', origin_deity_start_pos)
# This gives us the full origin layer block

# Find creation layer
creation_open_pos = content.find('{id:"creation"', c_start)
# Creation layer deities array start
creation_deity_start_pos = content.find('[', creation_open_pos)
# Find the end of creation layer
creation_layer_end = content.find('{id:"innate"', creation_open_pos)

print(f"\norigin_deity_start_pos: {origin_deity_start_pos}")
print(f"origin_close_pos: {origin_close_pos}")
print(f"creation_deity_start_pos: {creation_deity_start_pos}")
print(f"creation_layer_end: {creation_layer_end}")

# Now build new content
# Part 1: Before origin layer (unchanged)
part1 = content[:origin_deity_start_pos + 1]  # up to '[', including '['
# Part 2: New origin deities (origin + moved entries)
new_origin_deities = []
for raw in origin_entries_raw:
    new_origin_deities.append(raw)
for raw in creation_entries_raw:
    code_match = re.search(r'code:"([^"]+)"', raw)
    if code_match and code_match.group(1) in origin_candidates:
        new_origin_deities.append(raw)

new_origin_section = '\n  ' + ',\n  '.join(new_origin_deities) + '\n  ]'
# Part 3: Between origin close and creation open (unchanged)
part3_start = origin_close_pos + 1
part3 = content[part3_start:creation_deity_start_pos]
# Part 4: New creation deities
new_creation_section = '\n  ' + ',\n  '.join(new_creation_entries_raw) + '\n  ]'
# Part 5: After creation layer (unchanged)
part5 = content[creation_layer_end:]

# Reconstruct content
new_content = part1 + new_origin_section + part3 + new_creation_section + part5

# Validate entry counts
print(f"\n=== Validating ===")
final_origin, _, _ = get_layer_entry(new_content, 'origin')
final_creation, _, _ = get_layer_entry(new_content, 'creation')
print(f"origin层最终条目数: {len(final_origin)}")
print(f"creation层最终条目数: {len(final_creation)}")

if len(final_origin) == len(origin_entries_raw) + len(origin_candidates):
    if len(final_creation) == len(creation_entries_raw) - len(origin_candidates):
        print("✅ 验证通过!")
        # Write new content
        with open(JS, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ deities.js 已更新")
        
        # Verify file size
        file_size = os.path.getsize(JS)
        print(f"文件大小: {file_size} bytes")
    else:
        print("ERROR: creation layer count mismatch")
else:
    print("ERROR: origin layer count mismatch")

# Save backup
if not os.path.exists(BACKUP):
    import shutil
    shutil.copy(JS, BACKUP + '.after_migration')
    print(f"备份后: {BACKUP}.after_migration")
