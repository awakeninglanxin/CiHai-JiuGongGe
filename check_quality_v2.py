#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慈海九宫格童子图质量扫描 v2
使用PIL/Pillow进行图像分析，避免cv2编码问题
"""

import os
import json
from PIL import Image
import numpy as np

IMG_DIR = 'D:/AAA我的文件/慈海九宫格_整合版/generated-images/'

def get_image_files():
    """获取所有 code_0*.jpg 文件"""
    files = []
    for f in os.listdir(IMG_DIR):
        if f.startswith('code_0') and f.endswith('.jpg'):
            code = f.replace('code_', '').replace('.jpg', '')
            files.append((code, os.path.join(IMG_DIR, f)))
    return sorted(files, key=lambda x: int(x[0]))

def load_image(filepath):
    """加载图片并返回numpy数组"""
    try:
        img = Image.open(filepath)
        img.load()  # 确保图片完全加载
        arr = np.array(img)
        return arr, img.size
    except Exception as e:
        return None, str(e)

def detect_wing_asymmetry(arr, size):
    """检测翅膀不对称 - 比较左右肩膀亮度"""
    issues = []
    w, h = size
    
    # 肩膀区域: 顶部20%高度, 两侧各20%宽度
    shoulder_y1 = int(h * 0.1)
    shoulder_y2 = int(h * 0.35)
    mid_x = w // 2
    
    # 左肩
    left_shoulder = arr[shoulder_y1:shoulder_y2, :mid_x]
    # 右肩
    right_shoulder = arr[shoulder_y1:shoulder_y2, mid_x:]
    
    left_brightness = left_shoulder.mean()
    right_brightness = right_shoulder.mean()
    
    diff_pct = abs(left_brightness - right_brightness) / max(min(left_brightness, right_brightness), 1)
    
    if diff_pct > 0.15:  # 差异超过15%认为有问题
        side = '右' if left_brightness > right_brightness else '左'
        issues.append(f'翅膀亮度不均(左{left_brightness:.1f}/右{right_brightness:.1f},差{diff_pct:.1%}),{side}侧明显更暗,可能半边翅膀缺失')
    
    return issues

def detect_eye_quality(arr, size):
    """检测眼部质量 - 亮度/颜色分布分析"""
    issues = []
    w, h = size
    
    # 面部区域: 顶部15%-45%, 宽度35%-65%
    face_y1 = int(h * 0.05)
    face_y2 = int(h * 0.4)
    face_x1 = int(w * 0.35)
    face_x2 = int(w * 0.65)
    
    face_region = arr[face_y1:face_y2, face_x1:face_x2]
    
    if face_region.size == 0:
        return ['面部区域检测失败']
    
    # 转换为灰度
    if len(face_region.shape) == 3:
        gray = np.mean(face_region, axis=2)
    else:
        gray = face_region
    
    # 1. 检测整体亮度 - 如果面部太暗,可能图片质量问题
    if gray.mean() < 40:
        issues.append(f'面部过暗(均值{gray.mean():.0f}),可能生成失败')
    
    # 2. 检测方差 - 方差过低表示图片缺乏细节(可能闭眼/模糊)
    variance = gray.var()
    std = gray.std()
    
    if std < 15:
        issues.append(f'面部细节缺失(标准差{std:.1f}),可能极度模糊或闭眼')
    
    # 3. 检测高频成分 - 边缘密度
    # 用简单的梯度检测边缘
    dx = np.gradient(gray, axis=1)
    dy = np.gradient(gray, axis=0)
    
    edge_density = ((np.abs(dx) > 20) | (np.abs(dy) > 20)).sum() / gray.size
    
    if edge_density < 0.03:
        issues.append(f'边缘稀少(密度{edge_density:.4f}),可能图片模糊或过度平滑(闭眼?)')
    
    # 4. 对称性 - 左右脸亮度一致性
    mid_x = face_region.shape[1] // 2
    left_face = face_region[:, :mid_x]
    right_face = face_region[:, mid_x:]
    
    left_mean = np.mean(left_face) if left_face.size > 0 else 0
    right_mean = np.mean(right_face) if right_face.size > 0 else 0
    
    face_diff = abs(left_mean - right_mean) / max(max(left_mean, right_mean), 1)
    
    if face_diff > 0.2:
        issues.append(f'面部左右不均(左{left_mean:.1f}/右{right_mean:.1f},差{face_diff:.1%})')
    
    # 5. 亮度标准差 - 检测瞳孔与眼白的区分度
    # 瞳孔区域应该有较暗的点
    dark_pixels = (gray < 60).sum() / gray.size
    
    if 0.001 < dark_pixels < 0.01:
        issues.append(f'瞳孔/眼白区分度低(暗像素{dark_pixels:.2%}),可能翻白眼或瞳孔模糊')
    
    return issues

def detect_semi_closed_eyes(arr, size):
    """检测眼睛是否半闭 - 用眼睛区域的颜色均匀性判断"""
    issues = []
    w, h = size
    
    # 眼睛区域: 面部上半部分
    eye_y1 = int(h * 0.12)
    eye_y2 = int(h * 0.25)
    eye_x1 = int(w * 0.4)
    eye_x2 = int(w * 0.6)
    
    eye_region = arr[eye_y1:eye_y2, eye_x1:eye_x2]
    
    if eye_region.size == 0:
        return issues
    
    # 如果眼睛区域整体很暗或很亮,可能有问题
    if len(eye_region.shape) == 3:
        gray = np.mean(eye_region, axis=2)
    else:
        gray = eye_region
    
    brightness = gray.mean()
    
    # 翻白眼: 整体非常亮(白色过多)
    if brightness > 200:
        issues.append(f'疑似翻白眼(亮度{brightness:.1f})')
    
    # 半闭眼: 灰色调占比过高(眼睑覆盖)
    gray_zone = ((gray > 100) & (gray < 180)).sum() / gray.size
    if gray_zone > 0.6:
        issues.append(f'疑似半闭眼(灰色区域{gray_zone:.1%})')
    
    return issues

def main():
    print("="*60)
    print("慈海九宫格童子图质量扫描 v2")
    print("="*60)
    
    files = get_image_files()
    print(f"找到 {len(files)} 张童子图\n")
    
    results = {
        'total': len(files),
        'pass': 0,
        'fail': 0,
        'failures': [],
        'categories': {
            'wing_asymmetry': [],
            'blur_low_detail': [],
            'semi_closed_eyes': [],
            'pupil_unclear': [],
            'dark_face': [],
            'light_face': [],
            'unknown': []
        }
    }
    
    for i, (code, filepath) in enumerate(files):
        arr, err = load_image(filepath)
        
        if arr is None:
            results['fail'] += 1
            results['failures'].append({
                'code': code,
                'filepath': filepath,
                'error': err
            })
            continue
        
        all_issues = []
        
        # 检测各类问题
        eye_issues = detect_eye_quality(arr, (arr.shape[1], arr.shape[0]))
        wing_issues = detect_wing_asymmetry(arr, (arr.shape[1], arr.shape[0]))
        semi_closed = detect_semi_closed_eyes(arr, (arr.shape[1], arr.shape[0]))
        
        all_issues.extend([(f'眼: {iss}', eye_issues.index(iss)) for iss in eye_issues])
        all_issues.extend([(f'翅: {iss}', wing_issues.index(iss)) for iss in wing_issues])
        all_issues.extend([(f'闭: {iss}', semi_closed.index(iss)) for iss in semi_closed])
        
        has_issues = len(eye_issues) > 0 or len(wing_issues) > 0 or len(semi_closed) > 0
        
        if has_issues:
            results['fail'] += 1
            
            # 分类
            category = 'unknown'
            for issue_text, idx in all_issues[:1]:  # 主要问题
                if '翅膀' in issue_text or '亮度不均' in issue_text:
                    category = 'wing_asymmetry'
                    results['categories']['wing_asymmetry'].append({'code': code, 'issue': issue_text})
                elif '细节缺失' in issue_text or '边缘稀少' in issue_text:
                    category = 'blur_low_detail'
                    results['categories']['blur_low_detail'].append({'code': code, 'issue': issue_text})
                elif '翻白眼' in issue_text or '半闭' in issue_text:
                    category = 'semi_closed_eyes'
                    results['categories']['semi_closed_eyes'].append({'code': code, 'issue': issue_text})
                elif '瞳孔' in issue_text or '区分度低' in issue_text:
                    category = 'pupil_unclear'
                    results['categories']['pupil_unclear'].append({'code': code, 'issue': issue_text})
                elif '过暗' in issue_text:
                    category = 'dark_face'
                    results['categories']['dark_face'].append({'code': code, 'issue': issue_text})
                else:
                    category = 'light_face'
                    results['categories']['light_face'].append({'code': code, 'issue': issue_text})
            
            results['failures'].append({
                'code': code,
                'filepath': filepath,
                'all_issues': all_issues,
                'primary_category': category
            })
        
        else:
            results['pass'] += 1
        
        if (i + 1) % 50 == 0:
            print(f"  扫描进度: {i+1}/{len(files)}")
    
    # 输出统计
    print(f"\n{'='*60}")
    print(f"扫描完成!")
    print(f"{'='*60}")
    print(f"总计: {results['total']} 张")
    print(f"通过: {results['pass']} 张 ({results['pass']/results['total']:.1%})")
    print(f"有问题: {results['fail']} 张 ({results['fail']/results['total']:.1%})")
    
    print(f"\n问题分类:")
    for cat, items in results['categories'].items():
        print(f"  {cat}: {len(items)} 张")
    
    if results['failures']:
        print(f"\n=== 需要重新生成的童子代码清单 ===")
        for item in results['failures']:
            code = item['code']
            primary_cat = item.get('primary_category', 'unknown')
            main_issue = item['all_issues'][0][0] if item['all_issues'] else '未知'
            print(f"  code_{code} [{primary_cat}]: {main_issue}")
    
    # 保存完整报告
    report_path = 'D:/AAA我的文件/慈海九宫格_整合版/quality_report_v2.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整报告已保存至: {report_path}")

if __name__ == '__main__':
    main()
