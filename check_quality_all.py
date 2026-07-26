#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慈海九宫格 - 所有童子图质量扫描（不限code_0开头）
覆盖所有 code_*.jpg 文件，包括长者形象的非0开头童子图
"""
import os
import json
from PIL import Image
import numpy as np

IMG_DIR = r'D:\AAA我的文件\慈海九宫格_整合版\generated-images'

def get_all_code_images():
    """获取所有 code_*.jpg 文件"""
    files = []
    for f in os.listdir(IMG_DIR):
        if f.startswith('code_') and f.endswith('.jpg'):
            code = f.replace('code_', '').replace('.jpg', '')
            files.append((code, os.path.join(IMG_DIR, f)))
    return sorted(files, key=lambda x: x[0])

def load_image(filepath):
    try:
        img = Image.open(filepath)
        img.load()
        arr = np.array(img)
        return arr, img.size
    except Exception as e:
        return None, str(e)

def detect_face_asymmetry(arr, size):
    """
    检测面部/眼睛不对称问题
    特别针对长者形象（胡须老者、神仙等）
    思路：分别检测左眼区域和右眼区域的相似度和亮度差异
    """
    issues = []
    w, h = size
    
    # 面部区域估计：上30%中间40%
    face_y1 = int(h * 0.1)
    face_y2 = int(h * 0.4)
    face_x1 = int(w * 0.3)
    face_x2 = int(w * 0.7)
    
    if face_y2 <= face_y1 or face_x2 <= face_x1:
        return ['面部区域过小无法检测']
    
    face = arr[face_y1:face_y2, face_x1:face_x2]
    if face.size == 0:
        return ['面部像素为空']
    
    # 灰度
    if len(face.shape) == 3:
        gray = np.mean(face.astype(float), axis=2)
    else:
        gray = face.astype(float)
    
    # ===== 1. 检测左右脸亮度差异 =====
    mid_x = gray.shape[1] // 2
    left_face = gray[:, :mid_x]
    right_face = gray[:, mid_x:]
    
    left_mean = left_face.mean()
    right_mean = right_face.mean()
    
    if max(left_mean, right_mean) > 0:
        asym_ratio = abs(left_mean - right_mean) / max(left_mean, right_mean)
        if asym_ratio > 0.08:  # 左右不对称超过8%
            side = '右脸' if left_mean > right_mean else '左脸'
            issues.append(f'面部亮度不对称({asym_ratio:.1%}): {side}偏暗(左{left_mean:.0f}/右{right_mean:.0f})')
    
    # ===== 2. 检测眼睛区域 =====
    eye_y1 = int(face.shape[0] * 0.15)
    eye_y2 = int(face.shape[0] * 0.35)
    eye_x1 = int(face.shape[1] * 0.2)
    eye_x2 = int(face.shape[1] * 0.8)
    
    eye_region = face[eye_y1:eye_y2, eye_x1:eye_x2]
    if eye_region.size == 0:
        return issues
    
    if len(eye_region.shape) == 3:
        eye_gray = np.mean(eye_region.astype(float), axis=2)
    else:
        eye_gray = eye_region.astype(float)
    
    # 左眼区域
    le_mid_x = eye_gray.shape[1] // 2
    left_eye = eye_gray[:, :le_mid_x]
    right_eye = eye_gray[:, le_mid_x:]
    
    le_mean = left_eye.mean()
    re_mean = right_eye.mean()
    
    if max(le_mean, re_mean) > 0:
        eye_asym = abs(le_mean - re_mean) / max(le_mean, re_mean)
        if eye_asym > 0.1:  # 双眼亮度差异超过10%
            side = '右眼' if le_mean > re_mean else '左眼'
            issues.append(f'双眼亮度差异({eye_asym:.1%}): 可能{side}半闭/全闭(左均值{le_mean:.0f}/右{re_mean:.0f})')
    
    # ===== 3. 检测整体边缘密度 =====
    dx = np.gradient(gray, axis=1)
    dy = np.gradient(gray, axis=0)
    edge_density = ((np.abs(dx) > 30) | (np.abs(dy) > 30)).sum() / gray.size
    
    if edge_density < 0.02:
        issues.append(f'面部细节极低(边缘密度{edge_density:.4f}),可能模糊/过度平滑')
    
    # ===== 4. 检测翻白眼 =====
    dark_pct = (gray < 50).sum() / gray.size
    if dark_pct < 0.001:
        issues.append(f'无深色像素({dark_pct:.3%}),可能大面积白色(翻白眼/过曝)')
    
    return issues

def detect_general_quality(arr, size):
    """检测一般图像质量：模糊、过暗、过小"""
    issues = []
    w, h = size
    
    if len(arr.shape) != 3 or arr.shape[0] < 50 or arr.shape[1] < 50:
        issues.append(f'图像尺寸过小({w}x{h})或格式异常')
        return issues
    
    # 灰度
    if len(arr.shape) == 3:
        gray = np.mean(arr.astype(float), axis=2)
    else:
        gray = arr.astype(float)
    
    # 亮度均值
    brightness = gray.mean()
    if brightness < 30:
        issues.append(f'图像极暗(均值{brightness:.0f}),可能生成失败')
    elif brightness > 230:
        issues.append(f'图像极亮(均值{brightness:.0f}),可能过曝')
    
    # 整体方差
    var = gray.var()
    std = gray.std()
    if std < 10:
        issues.append(f'整体过于单一色调(std={std:.1f}),可能生成异常')
    
    return issues

def main():
    print("=" * 70)
    print("慈海九宫格 - 全量童子图质量扫描（含长者形象）")
    print("=" * 70)
    
    files = get_all_code_images()
    print(f"找到 {len(files)} 张童子/长者图\n")
    
    results = {
        'total': len(files),
        'pass': 0,
        'fail': 0,
        'failures': [],
        'categories': {}
    }
    
    for i, (code, filepath) in enumerate(files):
        arr, err = load_image(filepath)
        if arr is None:
            results['fail'] += 1
            results['failures'].append({
                'code': code, 'filepath': filepath,
                'error': err, 'is_error': True
            })
            continue
        
        all_issues = []
        face_issues = detect_face_asymmetry(arr, (arr.shape[1], arr.shape[0]))
        gen_issues = detect_general_quality(arr, (arr.shape[1], arr.shape[0]))
        all_issues.extend(face_issues + gen_issues)
        
        has_issues = len(all_issues) > 0
        
        if has_issues:
            results['fail'] += 1
            cat = 'unknown'
            for iss in all_issues:
                if '不对称' in iss or '半闭' in iss:
                    cat = 'eye_asymmetry'
                    break
                elif '模糊' in iss or '细节极低' in iss:
                    cat = 'blur'
                    break
                elif '极暗' in iss or '生成失败' in iss:
                    cat = 'too_dark'
                    break
                elif '极亮' in iss or '过曝' in iss:
                    cat = 'overexposed'
                    break
                elif '尺寸过小' in iss:
                    cat = 'too_small'
                    break
            
            results['failures'].append({
                'code': code, 'filepath': filepath,
                'issues': all_issues, 'category': cat,
                'is_error': False
            })
            
            if cat not in results['categories']:
                results['categories'][cat] = []
            results['categories'][cat].append({'code': code, 'issues': all_issues})
        else:
            results['pass'] += 1
        
        if (i + 1) % 100 == 0:
            print(f"  扫描进度: {i+1}/{len(files)} | 已发现异常: {results['fail']}")
    
    # 输出报告
    print(f"\n{'='*70}")
    print(f"扫描结果:")
    print(f"  总计: {results['total']} 张")
    print(f"  通过: {results['pass']} 张 ({results['pass']/results['total']:.1%})")
    print(f"  有问题: {results['fail']} 张 ({results['fail']/results['total']:.1%})")
    
    print(f"\n问题分类:")
    total_found = sum(len(v) for v in results['categories'].values())
    for cat, items in sorted(results['categories'].items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(items)} 张")
    
    # 输出问题code清单
    if results['failures']:
        print(f"\n=== 有问题童子/长者代码清单 ===")
        for item in results['failures']:
            code = item['code']
            if item.get('is_error'):
                print(f"  code_{code}: ❌ 加载失败 - {item['error']}")
            else:
                main_issue = '; '.join(item['issues'][:2])
                print(f"  code_{code}: ⚠️ [{item['category']}] {main_issue}")
    
    # 保存完整报告
    report_path = r'D:\AAA我的文件\慈海九宫格_整合版\quality_scan_all_v2.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存: {report_path}")
    
    return results

if __name__ == '__main__':
    main()
