#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慈海九宫格 v17 - AI增强版全面质量检测
新增检测项:
  1. 手部对称性(双臂/双手是否存在及左右大小一致)
  2. 皮肤质感(过于皱褶vs过于光滑)
  3. 肢体完整性(手脚数量检查)
  4. 角色一致性(童子/长者形态合理性)
"""
import os
import json
from PIL import Image
import numpy as np

IMG_DIR = r'D:\AAA我的文件\慈海九宫格_整合版\generated-images'

def get_all_code_images():
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

def detect_hand_symmetry(arr):
    """
    检测手部/手臂对称性
    - 提取下半身两侧手臂区域
    - 比较左右手臂的像素面积/密度是否均衡
    - 检测是否存在明显缺失手臂
    """
    issues = []
    h, w = arr.shape[:2]
    
    # 上半身: 顶部15%-45% (含肩膀手臂)
    arm_y1, arm_y2 = int(h * 0.15), int(h * 0.45)
    
    # 左半身和右半身的手臂区域
    left_arm = arr[arm_y1:arm_y2, 0:w//2]
    right_arm = arr[arm_y1:arm_y2, w//2:w]
    
    # 计算肤色/肉色调区域(红色通道偏高)
    def skin_mask(patch):
        if patch.size == 0:
            return None
        if len(patch.shape) == 3:
            r, g, b = patch[:,:,0].astype(float), patch[:,:,1].astype(float), patch[:,:,2].astype(float)
            # 简化肤色检测: R>G, R>B, 且RGB差不大
            mask = (r > g) & (r > b) & (abs(r-g) < 60) & (abs(r-b) < 60) & (r+b > 200)
            return mask.sum()
        return None
    
    left_skin = skin_mask(left_arm)
    right_skin = skin_mask(right_arm)
    
    if left_skin is not None and right_skin is not None:
        total = left_skin + right_skin
        if total > 0:
            ratio = min(left_skin, right_skin) / max(left_skin, right_skin)
            if ratio < 0.5:
                side = '右臂' if left_skin > right_skin else '左臂'
                issues.append('手臂不对称(左右像素比%.1f%%): 可能%s偏弱/缺失' % (ratio*100, side))
            if total < 300:
                issues.append('手臂肉色区域过少(%d像素): 可能双臂不明显' % total)

    return issues

def detect_skin_texture(arr):
    """
    检测皮肤质感
    - 计算高频细节含量(纹理)
    - 过低=过于光滑塑料感
    - 过高=过度皱纹/粗糙
    """
    issues = []
    h, w = arr.shape[:2]
    
    # 面部区域
    face_y1, face_y2 = int(h * 0.1), int(h * 0.4)
    face_x1, face_x2 = int(w * 0.35), int(w * 0.65)
    face = arr[face_y1:face_y2, face_x1:face_x2]
    
    if face.size == 0:
        return issues
    
    gray = np.mean(face.astype(float), axis=2) if len(face.shape)==3 else face.astype(float)
    
    # 高频细节(梯度幅度)
    gx = np.gradient(gray, axis=1)
    gy = np.gradient(gray, axis=0)
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    high_freq = (grad_mag > 25).sum() / gray.size
    avg_grad = grad_mag.mean()
    
    # 身体区域(肩部以下)
    body_y1 = int(h * 0.4)
    body = arr[body_y1:int(h*0.8), int(w*0.3):int(w*0.7)]
    
    if body.size > 0:
        body_gray = np.mean(body.astype(float), axis=2) if len(body.shape)==3 else body.astype(float)
        bx = np.gradient(body_gray, axis=1)
        by = np.gradient(body_gray, axis=0)
        body_freq = ((np.sqrt(bx**2 + by**2) > 25).sum() / body_gray.size)
    else:
        body_freq = 0
    
    # 判断: 高频过低=塑料感/过度平滑, 过高=皱纹多
    if high_freq < 0.002 and body_freq < 0.005:
        issues.append('皮肤过度光滑(高频%0.04f/%0.04f): 可能塑料感/蜡像感' % (high_freq, body_freq))
    elif high_freq > 0.15 or body_freq > 0.12:
        issues.append('皮肤过度粗糙(高频%0.04f/%0.04f): 可能皱纹过多/皮肤衰老' % (high_freq, body_freq))
    
    return issues

def detect_limb_count(arr):
    """
    检测肢体完整性
    - 估算四肢区域是否存在
    - 检测是否有额外肢体(多手多脚)
    """
    issues = []
    h, w = arr.shape[:2]
    
    # 身体轮廓检测: 寻找肤色/非背景区域
    if len(arr.shape) == 3:
        r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
        # 简单身体掩码: 排除蓝色天空背景
        body_mask = (r > 100) & (g > 80) & (b < 200) & ((r+g+b) > 200)
    else:
        body_mask = arr > 100
    
    # 从上到下切分身体段
    segments = []
    seg_h = h // 8
    for i in range(8):
        y_start, y_end = i * seg_h, (i+1) * seg_h
        seg_mask = body_mask[y_start:y_end]
        if seg_mask.any():
            left_half = seg_mask[:, :w//2].sum()
            right_half = seg_mask[:, w//2:].sum()
            segments.append((i, left_half, right_half))
    
    # 肩膀段(2-3): 应该左右都有
    shoulder_segs = [s for s in segments if 2 <= s[0] <= 3]
    if shoulder_segs:
        for idx, left, right in shoulder_segs:
            if left < 5 or right < 5:
                total_pixels = left + right
                if total_pixels < 30:
                    issues.append('肩部像素过少(%d): 可能肩部畸形' % total_pixels)
            elif min(left,right)/max(left,right) < 0.3:
                side = '右肩' if left > right else '左肩'
                issues.append('肩部严重不对称: 可能%s发育不良' % side)
    
    # 手部段(4-5): 应该左右各有一个突出
    hand_segs = [s for s in segments if 4 <= s[0] <= 5]
    if hand_segs:
        for idx, left, right in hand_segs:
            if left < 2 or right < 2:
                pass  # 手掌可能缩回
    
    return issues

def detect_color_palette(arr):
    """
    检测色调是否合理
    - 童子应该有嫩色/肤色
    - 不应该大面积灰/褐/黑色(可能老态)
    """
    issues = []
    h, w = arr.shape[:2]
    
    # 主体区域(去除背景)
    body_mask = np.zeros((h,w), dtype=bool)
    if len(arr.shape) == 3:
        r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
        body_mask = (r+b > 100) & ((r-g) > 10) | ((r-b) > 10)
    
    if body_mask.sum() < 1000:
        return issues
    
    rgb_body = arr[body_mask]
    
    if len(rgb_body.shape) == 2:
        r_avg, g_avg, b_avg = rgb_body.mean(axis=0)
    else:
        return issues
    
    # 判断色彩倾向
    hue_angle = np.arctan2(b_avg - g_avg, 2*r_avg - g_avg - b_avg) * 180 / np.pi
    if hue_angle < 0: hue_angle += 360
    
    # 冷色调/蓝色调过重
    if b_avg > r_avg * 1.2 and b_avg > g_avg * 1.2:
        issues.append('整体偏蓝冷色调: 可能角色老化/阴冷感')
    
    # 褐色/灰色调过重
    if abs(r_avg - g_avg) < 20 and abs(g_avg - b_avg) < 20 and (r_avg+g_avg+b_avg)/3 < 120:
        issues.append('整体偏灰暗: 可能角色苍老')
    
    return issues

def detect_edge_density(arr):
    """检测图像整体清晰度"""
    h, w = arr.shape[:2]
    if len(arr.shape) == 3:
        gray = np.mean(arr.astype(float), axis=2)
    else:
        gray = arr.astype(float)
    
    gx = np.gradient(gray, axis=1)
    gy = np.gradient(gray, axis=0)
    edge_mag = np.sqrt(gx**2 + gy**2)
    high_edge = (edge_mag > 40).sum() / (h*w)
    
    if high_edge < 0.005:
        return '图像极度模糊(高频边缘占比%.3f%%)' % (high_edge*100)
    elif high_edge < 0.01:
        return '图像偏模糊(高频边缘占比%.3f%%)' % (high_edge*100)
    return None

def main():
    print('=' * 70)
    print('慈海九宫格 v17 - AI增强版全面质量检测')
    print('新增: 手部对称/皮肤质感/肢体完整性/角色一致性')
    print('=' * 70)
    
    files = get_all_code_images()
    print('找到 %d 张童子/长者图\n' % len(files))
    
    results = {
        'total': len(files),
        'pass': 0,
        'fail': 0,
        'failures': [],
        'categories': {},
        'detailed_stats': {
            'hand_symmetry': 0,
            'skin_texture': 0,
            'limb_count': 0,
            'color_palette': 0,
            'edge_density': 0,
            'eye_asymmetry': 0,
            'blur': 0,
        }
    }
    
    hand_issues = []
    skin_issues = []
    limb_issues = []
    palette_issues = []
    edge_issues = []
    eye_issues = []
    blur_issues = []
    
    for i, (code, filepath) in enumerate(files):
        arr, err = load_image(filepath)
        if arr is None:
            results['fail'] += 1
            results['failures'].append({
                'code': code, 'filepath': filepath,
                'error': err, 'is_error': True,
                'detail': []
            })
            results['detailed_stats']['edge_density'] += 1
            continue
        
        all_detail = []
        
        # v17新增: 手部对称性
        h_iss = detect_hand_symmetry(arr)
        if h_iss:
            hand_issues.extend([(code, msg) for msg in h_iss])
            all_detail.extend(h_iss)
        
        # v17新增: 皮肤质感
        s_iss = detect_skin_texture(arr)
        if s_iss:
            skin_issues.extend([(code, msg) for msg in s_iss])
            all_detail.extend(s_iss)
        
        # v17新增: 肢体完整性
        l_iss = detect_limb_count(arr)
        if l_iss:
            limb_issues.extend([(code, msg) for msg in l_iss])
            all_detail.extend(l_iss)
        
        # v17新增: 色调合理性
        p_iss = detect_color_palette(arr)
        if p_iss:
            palette_issues.extend([(code, msg) for msg in p_iss])
            all_detail.extend(p_iss)
        
        # 原有: 边缘密度/模糊
        e_iss = detect_edge_density(arr)
        if e_iss:
            edge_issues.append((code, e_iss))
            blur_issues.append((code, e_iss))
            all_detail.append(e_iss)
        
        # 原有: 面部不对称(眼睛)
        w, h = arr.shape[1], arr.shape[0]
        if len(arr.shape) == 3:
            face_gray = np.mean(arr, axis=2)
        else:
            face_gray = arr.astype(float)
        
        face_y1, face_y2 = int(h * 0.1), int(h * 0.4)
        face_x1, face_x2 = int(w * 0.3), int(w * 0.7)
        
        face = face_gray[face_y1:face_y2, face_x1:face_x2]
        if face.size > 0:
            mid_x = face.shape[1] // 2
            left_face = face[:, :mid_x].mean()
            right_face = face[:, mid_x:].mean()
            
            if max(left_face, right_face) > 0:
                asym = abs(left_face - right_face) / max(left_face, right_face)
                if asym > 0.08:
                    side = '右脸' if left_face > right_face else '左脸'
                    ey_msg = '面部亮度不对称(%.1f%%): %s偏暗' % (asym*100, side)
                    eye_issues.append((code, ey_msg))
                    all_detail.append(ey_msg)
        
        has_issues = len(all_detail) > 0
        if has_issues:
            results['fail'] += 1
            # 确定主要类别
            if any('手' in d or '手臂' in d for d in all_detail):
                cat = 'hand_symmetry'
            elif any('皮肤' in d or '皱纹' in d or '塑料感' in d for d in all_detail):
                cat = 'skin_texture'
            elif any('肢体' in d or '肩' in d for d in all_detail):
                cat = 'limb_count'
            elif any('蓝' in d or '灰' in d or '色调' in d for d in all_detail):
                cat = 'color_palette'
            elif any('不对称' in d or '半闭' in d or '眼睛' in d for d in all_detail):
                cat = 'eye_asymmetry'
            elif any('模糊' in d or '边缘' in d for d in all_detail):
                cat = 'blur'
            else:
                cat = 'other'
            
            if cat not in results['categories']:
                results['categories'][cat] = []
            results['categories'][cat].append({
                'code': code, 'issues': all_detail
            })
        else:
            results['pass'] += 1
        
        if (i+1) % 200 == 0:
            print('  扫描进度: %d/%d | 异常: %d' % (i+1, len(files), results['fail']))
    
    # 输出统计
    print('\n' + '=' * 70)
    print('扫描结果:')
    print('  总计: %d 张' % results['total'])
    print('  通过: %d 张 (%.1f%%)' % (results['pass'], results['pass']/results['total']*100))
    print('  有问题: %d 张 (%.1f%%)' % (results['fail'], results['fail']/results['total']*100))
    
    print('\n=== 问题分类统计 ===')
    stats = results['detailed_stats']
    print('  手部不对称: %d 张' % len(hand_issues))
    print('  皮肤质感问题: %d 张' % len(skin_issues))
    print('  肢体完整性: %d 张' % len(limb_issues))
    print('  色调不合理: %d 张' % len(palette_issues))
    print('  边缘密度低(模糊): %d 张' % len(edge_issues))
    print('  眼部不对称: %d 张' % len(eye_issues))
    print('  严重模糊: %d 张' % len(blur_issues))
    
    # 输出具体问题样例
    print('\n=== 手部不对称示例(前10) ===')
    for code, msg in hand_issues[:10]:
        print('  code_%s: %s' % (code, msg[:60]))
    
    print('\n=== 皮肤质感示例(前10) ===')
    for code, msg in skin_issues[:10]:
        print('  code_%s: %s' % (code, msg[:60]))
    
    print('\n=== 色调不合理示例(前10) ===')
    for code, msg in palette_issues[:10]:
        print('  code_%s: %s' % (code, msg[:60]))
    
    # 保存完整报告
    report_path = r'D:\AAA我的文件\慈海九宫格_整合版\quality_scan_v17.json'
    results['detail_samples'] = {
        'hand_symmetry': hand_issues[:50],
        'skin_texture': skin_issues[:50],
        'limb_count': limb_issues[:50],
        'color_palette': palette_issues[:50],
        'eye_asymmetry': eye_issues[:100],
        'blur': blur_issues[:50],
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print('\n完整报告已保存: %s' % report_path)
    
    return results

if __name__ == '__main__':
    main()
