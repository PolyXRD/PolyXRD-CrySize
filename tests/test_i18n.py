"""i18n 三语一致性测试。

规则（与家族 RutAna 一致）：
1. 三个语言表的 key 集必须完全一致（zh_CN 为源）—— 缺键会在界面上显示
   ``⟪key⟫``，靠测试在上线前拦截；
2. 所有含 ``{…}`` 占位符的文案，三语的格式占位符集合必须一致，否则运行时
   ``str.format`` 直接抛 KeyError/IndexError。
"""

from __future__ import annotations

import string
import unittest

from crysize.i18n import TABLE, set_language, tr


def _placeholders(text: str) -> set[str]:
    """取 str.format 风格的字段名（忽略 {{}} 转义与格式规范）。"""
    fmt = string.Formatter()
    return {f for _, f, _, _ in fmt.parse(text) if f}


class TestI18n(unittest.TestCase):
    def test_key_sets_identical(self) -> None:
        base = set(TABLE["zh_CN"])
        for lang, table in TABLE.items():
            self.assertEqual(base - set(table), set(), f"{lang} 缺键")
            self.assertEqual(set(table) - base, set(), f"{lang} 多键")

    def test_placeholders_consistent(self) -> None:
        for key, zh in TABLE["zh_CN"].items():
            want = _placeholders(zh)
            for lang, table in TABLE.items():
                got = _placeholders(table[key])
                self.assertEqual(got, want, f"{lang}.{key} 占位符不一致")

    def test_tr_format_and_missing(self) -> None:
        set_language("en_US")
        self.assertIn("Williamson", tr("sum.wh.head"))
        self.assertEqual(tr("no.such.key"), "⟪no.such.key⟫")
        self.assertIn("12.3", tr("pf.rwp_high", v=12.3))
        set_language("zh_CN")
        self.assertIn("谢乐", tr("tab.scherrer"))


if __name__ == "__main__":
    unittest.main()
