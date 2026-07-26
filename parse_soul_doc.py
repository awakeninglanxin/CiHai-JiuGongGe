#!/usr/bin/env python3
"""Parse the docx to extract 十二维+ code list."""
import xml.etree.ElementTree as ET

unpack_dir = r"/tmp/soul_rank_unpack"
doc_path = f"{unpack_dir}/word/document.xml"
tree = ET.parse(doc_path)
root = tree.getroot()

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Extract all paragraph texts preserving order
paras = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    parts = []
    for r in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
        for t in r.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                parts.append(t.text)
    full_text = ''.join(parts).strip()
    if full_text:
        paras.append(full_text)

# Print all unique paragraphs
seen = set()
for p in paras:
    if p not in seen:
        seen.add(p)

print(f"共 {len(seen)} 个唯一段落:\n")
for p in paras:
    if p not in seen:
        print(repr(p))
        seen.add(p)

# Now identify 十二维+ section contents
print("\n\n=== 提取十二维+ section ===")
section1_done = False
sec1_items = []
for p in paras:
    if '先天神圣本源' in p or '十二维' in p:
        section1_done = True
        continue
    if section1_done:
        # Check if new section starts
        if any(kw in p for kw in ['二、', '三、', '四、', '五、', '六、', '七、']):
            break
        # This paragraph might contain a code or separator
        sec1_items.append(p)

print('\n'.join(sec1_items))
