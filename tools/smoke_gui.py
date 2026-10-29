"""GUI 冒烟测试：离屏启动、加载真实数据、出报告并截图。

用法::

    python tools/smoke_gui.py <sample.txt> <standard.txt> [输出目录]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from crysize.core.pattern import read_pattern  # noqa: E402
from crysize.gui.dialogs import AboutDialog, CopyrightDialog  # noqa: E402
from crysize.gui.main_window import MainWindow  # noqa: E402
from crysize.gui.report import build_html  # noqa: E402
from crysize.i18n import (TABLE, current_language, set_language)  # noqa: E402


def _check_missing_keys() -> int:
    """三语 key 集必须一致，缺失/多余都算失败（⟪key⟫ 会直接上界面）。"""
    bad = 0
    base = set(TABLE["zh_CN"])
    for lang, table in TABLE.items():
        miss = base - set(table)
        extra = set(table) - base
        if miss or extra:
            bad += 1
            print(f"[i18n] {lang}: missing={sorted(miss)} extra={sorted(extra)}")
    return bad


def main() -> int:
    sample = sys.argv[1] if len(sys.argv) > 1 else ""
    standard = sys.argv[2] if len(sys.argv) > 2 else ""
    outdir = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "_smoke"
    outdir.mkdir(parents=True, exist_ok=True)

    if _check_missing_keys():
        return 1

    app = QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 9))
    win = MainWindow()
    win.resize(1360, 900)
    win.show()
    app.processEvents()

    if sample:
        win.sample = read_pattern(sample)
    if standard:
        win.standard = read_pattern(standard)

    # 三语扫描：每个语言重算 + 截主界面 + 出报告。漏译键会以 ⟪key⟫ 形式
    # 出现在界面/报告里，人工复查截图即可发现；这里再做一次文本断言兜底。
    fail = 0
    for lang in ("zh_CN", "en_US", "ja_JP"):
        set_language(lang)
        win.retranslateUi()          # 内部会触发重算（若已有样品）
        if sample:
            win.recompute()
        app.processEvents()
        shot = outdir / f"win_{lang}.png"
        win.grab().save(str(shot))
        print(f"[shot] {shot}  {shot.stat().st_size // 1024} KB")

        if win.bundle is not None:
            html = build_html(win.bundle, sample_name=win.bundle.sample.label)
            if "⟪" in html:
                print(f"[i18n] {lang}: 报告出现未翻译键 ⟪…⟫")
                fail += 1
            rp = outdir / f"report_{lang}.html"
            rp.write_text(html, encoding="utf-8")
            print(f"[report] {rp}  {len(html) // 1024} KB")
            print(f"[bundle] {lang}: fits={len(win.bundle.fits)} "
                  f"valid={win.bundle.scherrer.n_valid}")
        print(f"[lang] {lang} active={current_language()}")

    # 中文态补拍：三个页签 + 关于/版权对话框（家族新增组件必须实拍）
    set_language("zh_CN")
    win.retranslateUi()
    app.processEvents()
    for i in range(win.tabs.count()):
        win.tabs.setCurrentIndex(i)
        app.processEvents()
        shot = outdir / f"tab{i}.png"
        win.grab().save(str(shot))
        print(f"[shot] {shot}  {shot.stat().st_size // 1024} KB")
    for cls, name in ((AboutDialog, "about"), (CopyrightDialog, "copyright")):
        dlg = cls(win)
        dlg.show()
        app.processEvents()
        shot = outdir / f"{name}.png"
        dlg.grab().save(str(shot))
        print(f"[dialog] {name}: {dlg.width()}x{dlg.height()}  "
              f"{shot.stat().st_size // 1024} KB")
        dlg.close()
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
