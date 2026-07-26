import re, json

content = open('deities.js', 'r', encoding='utf-8').read()

# 切分各 layer 块
layer_ids = ['origin', 'creation', 'innate', 'elite', 'function', 'material']
positions = {}
for lid in layer_ids:
    p = content.find('id:"' + lid + '"')
    if p >= 0:
        positions[lid] = p

# 按位置排序后截取
sorted_layers = sorted(positions.items(), key=lambda x: x[1])
layer_blocks = {}
for i, (lid, p) in enumerate(sorted_layers):
    end = sorted_layers[i+1][1] if i+1 < len(sorted_layers) else len(content)
    layer_blocks[lid] = content[p:end]

print("=== 各层 code 长度分布 ===")
for lid, block in layer_blocks.items():
    codes = re.findall(r'code:"(\d+)"', block)
    if not codes:
        print(f"{lid}: 空 (0 条)")
        continue
    lens = [len(c) for c in codes]
    from collections import Counter
    cnt = Counter(lens)
    dist = ", ".join(f"{k}位×{v}" for k, v in sorted(cnt.items()))
    print(f"{lid}: {len(codes)} 条 | 长度分布: {dist}")
    # 显示最短几个码
    shortest = sorted(codes, key=lambda c: (len(c), c))[:5]
    print(f"   最短码: {shortest}")
