#!/usr/bin/env python3
"""
correct_fix.py - 正确修复 deities.js 层级
"""

import re
import shutil
import os

JS_FILE = "deities.js"
BACKUP = JS_FILE + ".bak_correct"

# Backup first
shutil.copy(JS_FILE, BACKUP)

content = open(JS_FILE, 'r', encoding='utf-8').read()

# 1. Extract short code entries from function layer
function_start = content.find('id:"function"')
material_start = content.find('id:"material"')
function_section = content[function_start:material_start]

# Pattern matches full entry + code_str + image_path
pattern = r'(\{code:"(\d{1,3})",name:"[^\"]+",role:"[^\"]+",image:"generated-images/(code_\d+\.jpg)",node:\d+,races:\[.*?\]\})'
short_entries = re.findall(pattern, function_section)

origin_entries = []
creation_entries = []

for full_entry, code_str, img_path in short_entries:
    s = code_str.lstrip('0')
    if len(s) <= 2:
        origin_entries.append(full_entry)
    else:
        creation_entries.append(full_entry)

print(f"Origin entries: {len(origin_entries)}")
print(f"Creation entries: {len(creation_entries)}")

# 2. Remove short entries from function layer
for full_entry, code_str, img_path in short_entries:
    escaped = re.escape(full_entry)
    function_section = re.sub(escaped + r'\s*,?\s*', '', function_section, count=1)

# 3. Reconstruct function layer
# Find function layer object boundaries
func_obj_start = content.rfind('{', 0, function_start)
# Function layer goes until material layer starts
material_obj_start = content.rfind('{', 0, material_start)

old_function = content[func_obj_start:material_obj_start]

# Replace function_section in the middle
# Find where function_section appears
func_section_idx = old_function.find('id:"function"')
if func_section_idx >= 0:
    new_function = old_function[:func_section_idx] + function_section
else:
    new_function = old_function

# 4. Build creation layer with short entries
creation_idx = content.find('id:"creation"')
innate_idx = content.find('id:"innate"')
old_creation = content[creation_idx:innate_idx]

# Find deities:[ in old_creation
deities_open = old_creation.find('deities:[')
if deities_open >= 0:
    # Find closing ]}, or }]
    # Look for the pattern after deities:[
    remaining_after_deities = old_creation[deities_open+9:]
    # Find matching ] followed by }
    bracket_pos = remaining_after_deities.find(']}}')
    if bracket_pos >= 0:
        closing = remaining_after_deities[:bracket_pos+1]
        new_deities_block = '\n    ' + ',\n    '.join(creation_entries) + '\n  ]' if creation_entries else '[]'
        new_creation = old_creation[:deities_open+9] + new_deities_block + old_creation[deities_open+9+len(closing):]
    else:
        new_creation = old_creation
else:
    new_creation = old_creation

# 5. Assemble final content
origin_idx = content.find('id:"origin"')
origin_obj_start = content.rfind('{', 0, origin_idx)
old_origin = content[origin_idx:creation_idx]

# Reconstruct entire file
# Split by: before origin | origin section | creation section | rest
before_origin = content[:origin_obj_start]
rest_after_creation = content[innate_idx:]

new_file = before_origin + new_creation + rest_after_creation

# Fix function layer by removing short entries from function section
# Actually the function_section we extracted is just the text between id:"function" and id:"material"
# We need to replace that section in the new file

func_layer_start = new_file.find('id:"function"')
material_layer_start = new_file.find('id:"material"')

# Find the full function layer object
func_obj_s = new_file.rfind('{', 0, func_layer_start)
# Go forward to find the full object boundary
# The function object ends before "id:"material""
func_section_extracted = new_file[func_obj_s:material_layer_start]

# Replace with cleaned version
# Find the deities array
deities_open = func_section_extracted.find('deities:[')
if deities_open >= 0:
    # Find closing ]
    remaining = func_section_extracted[deities_open+9:]
    # The deities array content
    if remaining_entries:
        new_deities = ',\n    '.join(remaining_entries)
    else:
        new_deities = ''
    new_func_section = func_section_extracted[:deities_open+9] + '\n  ' + new_deities + '\n  ]}'
    
    # Replace in the full content
    new_file = new_file[:func_obj_s] + new_func_section + new_file[func_obj_s + len(func_section_extracted):]

with open(JS_FILE, 'w', encoding='utf-8') as f:
    f.write(new_file)

print(f"Fixed file written: {len(new_file)} chars")

# Verify
verify = open(JS_FILE, 'r', encoding='utf-8').read()
for layer in ['origin', 'creation', 'innate', 'elite', 'function', 'material']:
    idx = verify.find(f'id:"{layer}"')
    if idx >= 0:
        next_layer = verify.find('id:"', idx+5)
        section = verify[idx:next_layer] if next_layer > idx else verify[idx:idx+300]
        count = section.count('code:')
        print(f"{layer}: {count} deities")
