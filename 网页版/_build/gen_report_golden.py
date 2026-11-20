# -*- coding: utf-8 -*-
"""
生成三份报告的黄金 Markdown（冻结「现在」以保证可复现），供 JS 版逐字节比对。
"""
import json, os, sys, tempfile, importlib.util
import datetime as _dtmod


# ── 冻结时间：2026-10-27 10:05 ──
class _FakeDT(_dtmod.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 27, 10, 5, 0)


_dtmod.datetime = _FakeDT

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EDIR = os.path.join(ROOT, "核心引擎")
QDIR = os.path.join(ROOT, "查询工具")
for p in (EDIR, QDIR):
    sys.path.insert(0, p)

# 伪造 biowell.config（倪海厦模块内部会 import）
import types
_biowell = types.ModuleType('biowell')
_conf = types.ModuleType('biowell.config')
_conf.USER_NAME = '蓝馨'
_conf.BASE_DIR = tempfile.gettempdir()
_conf.USER_BIRTH_DATE = '1991/08/16'
_biowell.config = _conf
sys.modules['biowell'] = _biowell
sys.modules['biowell.config'] = _conf


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


bao = load_mod("bao_report", os.path.join(EDIR, "完整综合命理报告v3.9.py"))
sl = load_mod("shiliao", os.path.join(EDIR, "食疗动功生成器v3.3.py"))
nhx = load_mod("nihaixia", os.path.join(EDIR, "倪海厦中医建议生成器.py"))

CASES = [
    ("蓝馨", "1991/12/24", "巳时", "male", None),
    ("测试甲", "2000/01/01", "子时", "female", "深圳"),
    ("测试乙", "1985/06/15", "前子时", "male", None),
    ("测试丙", "1976/03/08", "卯时", "female", "北京"),
    ("测试丁", "2026/03/25", "午时", "male", None),
    ("测试戊", "1955/11/30", "后子时", "female", None),
    ("测试己", "2020/05/23", "申时", "male", "成都"),
]


def main():
    out = []
    for name, birth, sc, g, loc in CASES:
        rec = {"name": name, "birth": birth, "shichen": sc, "gender": g, "location": loc}
        try:
            # 1) 完整综合命理报告（该函数会写文件，落到 temp）
            f1 = os.path.join(tempfile.gettempdir(), 'tmp_%s.md' % name)
            old = os.getcwd()
            os.chdir(tempfile.gettempdir())
            try:
                _, md1 = bao.generate_comprehensive_report(birth, sc, g, name)
            finally:
                os.chdir(old)
            rec["md_comprehensive"] = md1
        except Exception as e:
            rec["md_comprehensive"] = "ERR %s: %s" % (type(e).__name__, e)
        try:
            rec["md_shiliao"] = sl.generate_report(name, birth, sc, g, None)
        except Exception as e:
            rec["md_shiliao"] = "ERR %s: %s" % (type(e).__name__, e)
        try:
            _, md3 = nhx.generate_ni_report(birth, sc, g, name, loc, tempfile.gettempdir())
            rec["md_ni"] = md3
        except Exception as e:
            rec["md_ni"] = "ERR %s: %s" % (type(e).__name__, e)
        out.append(rec)
        print("  已生成", name, birth, sc, g, loc,
              "| 长", len(rec.get("md_comprehensive", "")), len(rec.get("md_shiliao", "")), len(rec.get("md_ni", "")))

    dst = os.path.join(HERE, 'report_golden.json')
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump({"now": "2026-10-27T10:05:00", "cases": out}, f, ensure_ascii=False)
    print("已写", dst, os.path.getsize(dst), "字节")


if __name__ == '__main__':
    main()
