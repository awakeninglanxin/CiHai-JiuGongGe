# -*- coding: utf-8 -*-
"""
慈海九宫格 - 交互式查询工具
============================
运行此文件后，根据提示输入阳历生日和时辰，即可查询九宫格信息。

时辰对照表：
  申时(15-17点) / 酉时(17-19点) → 金 → 半补12
  寅时(3-5点)  / 卯时(5-7点)   → 木 → 半补45
  亥时(21-23点)/ 子时(23-01点)  → 水 → 半补06
  巳时(9-11点) / 午时(11-13点)  → 火 → 半补3
  辰时(7-9点)  / 戌时(19-21点)  / 丑时(1-3点) / 未时(13-15点) → 土 → 半补789

注：子时需区分：
  前子时：23:00-00:00（属于下一天）
  后子时：00:00-01:00（属于当天）
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from nine_palace import calculate_nine_palace, format_result

def ask_date():
    """询问并解析日期"""
    print("\n" + "=" * 50)
    print("【九宫格查询】请输入阳历生日")
    print("=" * 50)
    print("格式：年/月/日，例如：1991/12/24")
    print("提示：输入 q 退出\n")

    while True:
        date_input = input("请输入日期: ").strip()

        if date_input.lower() == 'q':
            print("\n感谢使用，再见！")
            sys.exit(0)

        # 验证格式
        parts = date_input.replace('-', '/').split('/')
        if len(parts) != 3:
            print("格式错误！请输入：年/月/日，例如：1991/12/24")
            continue

        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            if year < 1900 or year > 2100:
                print("年份请输入1900-2100之间的有效年份")
                continue
            if month < 1 or month > 12:
                print("月份请输入1-12")
                continue
            if day < 1 or day > 31:
                print("日期请输入1-31")
                continue
            return f"{year}/{month:02d}/{day:02d}"
        except ValueError:
            print("输入无效！请输入数字，例如：1991/12/24")

def ask_shichen():
    """询问时辰"""
    print("\n" + "=" * 50)
    print("【时辰选择】请输入出生时辰")
    print("=" * 50)
    print("""
时辰对照表：
  ┌─────────────────────────────────────────────┐
  │ 寅时(3-5点)  / 卯时(5-7点)   → 木 → 半补45 │
  │ 巳时(9-11点) / 午时(11-13点) → 火 → 半补3  │
  │ 申时(15-17点)/ 酉时(17-19点) → 金 → 半补12 │
  │ 亥时(21-23点)               → 水 → 半补06 │
  │ 辰时(7-9点)  / 戌时(19-21点) │            │
  │ 丑时(1-3点)  / 未时(13-15点) → 土 → 半补789│
  └─────────────────────────────────────────────┘

  ※ 子时(23:00-01:00) 需区分：
    → 前子时：23:00-00:00（属于下一天）
    → 后子时：00:00-01:00（属于当天）

请直接输入时辰，例如：巳时、卯时、前子时
输入 q 退出
""")

    valid_shichen = [
        '寅时', '卯时', '巳时', '午时',
        '申时', '酉时', '亥时', '辰时', '戌时', '丑时', '未时',
        '前子时', '后子时', '子时'
    ]

    while True:
        shichen_input = input("请输入时辰: ").strip()

        if shichen_input.lower() == 'q':
            print("\n感谢使用，再见！")
            sys.exit(0)

        if shichen_input in valid_shichen:
            # 如果输入"子时"，自动询问是前还是后
            if shichen_input == '子时':
                print("\n⚠️ 子时需要区分前子时或后子时：")
                print("  前子时：23:00-00:00（属于下一天）")
                print("  后子时：00:00-01:00（属于当天）")
                while True:
                    zi_choice = input("请选择 1=前子时 / 2=后子时: ").strip()
                    if zi_choice == '1':
                        return '前子时'
                    elif zi_choice == '2':
                        return '后子时'
                    else:
                        print("请输入 1 或 2")
            return shichen_input
        else:
            print(f"无效的时辰！可选：{'、'.join(valid_shichen)}")

def main():
    print("\n" + "★" * 25)
    print("   欢迎使用 慈海九宫格 查询工具")
    print("★" * 25)

    while True:
        # 1. 输入日期
        date_str = ask_date()

        # 2. 输入时辰
        shichen = ask_shichen()

        # 3. 计算并显示结果
        print("\n" + "█" * 50)
        print("【查询结果】")
        print("█" * 50)

        result = calculate_nine_palace(date_str, shichen)
        print(format_result(result))

        # 4. 询问是否继续
        print("\n" + "-" * 50)
        while True:
            again = input("是否继续查询？(y/n): ").strip().lower()
            if again == 'y':
                break
            elif again == 'n':
                print("\n感谢使用，再见！")
                print("\n" + "★" * 25)
                return
            else:
                print("请输入 y 或 n")

if __name__ == '__main__':
    main()
