import ctypes, os

root = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images"
paths = [
    os.path.join(root, "nul"),
    os.path.join(root, "individual", "nul"),
]

for p in paths:
    print(f"Trying: {p}")
    # Normal path
    if ctypes.windll.kernel32.DeleteFileW(p):
        print(f"  Deleted: {p}")
        continue
    err = ctypes.windll.kernel32.GetLastError()
    print(f"  Normal failed, err={err}")
    
    # Try with \\.\ prefix (NT namespace)
    raw_path = "\\\\?\\" + p.replace("/", "\\")
    print(f"  Trying raw: {raw_path}")
    if ctypes.windll.kernel32.DeleteFileW(raw_path):
        print(f"  Deleted via raw path")
    else:
        err = ctypes.windll.kernel32.GetLastError()
        print(f"  Raw path failed, err={err}")

print("Done")
