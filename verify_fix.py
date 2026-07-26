import re

content = open('deities.js', 'r', encoding='utf-8').read()

for layer in ['origin', 'creation', 'innate', 'elite', 'function', 'material']:
    idx = content.find(f'id:"{layer}"')
    if idx < 0:
        print(f'{layer}: NOT FOUND')
        continue
    
    obj_start = content.rfind('{', 0, idx)
    depth = 0
    obj_end = obj_start
    for j in range(obj_start, min(obj_start + 50000, len(content))):
        if content[j] == '{': depth += 1
        elif content[j] == '}':
            depth -= 1
            if depth == 0:
                obj_end = j + 1
                break
    
    layer_obj = content[obj_start:obj_end]
    code_count = len(re.findall(r'\{code:', layer_obj))
    codes = re.findall(r'code:"(\d+)",', layer_obj)
    
    print(f'{layer}: {code_count} deities')
    if codes:
        print(f'  Samples: {codes[:3]}')
        short = len([c for c in codes if len(c.lstrip('0')) <= 3])
        long = len([c for c in codes if len(c.lstrip('0')) > 3])
        print(f'  Length: {short} short, {long} long')

print('\nAll layers checked.')
