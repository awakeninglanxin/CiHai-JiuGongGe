import re
content = open('deities.js', 'r', encoding='utf-8').read()
layers = ['origin', 'creation', 'innate', 'elite', 'function', 'material']
for layer in layers:
    idx = content.find('id:"' + layer + '"')
    if idx < 0:
        print(f'{layer}: 未找到')
        continue
    dstart = content.find('deities:[', idx)
    depth = 0
    dend = -1
    for j in range(dstart + 9, len(content)):
        if content[j] == '[':
            depth += 1
        elif content[j] == ']':
            depth -= 1
            if depth == 0:
                dend = j
                break
    block = content[dstart:dend]
    n = len(re.findall(r'\{code:', block))
    print(f'{layer}: {n} 个条目')
