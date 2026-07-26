import os, subprocess

root = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images"

# Get all jpg and png files using os.listdir (Python handles 'nul' correctly)
files = []
for f in sorted(os.listdir(root)):
    fp = os.path.join(root, f)
    if os.path.isfile(fp) and f.lower() != "nul" and (f.endswith('.jpg') or f.endswith('.png')):
        rel = os.path.relpath(fp, root).replace(os.sep, '/')
        files.append(os.path.join("generated-images", rel))

print(f"Total files to add: {len(files)}")

# Add in batches of 50
batch = []
for i, f in enumerate(files):
    batch.append(f)
    if len(batch) >= 50:
        cmd = ["git", "add", "--ignore-errors"] + batch
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Batch {i//50}: {len(batch)} files - rc={r.returncode}, stderr={r.stderr[:200] if r.stderr else ''}")
        else:
            print(f"Batch {i//50}: {len(batch)} files OK")
        batch = []

if batch:
    cmd = ["git", "add", "--ignore-errors"] + batch
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Final batch: {len(batch)} files - rc={r.returncode}")

print("Done")
