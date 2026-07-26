"""
慈海九宫格 - 自动重启生成器
每次运行gen_v9_auto.py，如果中断自动重启，直到全部完成
"""
import os, sys, subprocess, re, time

PROJECT = r'D:\AAA我的文件\慈海九宫格_整合版'
IMG_DIR = os.path.join(PROJECT, 'generated-images')
SCRIPT = os.path.join(PROJECT, 'gen_v9_auto.py')
PYTHON = sys.executable

MAX_RESTARTS = 20

for attempt in range(1, MAX_RESTARTS + 1):
    # 检查当前进度
    existing = set()
    for f in os.listdir(IMG_DIR):
        m = re.match(r'^code_(\d+)\.jpg$', f)
        if m:
            existing.add(m.group(1))
    
    with open(os.path.join(PROJECT, 'deities.js'), encoding='utf-8') as fh:
        content = fh.read()
    all_codes = set(re.findall(r'code:\s*"(\d+)"', content))
    
    missing = len(all_codes - existing)
    print(f"\n{'='*60}")
    print(f"第 {attempt}/{MAX_RESTARTS} 次运行 | 已有: {len(existing)}/{len(all_codes)} | 缺失: {missing}")
    print(f"{'='*60}\n", flush=True)
    
    if missing == 0:
        print("全部完成！")
        break
    
    # 运行生成脚本
    try:
        proc = subprocess.run(
            [PYTHON, SCRIPT],
            cwd=PROJECT,
            timeout=540,  # 9分钟超时，留1分钟余量
            capture_output=False,
        )
        print(f"\n脚本退出，返回码: {proc.returncode}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"\n脚本超时(9分钟)，准备重启...", flush=True)
    except Exception as e:
        print(f"\n脚本异常: {e}，准备重启...", flush=True)
    
    time.sleep(3)

# 最终统计
existing = set()
for f in os.listdir(IMG_DIR):
    m = re.match(r'^code_(\d+)\.jpg$', f)
    if m:
        existing.add(m.group(1))
print(f"\n最终: {len(existing)}/{len(all_codes)} | 缺失: {len(all_codes - existing)}")
