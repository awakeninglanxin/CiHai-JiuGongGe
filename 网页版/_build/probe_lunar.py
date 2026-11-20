# -*- coding: utf-8 -*-
import sys, json
from datetime import date, timedelta
from lunarcalendar import Converter, Solar
try:
    import lunar_python
    HAS_LP = True
except Exception:
    HAS_LP = False
print('lunar_python', HAS_LP)

start = date(1900,1,1); end = date(2100,12,31)
d = start; prev=None; months=[]
while d <= end:
    try:
        l = Converter().Solar2Lunar(Solar(d.year,d.month,d.day))
        key = (l.year, l.month, l.day)
    except Exception as e:
        print('ERR', d, e); break
    if prev is None or key[2]==1:
        months.append({'start': d.isoformat(), 'ly': key[0], 'lm': key[1], 'day': key[2]})
    prev=key
    d += timedelta(days=1)
print('月份数', len(months))
print('首3', months[:3])
print('末3', months[-3:])
# 检查长度分布
lens={}
for i,m in enumerate(months[:-1]):
    n = (date.fromisoformat(months[i+1]['start']) - date.fromisoformat(m['start'])).days
    lens[n]=lens.get(n,0)+1
print('月长分布', lens)
# 闰月数
leaps=[m for m in months if m['lm']<0]
print('闰月数', len(leaps), '首尾', leaps[0], leaps[-1])
# 年范围
print('农历年范围', months[0]['ly'], months[-1]['ly'])
