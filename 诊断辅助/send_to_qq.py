# -*- coding: utf-8 -*-
"""
QQ发送脚本
读取auto_report_system.py生成的发送指令，发送报告到QQ
"""

import os
import json
import sys

def send_report_to_qq():
    """发送报告到QQ"""
    print("📤 发送报告到QQ...")
    
    # 读取发送指令
    instruction_path = os.path.join(os.path.dirname(__file__), 'qq_send_instruction.json')
    
    if not os.path.exists(instruction_path):
        print("❌ 发送指令文件不存在")
        print("请先运行 auto_report_system.py")
        return False
    
    try:
        with open(instruction_path, 'r', encoding='utf-8') as f:
            instruction = json.load(f)
        
        print(f"📋 发送指令内容:")
        print(f"  通道: {instruction.get('channel')}")
        print(f"  目标QQ: {instruction.get('target')}")
        print(f"  消息长度: {len(instruction.get('message', ''))} 字符")
        
        # 显示消息预览
        message = instruction.get('message', '')
        print(f"\n📝 消息预览 (前500字符):")
        print("-" * 50)
        print(message[:500])
        if len(message) > 500:
            print("...")
        print("-" * 50)
        
        # 确认发送
        print("\n⚠️ 注意：此脚本需要OpenClaw环境才能实际发送")
        print("在实际环境中，您需要调用OpenClaw的message工具")
        
        # 生成发送命令
        print("\n🔧 发送命令（在OpenClaw中执行）:")
        print(f"""
message send \\
  --channel wechat-access \\
  --target {instruction.get('target')} \\
  --message "{message[:100].replace('"', '\\"')}..."
""")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取发送指令失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("QQ报告发送工具")
    print("=" * 60)
    
    success = send_report_to_qq()
    
    if success:
        print("\n✅ 发送指令已准备")
        print("请在OpenClaw环境中使用message工具发送")
    else:
        print("\n❌ 发送准备失败")

if __name__ == "__main__":
    main()