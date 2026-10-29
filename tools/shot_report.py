"""把 HTML 报告整页渲染成 PNG，用于版式实拍复核。

用法::

    python tools/shot_report.py _smoke/report.html _smoke/report_full.png [宽]

做法：用 QtWebEngine 载入本地 HTML，读出 ``document.body.scrollHeight`` 后把
视图拉到整页高度再 grab —— 一次成像，避免分段截图拼不齐。中文与字体依赖
系统字体，需在有图形会话的环境运行（沙箱里会退化为空白）。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "_smoke/report.html")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "_smoke/report_full.png")
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1100
    if not src.exists():
        print(f"找不到 {src}")
        return 1

    app = QApplication(sys.argv[:1])
    view = QWebEngineView()
    view.resize(width, 1200)
    view.show()

    loop = QEventLoop()
    height = {"v": 1200}

    def probe() -> None:
        def got(value) -> None:
            height["v"] = int(value) if value else 1200
            loop.quit()
        view.page().runJavaScript("document.body.scrollHeight", got)

    def loaded(ok: bool) -> None:
        QTimer.singleShot(600, probe)   # 等字体与内嵌 base64 图解码完

    view.loadFinished.connect(loaded)
    view.load(QUrl.fromLocalFile(str(src.resolve())))
    QTimer.singleShot(20000, loop.quit)     # 兜底，避免卡死
    loop.exec()

    view.resize(width, min(max(height["v"], 800), 12000))
    QTimer.singleShot(700, loop.quit)
    loop.exec()

    dst.parent.mkdir(parents=True, exist_ok=True)
    ok = view.grab().save(str(dst))
    print(f"[report-shot] {dst}  {width}x{height['v']}  saved={ok}  "
          f"{dst.stat().st_size // 1024 if ok else 0} KB")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
