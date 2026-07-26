# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from nine_palace import calculate_nine_palace

for date in ['1991/12/24', '1991/8/16']:
    try:
        result = calculate_nine_palace(date, shichen='卯时')
        print(f'{date}: {result}')
        print()
    except Exception as e:
        print(f'{date}: ERROR {e}')
        import traceback
        traceback.print_exc()
        print()
