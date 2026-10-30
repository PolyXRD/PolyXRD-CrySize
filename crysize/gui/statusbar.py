"""状态栏：内部评估版徽章居中显示（红色加粗）。

QStatusBar 现有两种放置方式都拿不到「常驻 + 严格水平居中」：

- ``addPermanentWidget`` —— 只能贴右侧，且会挤在永久区最右端；
- ``addWidget`` —— 普通控件，``showMessage`` 显示临时消息时会被隐藏。

所以这里把徽章做成状态栏的子控件，在 resize/show 时按整条状态栏的几何
手工居中；同时重写 ``showMessage``，把左侧消息按剩余宽度省略，避免长消息
压到徽章上。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QStatusBar

from crysize.gui.theme import EDITION_RED, UI_FONT

#: 徽章与状态栏左右边缘保留的最小间距（px）
_EDGE_PAD = 12


class CenteredBadgeStatusBar(QStatusBar):
    """底部状态栏，支持一枚居中的红色加粗徽章。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._badge = QLabel(self)
        font = QFont(UI_FONT, 10)
        font.setBold(True)
        self._badge.setFont(font)
        self._badge.setStyleSheet(f"color:{EDITION_RED}; background:transparent;")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.hide()

    # ------------------------------------------------------------------
    def badge(self) -> QLabel:
        """徽章控件（注册版不显示，调用方自行 setText + show）。"""
        return self._badge

    def set_badge_text(self, text: str) -> None:
        """设置徽章文字；空串表示不显示（注册版）。"""
        self._badge.setText(text)
        self._badge.setVisible(bool(text))
        self._place_badge()

    # ------------------------------------------------------------------
    def showMessage(self, message: str, timeout: int = 0) -> None:  # noqa: N802
        """左侧消息按剩余宽度省略，保证不压到居中徽章。"""
        super().showMessage(self._elide(message), timeout)

    def _elide(self, message: str) -> str:
        if not message:
            return message
        if self._badge.isHidden():
            avail = self.width() - 2 * _EDGE_PAD
        else:
            # 徽章左边界之前可用的宽度
            avail = self._badge.x() - 2 * _EDGE_PAD
        if avail <= 0:
            return message
        metrics = QFontMetrics(self.font())
        if metrics.horizontalAdvance(message) <= avail:
            return message
        return metrics.elidedText(message, Qt.ElideRight, avail)

    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._place_badge()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._place_badge()

    def _place_badge(self) -> None:
        if self._badge.isHidden():
            return
        self._badge.adjustSize()
        x = (self.width() - self._badge.width()) // 2
        y = (self.height() - self._badge.height()) // 2
        self._badge.move(max(_EDGE_PAD, x), max(0, y))
        self._badge.raise_()
