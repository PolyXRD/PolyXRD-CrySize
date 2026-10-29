"""对话框：关于 / 版权与许可。

「关于」「版权」两框的框架文案为中文，许可要点正文以**中英并列**常量化 ——
与家族 RutAna、LFP 同一写法：许可条款是中英双语法律文本，不随界面语言切换，
也不因工具不同而改写。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                               QTextBrowser, QVBoxLayout, QWidget)

from crysize.edition import IS_INTERNAL
from crysize.i18n import tr
from crysize.gui.resources import LOGO_HORIZONTAL, resource_path
from crysize.gui.theme import (BODY, BRAND, CHIP_BG, CHIP_BORDER, CHIP_TEXT,
                               FAINT, INK, MUTED)
from crysize.version import (APP_CONTACT_EMAIL, APP_CONTACT_URL, APP_COPYRIGHT,
                             APP_NAME, APP_ROLE, __version__)

# --------------------------------------------------------------------------- #
# 版权要点（恒为中英双语并列，与界面语言无关）
# --------------------------------------------------------------------------- #
COPYRIGHT_BODY_ZH = (
    "<p>© 2026 PolyXRD Team。本软件采用<b>双许可</b>发布："
    "<b>学术许可</b>（仅限非商业学术研究与教学，免费）或向版权持有人另行申请的"
    "<b>商业许可</b>。学术许可下可自由使用、复制、修改与分发，"
    "<b>不允许任何商业用途</b>；商用前必须联系版权持有人取得书面商业授权。</p>"
)
COPYRIGHT_BODY_EN = (
    "<p>Copyright © 2026 PolyXRD Team. This software is released under a "
    "<b>dual license</b>: the free <b>Academic License</b> (non-commercial "
    "academic research and education only) or a separately obtained "
    "<b>Commercial License</b>. The Academic License permits use, copying, "
    "modification and distribution <b>for non-commercial purposes only</b>; "
    "commercial use requires a separate written Commercial License.</p>"
)
COPYRIGHT_NOTE = (
    "完整许可文本见随附 LICENSE 与 LICENSE-CN 文件 / "
    "See the accompanying LICENSE and LICENSE-CN files for the full text."
)

#: 方法学来源声明（About 与 README、HTML 报告须保持同一口径）
METHOD_SOURCE_ZH = (
    "Scherrer, Gött. Nachr. 2 (1918) 98 · Williamson &amp; Hall, "
    "Acta Metall. 1 (1953) 22 · Caglioti et al., Nucl. Instr. 3 (1958) 223 · "
    "Stokes, Proc. Phys. Soc. A 61 (1948) 382"
)
METHOD_SOURCE_EN = (
    "Method references: Scherrer (1918) · Williamson &amp; Hall (1953) · "
    "Caglioti et al. (1958) · Stokes (1948)"
)

#: 特性 chip 的 key（与家族 About 一致的三枚青色药丸）
CHIP_KEYS = ("about.chip1", "about.chip2", "about.chip3")


class AboutDialog(QDialog):
    """关于：logo、版本、定位、特性 chip、方法来源与联系方式。

    布局与家族 RutAna/LFP 一致：**不用 QTextBrowser**（其在 QVBoxLayout 中
    sizeHint 只按一行算，必然出现滚动条），全部用 QLabel + chip 排布，让
    对话框一次显示完整内容。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title", name=APP_NAME))
        self.setMinimumWidth(520)
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignHCenter)
        root.setSpacing(8)

        logo_path = resource_path(LOGO_HORIZONTAL)
        if logo_path.exists():
            logo = QLabel(self)
            logo.setPixmap(QPixmap(str(logo_path)).scaledToWidth(
                340, Qt.SmoothTransformation))
            logo.setAlignment(Qt.AlignHCenter)
            root.addWidget(logo)
        else:
            name = QLabel(APP_NAME, self)
            name.setStyleSheet(f"font-size:22px; font-weight:700; color:{BRAND};")
            name.setAlignment(Qt.AlignHCenter)
            root.addWidget(name)

        edition_txt = tr("edition.internal") if IS_INTERNAL else ""
        ver_text = f"v{__version__}" + (f"　·　{edition_txt}" if edition_txt else "")
        ver = QLabel(ver_text, self)
        ver.setAlignment(Qt.AlignHCenter)
        ver.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        root.addWidget(ver)

        role = QLabel(tr("about.role"), self)
        role.setAlignment(Qt.AlignHCenter)
        role.setWordWrap(True)
        role.setStyleSheet(f"color:{BODY};")
        root.addWidget(role)

        chips = QHBoxLayout()
        chips.setAlignment(Qt.AlignHCenter)
        chips.setSpacing(6)
        for key in CHIP_KEYS:
            text = tr(key)
            chip = QLabel(text, self)
            chip.setStyleSheet(
                f"font-size:11px; color:{CHIP_TEXT}; background:{CHIP_BG};"
                f"border:1px solid {CHIP_BORDER}; border-radius:10px;"
                "padding:3px 10px;")
            chips.addWidget(chip)
        root.addLayout(chips)

        # 方法来源：中英并列（与许可正文同理，文献引用不随界面语言改写）
        refs = QLabel(f"{METHOD_SOURCE_ZH}<br>{METHOD_SOURCE_EN}", self)
        refs.setAlignment(Qt.AlignHCenter)
        refs.setWordWrap(True)
        refs.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        root.addWidget(refs)

        contact = QLabel(self)
        contact.setTextFormat(Qt.RichText)
        contact.setOpenExternalLinks(True)
        contact.setAlignment(Qt.AlignHCenter)
        contact.setWordWrap(True)
        contact.setText(
            f"{tr('about.contact')}<br>"
            f"<a href='mailto:{APP_CONTACT_EMAIL}'>{APP_CONTACT_EMAIL}</a> · "
            f"<a href='{APP_CONTACT_URL}'>{APP_CONTACT_URL}</a>")
        root.addWidget(contact)

        cr = QLabel(APP_COPYRIGHT, self)
        cr.setAlignment(Qt.AlignHCenter)
        cr.setStyleSheet(f"color:{FAINT}; font-size:11px;")
        root.addWidget(cr)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.button(QDialogButtonBox.Ok).setText(tr("dlg.ok"))
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)


class CopyrightDialog(QDialog):
    """版权与许可（中英要点 + 完整文本指向）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("copyright.title"))
        # 家族做法：给定初始尺寸而不是交给 sizeHint —— QTextBrowser 的
        # sizeHint 不随文档长度增长，否则底部联系方式会被裁掉
        self.resize(640, 400)
        self.setMinimumWidth(580)
        root = QVBoxLayout(self)
        view = QTextBrowser(self)
        view.setFrameShape(QTextBrowser.NoFrame)
        view.setOpenExternalLinks(True)
        view.setHtml(
            f"<h3 style='color:{INK}'>PolyXRD 家族 · 版权与许可声明</h3>"
            f"{COPYRIGHT_BODY_ZH}{COPYRIGHT_BODY_EN}"
            f"<p style='color:{MUTED}'>{COPYRIGHT_NOTE}</p>"
            f"<hr>"
            f"<p style='color:{BODY}'>商业授权联系 / Commercial licensing<br>"
            f"<a href='mailto:{APP_CONTACT_EMAIL}'>{APP_CONTACT_EMAIL}</a> · "
            f"<a href='{APP_CONTACT_URL}'>{APP_CONTACT_URL}</a></p>"
            f"<p style='color:{FAINT};font-size:12px'>{APP_COPYRIGHT}</p>")
        root.addWidget(view)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.button(QDialogButtonBox.Ok).setText(tr("dlg.ok"))
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

    def toPlainText(self) -> str:
        """供冒烟测试断言关键内容（许可要点必须出现中英双段）。"""
        view = self.findChild(QTextBrowser)
        return view.toPlainText() if view is not None else ""
