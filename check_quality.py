#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慈海九宫格童子图质量扫描脚本
扫描所有 code_0*.jpg，检测：
1. 眼睛问题（闭上/模糊/扭曲）- 用面部颜色分布+对称性分析
2. 翅膀不对称（半边翅膀）- 用左右半边亮度/纹理差异
3. 瞳孔模糊（眼白瞳孔不分明）- 用高频细节检测

输出：quality_report.json + 手动抽查图片预览
"""

import os
import sys
import json
import re
import cv2
import numpy as np
from collections import defaultdict

IMG_DIR = 'D:/AAA我的文件/慈海九宫格_整合版/generated-images/'

def get_image_files():
    """获取所有 code_0*.jpg 文件"""
    files = []
    for f in os.listdir(IMG_DIR):
        if f.startswith('code_0') and f.endswith('.jpg'):
            code = f.replace('code_', '').replace('.jpg', '')
            files.append((code, os.path.join(IMG_DIR, f)))
    return sorted(files, key=lambda x: int(x[0]))

def detect_eye_issues(img_path):
    """
    检测眼部问题：
    - 计算面部区域的颜色分布
    - 检测眼睛区域的对称性和清晰度
    """
    issues = []
    try:
        img = cv2.imread(img_path)
        if img is None:
            return ['无法读取']
        
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. 检测亮度变化 - 眼睛区域应该有明显的明暗对比
        # 假设面部在图像中央偏上区域 (30%-70% width, 10%-50% height)
        face_y_start = int(h * 0.1)
        face_y_end = int(h * 0.5)
        face_x_start = int(w * 0.3)
        face_x_end = int(w * 0.7)
        
        face_roi = gray[face_y_start:face_y_end, face_x_start:face_x_end]
        
        # 如果脸部ROI太亮/太暗，可能有问题
        if face_roi.mean() < 30 or face_roi.mean() > 200:
            issues.append(f'面部亮度异常(均值={face_roi.mean():.1f})')
        
        # 2. 边缘检测 - 模糊的脸部通常边缘很少
        edges = cv2.Canny(face_roi, 50, 150)
        edge_density = (edges > 0).sum() / edges.size
        
        if edge_density < 0.05:
            issues.append(f'面部边缘稀疏(密度={edge_density:.4f})，可能模糊')
        
        # 3. 左右半边对称性检测 - 检测翅膀不对称
        half_w = face_roi.shape[1] // 2
        left_half = face_roi[:, :half_w]
        right_half = face_roi[:, half_w:]
        
        # 计算左右亮度差异
        left_mean = left_half.mean()
        right_mean = right_half.mean()
        brightness_diff = abs(left_mean - right_mean) / max(left_mean, right_mean, 1)
        
        if brightness_diff > 0.3:
            issues.append(f'左右亮度不均(差{brightness_diff:.2%})，可能翅膀不对称')
        
        # 4. 纹理方向一致性 - 检测扭曲变形
        # 用Sobel算子检测水平/垂直梯度的一致性
        sobel_x = cv2.Sobel(face_roi, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(face_roi, cv2.CV_64F, 0, 1, ksize=3)
        
        grad_x_std = sobel_x.std()
        grad_y_std = sobel_y.std()
        
        # 如果梯度标准差极低，说明纹理单一（可能闭眼/模糊）
        if grad_x_std < 5 and grad_y_std < 5:
            issues.append('纹理过于单一，可能眼部闭合或极度模糊')
        
        # 5. 高频分量检测 - 模糊的图片高频分量少
        f_transform = np.fft.fft2(face_roi)
        f_shifted = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shifted)
        
        # 中心区域(低频) vs 边缘区域(高频)
        center_h, center_w = magnitude.shape[0]//4, magnitude.shape[1]//4
        low_freq = magnitude[center_h:-center_h, center_w:-center_w].mean()
        high_freq = magnitude[:center_h, :center_w].mean()
        
        freq_ratio = high_freq / (low_freq + 1)
        if freq_ratio < 0.1:
            issues.append(f'高频分量极低(比值={freq_ratio:.4f})，图片模糊')
        
        return issues if issues else ['OK']
        
    except Exception as e:
        return [f'检测异常: {str(e)}']

def detect_wing_asymmetry(img_path):
    """专门检测翅膀不对称"""
    issues = []
    try:
        img = cv2.imread(img_path)
        if img is None:
            return ['无法读取']
        
        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 肩部区域 (上半部分, 宽度40%-90%)
        shoulder_y = int(h * 0.15)
        shoulder_x_left = int(w * 0.1)
        shoulder_x_right = int(w * 0.9)
        half_x = int(w * 0.5)
        
        left_shoulder = img[shoulder_y:h//3, shoulder_x_left:half_x]
        right_shoulder = img[shoulder_y:h//3, half_x:shoulder_x_right]
        
        # 计算左右肩部的亮度差异
        left_gray = cv2.cvtColor(left_shoulder, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_shoulder, cv2.COLOR_BGR2GRAY)
        
        left_mean = left_gray.mean()
        right_mean = right_gray.mean()
        
        diff_ratio = abs(left_mean - right_mean) / (max(left_mean, right_mean) + 1)
        
        if diff_ratio > 0.2:
            issues.append(f'翅膀左右亮度不均(差{diff_ratio:.2%})，可能半边翅膀缺失')
        
        return issues if issues else ['OK']
        
    except Exception as e:
        return [f'检测异常: {str(e)}']

def main():
    print("正在扫描所有童子图...")
    files = get_image_files()
    print(f"找到 {len(files)} 张童子图")
    
    results = {
        'total': len(files),
        'ok': 0,
        'has_issues': 0,
        'issues_detail': [],
        'eye_issues': [],
        'wing_issues': [],
        'blur_issues': [],
        'all_detected': []
    }
    
    for i, (code, filepath) in enumerate(files):
        eye_issues = detect_eye_issues(filepath)
        wing_issues = detect_wing_asymmetry(filepath)
        
        all_issues = eye_issues + wing_issues
        has_problems = not (
            (len(eye_issues) == 1 and eye_issues[0] == 'OK') and
            (len(wing_issues) == 1 and wing_issues[0] == 'OK')
        )
        
        if has_problems:
            results['has_issues'] += 1
            results['issues_detail'].append({
                'code': code,
                'filepath': filepath,
                'eye_issues': eye_issues,
                'wing_issues': wing_issues,
                'combined_issues': all_issues
            })
            
            # Categorize
            for iss in eye_issues:
                if '对称' in iss or '亮度不均' in iss or '翅膀' in iss:
                    results['wing_issues'].append({'code': code, 'issue': iss})
                elif '边缘稀疏' in iss or '高频' in iss or '单一' in iss:
                    results['blur_issues'].append({'code': code, 'issue': iss})
        else:
            results['ok'] += 1
        
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{len(files)}")
    
    # Save report
    report_path = 'D:/AAA我的文件/慈海九宫格_整合版/quality_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 质量扫描完成 ===")
    print(f"总计: {results['total']} 张")
    print(f"通过: {results['ok']} 张")
    print(f"有问题: {results['has_issues']} 张")
    
    if results['has_issues'] > 0:
        print(f"\n有问题的code列表:")
        for item in results['issues_detail']:
            print(f"  {item['code']}: {'; '.join(item['combined_issues'])}")
        
        print(f"\n翼翅不对称问题: {len(results['wing_issues'])} 个")
        print(f"模糊/纹理问题: {len(results['blur_issues'])} 个")
        
        print(f"\n完整报告已保存至: {report_path}")
    else:
        print("\n所有童子图眼部/翅膀质量检查通过!")

if __name__ == '__main__':
    main()
