"""主窗口：双标签（Scherrer / Williamson-Hall）+ 参数面板 + 峰表。

菜单：文件 / 语言（运行时热切换，三语）/ 帮助（方法说明、版权、关于）。
状态栏右侧显示版次徽章（仅内部评估版）。

语言切换的实现与家族 RutAna 一致：控件文案集中在 :meth:`retranslateUi`
里统一设置；切换后除刷新控件外还要**重算**一次 —— core 层的警告与质量
标记是计算时按当前语言生成的，不重算会残留旧语言文案。
"""

from __future__ import annotations

import csv
import datetime
import os
import traceback

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QMainWindow, QMessageBox, QPushButton,
                               QSizePolicy, QSpinBox, QSplitter, QTabWidget,
                               QTableWidget, QTableWidgetItem, QTextBrowser,
                               QVBoxLayout, QWidget)

from crysize.core.analysis import AnalysisBundle, AnalysisConfig, refit_with_positions, run_analysis
from crysize.core.elasticity import PRESETS, ElasticParams
from crysize.core.methods import (GROUPS, METHOD_IDS, group_name, method_assume,
                                  method_limit, method_name, method_need,
                                  method_scene, spec_of)
from crysize.core.pattern import SUPPORTED_EXTS, Pattern, read_pattern
from crysize.edition import IS_INTERNAL
from crysize import registration
from crysize.gui.canvas import PatternCanvas, StandardCanvas, WHCanvas
from crysize.gui.dialogs import AboutDialog, CopyrightDialog
from crysize.gui.report import build_html
from crysize.gui.resources import app_icon_path
from crysize.gui.statusbar import CenteredBadgeStatusBar
from crysize.gui.theme import (BODY, BRAND, ERR_RED, FAINT, INK, LINE, MUTED,
                               OK_GREEN, UI_FONT, WARN_AMBER)
from crysize.i18n import (available_languages, current_language, load_language,
                          save_language, set_language, tr)
from crysize.version import APP_CONTACT_EMAIL, APP_COPYRIGHT, APP_NAME, APP_SHORT, __version__

MONO = QFont("Consolas", 9)

#: i18n 长码 -> registration 模块短码（zh_CN/en_US/ja_JP -> zh/en/ja）
_REG_LANG = {"zh_CN": "zh", "en_US": "en", "ja_JP": "ja"}


def _fmt(v, nd: int = 2, dash: str = "—") -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return dash
    if f != f:  # nan
        return dash
    return f"{f:.{nd}f}"


def _sci(v, nd: int = 4, unit: str = "") -> str:
    """科学计数法富文本：``5.5519×10⁻³``。

    界面不用 ``f"{v:.4e}"`` 的 ``e-03`` 写法 —— 那是程序员的读法，
    报告与论文里一律写 ``×10⁻³``；QLabel 走 HTML，上标用 <sup> 即可
    （matplotlib 画布上不能用 &#8315;，字体缺该字形会显示豆腐块，
    那里改用 mathtext）。
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    if f != f or f == 0.0:
        return f"{0.0:.{nd}f}" + (f" {unit}" if unit else "")
    exp = int(f"{f:e}".split("e")[1])
    mant = f / (10.0 ** exp)
    mant_s = f"{mant:.{nd}f}".replace("-", "−")
    sup = f"<sup>{str(exp).replace('-', '−')}</sup>"
    return f"{mant_s}×10{sup}" + (f" {unit}" if unit else "")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        load_language()               # 上次选择的语言，先于任何 tr() 调用
        self.sample: Pattern | None = None
        self.standard: Pattern | None = None
        self.bundle: AnalysisBundle | None = None
        self._loading_table = False
        self._last_method = "scherrer_fwhm"   # 方法下拉重建前后的选中项记忆

        # 注册机制（仅注册版启用；内部评估版 IS_INTERNAL=True 不启用）。
        # 状态文件落在 %APPDATA%/PolyXRD/Registration/CrySize.json，每次启动重校验。
        self._reg = None
        if not IS_INTERNAL:
            registration.set_language(_REG_LANG.get(current_language(), "zh"))
            self._reg = registration.RegistrationManager(
                APP_NAME, registration.default_state_path(APP_SHORT))

        self.setWindowTitle(f"{APP_NAME} v{__version__} — {tr('win.title')}")
        self.resize(1320, 880)
        icon = app_icon_path()
        if icon:
            self.setWindowIcon(QIcon(icon))
        self._build_ui()
        self._build_actions()
        self.retranslateUi()
        self._status(tr("status.ready"))

        # 启动未注册提示：QTimer 延迟到事件循环，不阻塞冒烟/启动画面；
        # 离屏（QT_QPA_PLATFORM=offscreen）或 POLYXRD_REG_NO_PROMPT=1 时自动跳过。
        if self._reg is not None:
            QTimer.singleShot(0, lambda: self._reg.startup_check(self))

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        # 顶部文件行
        top = QHBoxLayout()
        top.setSpacing(8)
        self.btn_sample = QPushButton()
        self.btn_sample.clicked.connect(self.load_sample)
        self.btn_std = QPushButton()
        self.btn_std.clicked.connect(self.load_standard)
        self.btn_clear_std = QPushButton()
        self.btn_clear_std.clicked.connect(self.clear_standard)
        self.lbl_sample = QLabel()
        self.lbl_std = QLabel()
        for w in (self.lbl_sample, self.lbl_std):
            w.setStyleSheet(f"color:{BODY};")
        top.addWidget(self.btn_sample)
        top.addWidget(self.btn_std)
        top.addWidget(self.btn_clear_std)
        top.addSpacing(10)
        top.addWidget(self.lbl_sample, 1)
        top.addWidget(self.lbl_std, 1)
        root.addLayout(top)

        # 主体：左参数 + 右标签
        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._build_side_panel())
        split.addWidget(self._build_tabs())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([360, 940])
        root.addWidget(split, 1)

        self.setCentralWidget(central)
        # 状态栏：内部评估版徽章红色加粗、严格水平居中（见 gui/statusbar.py）
        bar = CenteredBadgeStatusBar(self)
        self.setStatusBar(bar)
        self._status_bar = bar
        self._badge: QLabel | None = bar.badge() if IS_INTERNAL else None

        # 注册版：状态栏最右侧（右对齐）显示「已注册：<单位部门名称>」/「未注册」
        if self._reg is not None:
            self._reg.attach_status_label(bar, self)

    # ------------------------------------------------------------------
    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(330)
        panel.setMaximumWidth(430)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(8)

        # 分析参数
        self.box_params = QGroupBox()
        g = QGridLayout(self.box_params)
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(6)

        self.sp_peaks = QSpinBox()
        self.sp_peaks.setRange(2, 20)
        self.sp_peaks.setValue(5)
        self.sp_peaks.valueChanged.connect(self._schedule)

        self.cb_mode = QComboBox()
        self.cb_mode.currentIndexChanged.connect(self._on_mode_changed)

        self.sp_K = QDoubleSpinBox()
        self.sp_K.setRange(0.5, 1.5)
        self.sp_K.setSingleStep(0.01)
        self.sp_K.setDecimals(2)
        self.sp_K.setValue(0.89)
        self.sp_K.valueChanged.connect(self._schedule)

        self.sp_window = QDoubleSpinBox()
        self.sp_window.setRange(0.6, 12.0)
        self.sp_window.setSingleStep(0.5)
        self.sp_window.setDecimals(1)
        self.sp_window.setValue(3.0)
        self.sp_window.valueChanged.connect(self._schedule)

        self.ck_ka2 = QCheckBox()
        self.ck_ka2.setChecked(True)
        self.ck_ka2.toggled.connect(self._schedule)

        self.sp_prom = QDoubleSpinBox()
        self.sp_prom.setRange(0.002, 0.3)
        self.sp_prom.setSingleStep(0.005)
        self.sp_prom.setDecimals(3)
        self.sp_prom.setValue(0.030)
        self.sp_prom.valueChanged.connect(self._schedule)

        self._param_rows = []         # (QLabel, key) —— retranslateUi 统一改文案
        for i, key in enumerate(("param.n_peaks", "param.width_mode",
                                 "param.K", "param.window", "param.prominence")):
            lbl = QLabel()
            self._param_rows.append((lbl, key))
            g.addWidget(lbl, i, 0)
        g.addWidget(self.sp_peaks, 0, 1)
        g.addWidget(self.cb_mode, 1, 1)
        g.addWidget(self.sp_K, 2, 1)
        g.addWidget(self.sp_window, 3, 1)
        g.addWidget(self.sp_prom, 4, 1)
        g.addWidget(self.ck_ka2, 5, 0, 1, 2)
        lay.addWidget(self.box_params)
        lay.addWidget(self._build_method_box())

        # 角度校正
        self.box_corr = QGroupBox()
        v2 = QVBoxLayout(self.box_corr)
        self.lbl_corr = QLabel()
        self.lbl_corr.setWordWrap(True)
        self.lbl_corr.setStyleSheet("color:#475569; font-size:12px;")
        v2.addWidget(self.lbl_corr)
        lay.addWidget(self.box_corr)

        # 峰表
        self.box_peaks = QGroupBox()
        v3 = QVBoxLayout(self.box_peaks)
        self.tbl = QTableWidget(0, 4)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tbl.setColumnWidth(0, 26)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl.setMinimumHeight(190)
        self.tbl.itemChanged.connect(self._on_table_changed)
        self.tbl.itemSelectionChanged.connect(self._on_row_selected)
        v3.addWidget(self.tbl)
        lay.addWidget(self.box_peaks, 1)

        # 操作按钮
        ops = QHBoxLayout()
        self.btn_recalc = QPushButton()
        self.btn_recalc.clicked.connect(self.recompute)
        self.btn_report = QPushButton()
        self.btn_report.clicked.connect(self.export_report)
        self.btn_csv = QPushButton()
        self.btn_csv.clicked.connect(self.export_csv)
        for b in (self.btn_recalc, self.btn_report, self.btn_csv):
            ops.addWidget(b)
        lay.addLayout(ops)
        return panel

    # ------------------------------------------------------------------
    def _build_method_box(self) -> QWidget:
        """计算方法选择（5 组 7 种）+ 各向异性/弹性参数。"""
        self.box_method = QGroupBox()
        g = QGridLayout(self.box_method)
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(6)

        self.cb_method = QComboBox()
        self.cb_method.currentIndexChanged.connect(self._on_method_changed)

        self.ck_group = QCheckBox()
        self.ck_group.setChecked(False)
        self.ck_group.toggled.connect(self._schedule)

        self.cb_preset = QComboBox()
        self.cb_preset.currentIndexChanged.connect(self._on_preset_changed)

        self.sp_a = QDoubleSpinBox()
        self.sp_a.setRange(1.0, 30.0)
        self.sp_a.setDecimals(4)
        self.sp_a.setSingleStep(0.001)
        self.sp_a.setValue(0.0)
        self.sp_a.valueChanged.connect(self._schedule)

        self.sp_c11 = QDoubleSpinBox()
        self.sp_c12 = QDoubleSpinBox()
        self.sp_c44 = QDoubleSpinBox()
        for sp in (self.sp_c11, self.sp_c12, self.sp_c44):
            sp.setRange(0.0, 2000.0)
            sp.setDecimals(1)
            sp.setSingleStep(1.0)
            sp.setValue(0.0)
            sp.valueChanged.connect(self._schedule)

        self.cb_lattice = QComboBox()
        self.cb_lattice.currentIndexChanged.connect(self._schedule)

        self.btn_guide = QPushButton()
        self.btn_guide.clicked.connect(self.show_method_guide)

        # (label, i18n key) —— retranslateUi 统一改文案
        self._method_rows: list[tuple[QLabel, str]] = []
        row = 0
        for key in ("param.method", "param.group_dir", "param.preset",
                    "param.a", "param.c11", "param.lattice"):
            lbl = QLabel()
            self._method_rows.append((lbl, key))
            g.addWidget(lbl, row, 0)
            row += 1
        g.addWidget(self.cb_method, 0, 1)
        g.addWidget(self.ck_group, 1, 0, 1, 2)
        g.addWidget(self.cb_preset, 2, 1)
        g.addWidget(self.sp_a, 3, 1)
        h = QHBoxLayout()
        h.setSpacing(4)
        h.addWidget(self.sp_c11)
        h.addWidget(self.sp_c12)
        h.addWidget(self.sp_c44)
        g.addLayout(h, 4, 1)
        g.addWidget(self.cb_lattice, 5, 1)
        g.addWidget(self.btn_guide, 6, 0, 1, 2)
        return self.box_method

    def _fill_method_combo(self) -> None:
        """方法下拉：按 5 组分组，条目形如「组名 — 方法名」。"""
        cur = self._current_method_id()
        self.cb_method.blockSignals(True)
        self.cb_method.clear()
        for gid, mids in GROUPS:
            for mid in mids:
                self.cb_method.addItem(f"{group_name(gid)} — {method_name(mid)}", mid)
        idx = self.cb_method.findData(cur)
        self.cb_method.setCurrentIndex(idx if idx >= 0 else 0)
        self.cb_method.blockSignals(False)

    def _current_method_id(self) -> str:
        data = self.cb_method.currentData()
        return str(data) if data else self._last_method

    def _current_elastic(self) -> ElasticParams | None:
        """由界面输入组装弹性参数；全部为 0 时视为不启用。"""
        a = self.sp_a.value()
        c11, c12, c44 = self.sp_c11.value(), self.sp_c12.value(), self.sp_c44.value()
        if min(a, c11, c44) <= 0:
            return None
        lat = ("fcc", "bcc", "simple")[max(0, self.cb_lattice.currentIndex())]
        return ElasticParams(a=a, c11=c11, c12=c12, c44=c44, lattice=lat)

    def _on_method_changed(self) -> None:
        self._last_method = self._current_method_id()
        spec = spec_of(self._last_method)
        self.ck_group.setEnabled(spec.supports_grouping)
        self._schedule()

    def _on_preset_changed(self) -> None:
        name = self.cb_preset.currentData()
        if not name:
            return
        p = PRESETS[name]
        self.sp_a.setValue(p.a)
        self.sp_c11.setValue(p.c11)
        self.sp_c12.setValue(p.c12)
        self.sp_c44.setValue(p.c44)
        idx = ("fcc", "bcc", "simple").index(p.lattice)
        self.cb_lattice.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    def _build_tabs(self) -> QWidget:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # --- 谢乐法 ---
        self.tab_scherrer = QWidget()
        v1 = QVBoxLayout(self.tab_scherrer)
        v1.setContentsMargins(6, 6, 6, 6)
        v1.setSpacing(6)
        self.canvas_pattern = PatternCanvas()
        self.canvas_pattern.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txt_scherrer = QTextBrowser()
        self.txt_scherrer.setMaximumHeight(150)
        self.txt_scherrer.setOpenExternalLinks(False)
        self.txt_scherrer.setStyleSheet(
            "QTextBrowser{border:1px solid #E2E8F0;border-radius:6px;background:#FCFCFD;}")
        v1.addWidget(self.canvas_pattern, 1)
        v1.addWidget(self.txt_scherrer)
        self.tabs.addTab(self.tab_scherrer, "")

        # --- W-H ---
        self.tab_wh = QWidget()
        v2 = QVBoxLayout(self.tab_wh)
        v2.setContentsMargins(6, 6, 6, 6)
        v2.setSpacing(6)
        self.canvas_wh = WHCanvas()
        self.txt_wh = QTextBrowser()
        self.txt_wh.setMaximumHeight(150)
        self.txt_wh.setStyleSheet(
            "QTextBrowser{border:1px solid #E2E8F0;border-radius:6px;background:#FCFCFD;}")
        v2.addWidget(self.canvas_wh, 1)
        v2.addWidget(self.txt_wh)
        self.tabs.addTab(self.tab_wh, "")

        # --- 标样与仪器线宽 ---
        self.tab_inst = QWidget()
        v3 = QVBoxLayout(self.tab_inst)
        v3.setContentsMargins(6, 6, 6, 6)
        v3.setSpacing(6)
        self.canvas_std = StandardCanvas()
        self.txt_inst = QTextBrowser()
        self.txt_inst.setStyleSheet(
            "QTextBrowser{border:1px solid #E2E8F0;border-radius:6px;background:#FCFCFD;}")
        v3.addWidget(self.canvas_std, 1)
        v3.addWidget(self.txt_inst, 1)
        self.tabs.addTab(self.tab_inst, "")

        # --- 方法对比（v2.0.0：5 组 7 种）---
        self.tab_methods = QWidget()
        v4 = QVBoxLayout(self.tab_methods)
        v4.setContentsMargins(6, 6, 6, 6)
        v4.setSpacing(6)
        self.tbl_methods = QTableWidget(0, 6)
        self.tbl_methods.verticalHeader().setVisible(False)
        self.tbl_methods.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_methods.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_methods.setMinimumHeight(230)
        mh = self.tbl_methods.horizontalHeader()
        for col, mode in enumerate((QHeaderView.ResizeToContents, QHeaderView.ResizeToContents,
                                    QHeaderView.ResizeToContents, QHeaderView.ResizeToContents,
                                    QHeaderView.ResizeToContents, QHeaderView.Stretch)):
            mh.setSectionResizeMode(col, mode)
        self.txt_method = QTextBrowser()
        self.txt_method.setOpenExternalLinks(False)
        self.txt_method.setStyleSheet(
            "QTextBrowser{border:1px solid #E2E8F0;border-radius:6px;background:#FCFCFD;}")
        v4.addWidget(self.tbl_methods)
        v4.addWidget(self.txt_method, 1)
        self.tabs.addTab(self.tab_methods, "")
        return self.tabs

    # ------------------------------------------------------------------
    def _build_actions(self) -> None:
        bar = self.menuBar()
        self.menu_file = bar.addMenu("")
        self.act_sample = QAction(self)
        self.act_sample.triggered.connect(self.load_sample)
        self.menu_file.addAction(self.act_sample)
        self.act_standard = QAction(self)
        self.act_standard.triggered.connect(self.load_standard)
        self.menu_file.addAction(self.act_standard)
        self.menu_file.addSeparator()
        self.act_html = QAction(self)
        self.act_html.triggered.connect(self.export_report)
        self.menu_file.addAction(self.act_html)
        self.act_csv = QAction(self)
        self.act_csv.triggered.connect(self.export_csv)
        self.menu_file.addAction(self.act_csv)
        self.menu_file.addSeparator()
        self.act_exit = QAction(self)
        self.act_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.act_exit)

        # 语言菜单：互斥、可勾选，原生语言名显示（任何界面语言下不变）
        self.menu_language = bar.addMenu("")
        self._lang_group = QActionGroup(self)
        self._lang_group.setExclusive(True)
        self.act_langs: dict[str, QAction] = {}
        for code, name in available_languages().items():
            act = QAction(name, self)
            act.setCheckable(True)
            act.triggered.connect(lambda _checked=False, c=code: self._on_language(c))
            self._lang_group.addAction(act)
            self.act_langs[code] = act
            self.menu_language.addAction(act)

        self.menu_help = bar.addMenu("")
        self.act_method = QAction(self)
        self.act_method.triggered.connect(self.show_method)
        self.menu_help.addAction(self.act_method)
        self.menu_help.addSeparator()
        self.act_copyright = QAction(self)
        self.act_copyright.triggered.connect(self.show_copyright)
        self.menu_help.addAction(self.act_copyright)
        self.act_about = QAction(self)
        self.act_about.triggered.connect(self.show_about)
        self.menu_help.addAction(self.act_about)
        # 注册版：帮助菜单追加「输入注册码 (&R)…」（内部评估版无此入口）
        if self._reg is not None:
            self.menu_help.addSeparator()
            self._reg.add_help_action(self.menu_help, self)

    # ------------------------------------------------------------------
    # 多语言
    # ------------------------------------------------------------------
    def retranslateUi(self) -> None:
        """语言切换后刷新全部文案（菜单/按钮/表头/标签/状态栏/画布）。"""
        self.setWindowTitle(f"{APP_NAME} v{__version__} — {tr('win.title')}")

        self.menu_file.setTitle(tr("menu.file"))
        self.act_sample.setText(tr("menu.open_sample"))
        self.act_standard.setText(tr("menu.open_standard"))
        self.act_html.setText(tr("menu.export_html"))
        self.act_csv.setText(tr("menu.export_csv"))
        self.act_exit.setText(tr("menu.exit"))
        self.menu_language.setTitle(tr("menu.language"))
        for code, act in self.act_langs.items():
            act.setChecked(code == current_language())
        self.menu_help.setTitle(tr("menu.help"))
        self.act_method.setText(tr("menu.method"))
        self.act_copyright.setText(tr("menu.copyright"))
        self.act_about.setText(tr("menu.about", name=APP_SHORT))

        self.btn_sample.setText(tr("btn.sample"))
        self.btn_std.setText(tr("btn.standard"))
        self.btn_clear_std.setText(tr("btn.clear_std"))
        self.btn_recalc.setText(tr("btn.recalc"))
        self.btn_report.setText(tr("btn.report"))
        self.btn_csv.setText(tr("btn.csv"))

        self.box_params.setTitle(tr("group.params"))
        self.box_corr.setTitle(tr("group.corr"))
        self.box_peaks.setTitle(tr("group.peaks"))
        for lbl, key in self._param_rows:
            lbl.setText(tr(key))
        self.sp_peaks.setSuffix(tr("suffix.peaks"))
        self.sp_window.setSuffix(" °")
        self.ck_ka2.setText(tr("param.ka2"))
        self.ck_ka2.setToolTip(tr("param.ka2_tip"))
        self.sp_prom.setToolTip(tr("param.prom_tip"))
        # 口径下拉框：重建条目并保住当前选择
        mode_idx = self.cb_mode.currentIndex()
        self.cb_mode.blockSignals(True)
        self.cb_mode.clear()
        self.cb_mode.addItems([tr("mode.fwhm"), tr("mode.integral")])
        self.cb_mode.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.cb_mode.blockSignals(False)

        self.tabs.setTabText(0, tr("tab.scherrer"))
        self.tabs.setTabText(1, tr("tab.wh"))
        self.tabs.setTabText(2, tr("tab.inst"))
        self.tabs.setTabText(3, tr("tab.methods"))
        self.tbl.setHorizontalHeaderLabels(["", "2θ (°)", "D (nm)", tr("th.note")])
        self.tbl_methods.setHorizontalHeaderLabels([
            tr("rep.m_th_method"), tr("rep.m_th_group"), tr("rep.m_th_size"),
            tr("rep.m_th_sec"), tr("rep.m_th_r2"), tr("rep.m_th_status")])

        # 方法面板：条目文案随语言重建，保住当前选择
        self.box_method.setTitle(tr("group.method"))
        for lbl, key in self._method_rows:
            lbl.setText(tr(key))
        self._fill_method_combo()
        self.ck_group.setToolTip(tr("param.group_dir_tip"))
        self.ck_group.setEnabled(spec_of(self._current_method_id()).supports_grouping)
        self.btn_guide.setText(tr("btn.method_guide"))
        preset_idx = self.cb_preset.currentIndex()
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem(tr("param.preset_none"), "")
        for name in PRESETS:
            self.cb_preset.addItem(PRESETS[name].label or name, name)
        self.cb_preset.setCurrentIndex(preset_idx if preset_idx >= 0 else 0)
        self.cb_preset.blockSignals(False)
        lat_idx = self.cb_lattice.currentIndex()
        self.cb_lattice.blockSignals(True)
        self.cb_lattice.clear()
        self.cb_lattice.addItems([tr("param.lattice_fcc"), tr("param.lattice_bcc"),
                                  tr("param.lattice_simple")])
        self.cb_lattice.setCurrentIndex(lat_idx if lat_idx >= 0 else 0)
        self.cb_lattice.blockSignals(False)
        self.sp_a.setSuffix(" Å")
        for sp in (self.sp_c11, self.sp_c12, self.sp_c44):
            sp.setSuffix(" GPa")

        if self._badge is not None:
            self._status_bar.set_badge_text(tr("edition.internal"))

        # 样品/标样标签与角度校正行（有数据时按数据重排，无数据用占位文案）
        if self.sample is not None:
            self._set_sample_label()
        else:
            self.lbl_sample.setText(tr("lbl.sample_none"))
        if self.standard is not None:
            self._set_std_label()
        else:
            self.lbl_std.setText(tr("lbl.std_none"))

        b = self.bundle
        if b is not None:
            if b.instrument is not None:
                self.lbl_corr.setText(b.instrument.correction.describe())
            else:
                self.lbl_corr.setText(tr("corr.lbl_none_full"))
            # core 的警告/质量标记是计算时生成的，重算以整体刷新语言
            self.recompute()
        else:
            self.lbl_corr.setText(tr("corr.lbl_none"))
            # 空状态画布上的提示文字也要跟着换
            self.canvas_pattern.set_bundle(None)
            self.canvas_wh.set_bundle(None)
            self.canvas_std.set_instrument(None)
            self._fill_summaries(None)
            self._fill_method_tab(None)

    def _on_language(self, code: str) -> None:
        set_language(code)
        save_language(code)
        self.retranslateUi()
        # 注册版：同步注册模块文案并重刷新状态栏标签（已注册单位名/未注册）
        if self._reg is not None:
            registration.set_language(_REG_LANG.get(code, "zh"))
            self._reg.refresh()

    def _status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    # ------------------------------------------------------------------
    # 文件
    # ------------------------------------------------------------------
    def _filters(self) -> str:
        exts = " ".join(f"*{e}" for e in SUPPORTED_EXTS)
        return f"{tr('filter.patterns', exts=exts)};;{tr('filter.all')}"

    def _set_sample_label(self) -> None:
        assert self.sample is not None
        self.lbl_sample.setText(tr("lbl.sample_info", label=self.sample.label,
                                   n=self.sample.n, lo=self.sample.range[0],
                                   hi=self.sample.range[1],
                                   wl=self.sample.wavelength))

    def _set_std_label(self) -> None:
        assert self.standard is not None
        self.lbl_std.setText(tr("lbl.std_info", label=self.standard.label,
                                n=self.standard.n))

    def load_sample(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.choose_sample"), "", self._filters())
        if not path:
            return
        try:
            self.sample = read_pattern(path)
        except Exception as exc:
            QMessageBox.critical(self, tr("dlg.read_fail"),
                                 f"{os.path.basename(path)}\n\n{exc}")
            return
        self._set_sample_label()
        self.lbl_sample.setToolTip(path)
        self.recompute()

    def load_standard(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.choose_standard"), "", self._filters())
        if not path:
            return
        try:
            self.standard = read_pattern(path)
        except Exception as exc:
            QMessageBox.critical(self, tr("dlg.read_fail"),
                                 f"{os.path.basename(path)}\n\n{exc}")
            return
        self._set_std_label()
        self.lbl_std.setToolTip(path)
        if self.sample is not None:
            self.recompute()
        else:
            self._status(tr("dlg.std_loaded"))

    def clear_standard(self) -> None:
        self.standard = None
        self.lbl_std.setText(tr("lbl.std_none"))
        self.lbl_std.setToolTip("")
        if self.sample is not None:
            self.recompute()

    # ------------------------------------------------------------------
    # 计算
    # ------------------------------------------------------------------
    def _schedule(self) -> None:
        if self.sample is None:
            return
        QTimer.singleShot(220, self.recompute)

    def _on_mode_changed(self) -> None:
        # 口径切换时同步 K 的默认值，用户可再手改
        self.sp_K.setValue(0.89 if self.cb_mode.currentIndex() == 0 else 1.0)
        self._schedule()

    def current_config(self) -> AnalysisConfig:
        return AnalysisConfig(
            n_peaks=self.sp_peaks.value(),
            window_max=self.sp_window.value(),
            strip_ka2=self.ck_ka2.isChecked(),
            width_mode="fwhm" if self.cb_mode.currentIndex() == 0 else "integral",
            K=self.sp_K.value(),
            min_prominence_frac=self.sp_prom.value(),
            method=self._current_method_id(),
            group_by_direction=self.ck_group.isChecked() and self.ck_group.isEnabled(),
            elastic=self._current_elastic(),
        )

    def recompute(self) -> None:
        if self.sample is None:
            return
        try:
            self.setCursor(Qt.WaitCursor)
            self.bundle = run_analysis(self.sample, self.standard, self.current_config())
        except Exception as exc:
            self.unsetCursor()
            QMessageBox.warning(self, tr("dlg.calc_fail"), str(exc))
            self._status(f"{tr('dlg.calc_fail')}: {exc}")
            return
        finally:
            self.unsetCursor()
        self.refresh_views()

    def refit_selected(self) -> None:
        """按勾选的峰重算（保留仪器模型，速度更快）。"""
        if self.bundle is None:
            return
        positions = []
        for row in range(self.tbl.rowCount()):
            item = self.tbl.item(row, 0)
            if item is not None and item.checkState() == Qt.Checked:
                positions.append(float(self.tbl.item(row, 1).text().replace("°", "")))
        if len(positions) < 2:
            self._status(tr("dlg.min_peaks"))
            return
        try:
            self.bundle = refit_with_positions(self.bundle, positions, self.current_config())
        except Exception as exc:
            QMessageBox.warning(self, tr("dlg.refit_fail"), str(exc))
            return
        self.refresh_views(rebuild_table=False)

    # ------------------------------------------------------------------
    # 视图刷新
    # ------------------------------------------------------------------
    def refresh_views(self, rebuild_table: bool = True) -> None:
        b = self.bundle
        if b is None:
            return
        if rebuild_table:
            self._fill_table(b)
        self.canvas_pattern.set_bundle(b, self._active_row())
        self.canvas_wh.set_bundle(b)
        self.canvas_std.set_instrument(b.instrument)
        self._fill_summaries(b)
        self._fill_method_tab(b)

        if b.instrument is not None:
            self.lbl_corr.setText(b.instrument.correction.describe())
        else:
            self.lbl_corr.setText(tr("corr.lbl_none_full"))
        s = b.scherrer
        extra = "" if b.corrected else tr("status.uncorrected")
        self._status(tr("status.done", valid=s.n_valid, total=len(s.peaks),
                        mean=_fmt(s.mean_number, 2), extra=extra))

    def _active_row(self) -> int:
        rows = self.tbl.selectionModel().selectedRows() if self.tbl.selectionModel() else []
        return int(rows[0].row()) if rows else 0

    def _fill_table(self, b: AnalysisBundle) -> None:
        self._loading_table = True
        try:
            self.tbl.setRowCount(len(b.scherrer.peaks))
            for i, p in enumerate(b.scherrer.peaks):
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                chk.setCheckState(Qt.Checked if p.ok else Qt.Unchecked)
                self.tbl.setItem(i, 0, chk)

                it = QTableWidgetItem(f"{p.two_theta:.3f}°")
                it.setFont(MONO)
                self.tbl.setItem(i, 1, it)

                it2 = QTableWidgetItem(_fmt(p.size_nm, 2))
                it2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it2.setFont(MONO)
                self.tbl.setItem(i, 2, it2)

                note = ""
                color = None
                if p.flag == "instrument_exceeds":
                    note = tr("note.instrument_exceeds")
                    color = QColor("#B91C1C")
                elif p.flag == "unreliable":
                    note = tr("note.unreliable")
                    color = QColor("#B45309")
                elif p.flag == "no_standard":
                    note = tr("note.no_std")
                    color = QColor("#B45309")
                elif p.quality:
                    note = p.quality[0]
                it3 = QTableWidgetItem(note)
                if color:
                    it3.setForeground(color)
                it3.setToolTip("；".join(p.quality) or note)
                self.tbl.setItem(i, 3, it3)
            if self.tbl.rowCount():
                self.tbl.selectRow(0)
        finally:
            self._loading_table = False

    def _on_table_changed(self, item: QTableWidgetItem) -> None:
        if self._loading_table or item.column() != 0:
            return
        self.refit_selected()

    def _on_row_selected(self) -> None:
        if self.bundle is None:
            return
        self.canvas_pattern.set_active(self._active_row())

    # ------------------------------------------------------------------
    def _fill_summaries(self, b: AnalysisBundle | None) -> None:
        if b is None:
            self.txt_scherrer.setHtml("")
            self.txt_wh.setHtml("")
            self.txt_inst.setHtml(f"""
<div style="font-family:'{UI_FONT}';color:{MUTED};font-size:12.5px;padding:8px;">
{tr('sum.inst.empty')}</div>""")
            return

        s = b.scherrer
        wh = b.wh
        warns = b.warnings()
        head = "".join(f'<div style="color:{WARN_AMBER};font-size:12px;">⚠ {w}</div>' for w in warns) \
            or f'<div style="color:{OK_GREEN};font-size:12px;">{tr("sum.no_warn")}</div>'
        mode_txt = tr("sum.mode.fwhm") if s.width_mode == "fwhm" else tr("sum.mode.integral")
        corr_txt = tr("sum.corr.done") if b.corrected else tr("sum.corr.none")

        self.txt_scherrer.setHtml(f"""
<div style="font-family:'{UI_FONT}';">
<div style="font-size:12px;color:{MUTED};">{tr('sum.scherrer.head', total=len(s.peaks), valid=s.n_valid)}</div>
<div><span style="font-size:26px;font-weight:700;color:{BRAND};">{_fmt(s.mean_number, 2)}</span>
<span style="font-size:13px;color:{MUTED};"> nm</span>
<span style="font-size:12px;color:{MUTED};">&nbsp;&nbsp;{tr('sum.scherrer.stats', di=_fmt(s.mean_intensity, 2), dv=_fmt(s.mean_volume, 2), sp=_fmt(s.spread(), 0))}</span></div>
<div style="font-size:12px;color:{MUTED};margin-top:4px;">
{tr('sum.scherrer.model', mode=mode_txt, K=s.K, wl=s.wavelength, corr=corr_txt)}</div>
<div style="margin-top:6px;">{head}</div>
</div>""")

        self.txt_wh.setHtml(f"""
<div style="font-family:'{UI_FONT}';">
<div style="font-size:12px;color:{MUTED};">{tr('sum.wh.head')}</div>
<div><span style="font-size:26px;font-weight:700;color:{BRAND};">{_fmt(wh.size_nm, 2)}</span>
<span style="font-size:13px;color:{MUTED};"> nm</span>
<span style="font-size:12px;color:{MUTED};">&nbsp;&nbsp;{tr('sum.wh.stats', e=_fmt(wh.strain_pct, 3), r2=_fmt(wh.r2, 3), n=wh.n_valid)}</span></div>
<div style="font-size:12px;color:{MUTED};margin-top:4px;">
{tr('sum.wh.detail', slope=_sci(wh.slope), intercept=_sci(wh.intercept), mean=_fmt(wh.mean_size_nm, 2))}
<span style="color:{FAINT};">{tr('sum.wh.note')}</span></div>
<div style="margin-top:6px;">{head}</div>
</div>""")

        inst = b.instrument
        if inst is not None and inst.usable:
            U, V, W = inst.U, inst.V, inst.W
            rows = "".join(
                f"<tr><td>{p.position:.3f}</td><td>{p.position_raw:.3f}</td>"
                f"<td>{p.fwhm:.4f}</td><td>{inst.fwhm_at(p.position):.4f}</td>"
                f"<td>{p.eta:.2f}</td><td>{p.rwp:.1f}</td></tr>"
                for p in inst.peaks if p.ok)
            method_txt = tr("sum.inst.caglioti") if inst.method == "caglioti" else tr("sum.inst.pchip")
            self.txt_inst.setHtml(f"""
<div style="font-family:'{UI_FONT}';font-size:12.5px;">
<div style="font-size:12px;color:{MUTED};">{tr('sum.inst.head', name=inst.standard_name or tr('sum.inst.unknown'))}</div>
<div style="margin:4px 0;"><b>{method_txt}</b>
{tr('sum.inst.coef', u=_sci(U), v=_sci(V), w=_sci(W), r2=f'{inst.r2:.3f}', rms=f'{inst.rms:.4f}')}</div>
<div style="color:{MUTED};">{inst.note}</div>
<div style="margin:6px 0;color:{MUTED};">{tr('sum.inst.corr', desc=inst.correction.describe())}</div>
<table border="1" cellspacing="0" cellpadding="3" style="border-collapse:collapse;font-size:12px;color:{INK};border-color:{LINE};">
<tr style="background:#F8FAFC;color:#475569;"><th>{tr('sum.inst.th_corr')}</th><th>{tr('sum.inst.th_obs')}</th><th>{tr('sum.inst.th_fwhm_obs')}</th>
<th>{tr('sum.inst.th_fwhm_model')}</th><th>η</th><th>Rwp%</th></tr>{rows}</table>
</div>""")
        else:
            self.txt_inst.setHtml(f"""
<div style="font-family:'{UI_FONT}';color:{MUTED};font-size:12.5px;padding:8px;">
{tr('sum.inst.empty')}</div>""")

    # ------------------------------------------------------------------
    # 方法对比（5 组 7 种）
    # ------------------------------------------------------------------
    def _fill_method_tab(self, b: AnalysisBundle | None) -> None:
        if b is None or not b.outcomes:
            self.tbl_methods.setRowCount(0)
            self.txt_method.setHtml(
                f'<div style="font-family:\'{UI_FONT}\';color:{MUTED};font-size:12.5px;'
                f'padding:8px;">{tr("dlg.need_compute")}</div>')
            return

        rows = []
        for mid in METHOD_IDS:
            o = b.outcomes.get(mid)
            if o is None:
                continue
            rows.append((mid, o))
        self.tbl_methods.setRowCount(len(rows))
        for i, (mid, o) in enumerate(rows):
            self.tbl_methods.setItem(i, 0, QTableWidgetItem(method_name(mid)))
            self.tbl_methods.setItem(i, 1, QTableWidgetItem(group_name(spec_of(mid).group)))
            it = QTableWidgetItem(_fmt(o.size_nm, 2))
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(MONO)
            self.tbl_methods.setItem(i, 2, it)
            sec = "" if o.secondary_kind == "none" or not np.isfinite(o.secondary) \
                else f"{o.secondary:.3f} {o.secondary_unit}"
            it = QTableWidgetItem(sec)
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_methods.setItem(i, 3, it)
            it = QTableWidgetItem(_fmt(o.r2, 3))
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_methods.setItem(i, 4, it)
            if not o.available:
                state, color = tr("m.status.unavailable"), QColor("#B91C1C")
            elif o.reason:
                state, color = tr("m.status.degraded"), QColor("#B45309")
            else:
                state, color = tr("m.status.ok"), QColor("#15803D")
            if o.reason:
                state += f"（{o.reason}）"
            st = QTableWidgetItem(state)
            st.setForeground(color)
            self.tbl_methods.setItem(i, 5, st)
            if mid == b.active_method:
                for c in range(6):
                    item = self.tbl_methods.item(i, c)
                    if item is not None:
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)

        mid = b.active_method
        o = b.outcomes.get(mid)
        sec_line = ""
        if o is not None and o.secondary_kind != "none" and np.isfinite(o.secondary):
            sec_line = (f'<div><span style="font-size:20px;font-weight:700;color:{BRAND};">'
                        f'{o.secondary:.3f}</span>'
                        f'<span style="font-size:12px;color:{MUTED};"> {o.secondary_unit}'
                        f'（{o.secondary_label}）</span></div>')
        warn_html = "".join(
            f'<div style="color:{WARN_AMBER};font-size:12px;">⚠ {w}</div>'
            for w in (o.warnings if o else []))
        self.txt_method.setHtml(f"""
<div style="font-family:'{UI_FONT}';font-size:12.5px;">
<div style="font-size:12px;color:{MUTED};">{tr('sum.method.head')}</div>
<div><b style="font-size:14px;">{method_name(mid)}</b>
<span style="color:{MUTED};">（{group_name(spec_of(mid).group)}）</span></div>
<div><span style="font-size:26px;font-weight:700;color:{BRAND};">{_fmt(o.size_nm if o else None, 2)}</span>
<span style="font-size:13px;color:{MUTED};"> nm</span></div>
{sec_line}
<div style="margin-top:6px;color:{INK};">
<b>{tr('m.head.assume')}</b>：{method_assume(mid)}<br>
<b>{tr('m.head.need')}</b>：{method_need(mid)}<br>
<b>{tr('m.head.scene')}</b>：{method_scene(mid)}<br>
<b>{tr('m.head.limit')}</b>：{method_limit(mid)}
</div>
<div style="margin-top:6px;">{warn_html}</div>
</div>""")

    # ------------------------------------------------------------------
    # 导出
    # ------------------------------------------------------------------
    def export_report(self) -> None:
        if self.bundle is None:
            QMessageBox.information(self, tr("dlg.info"), tr("dlg.need_compute"))
            return
        default = tr("fname.report", label=self.bundle.sample.label or "sample")
        path, _ = QFileDialog.getSaveFileName(self, tr("dlg.save_html"), default, "HTML (*.html)")
        if not path:
            return
        try:
            html_text = build_html(self.bundle)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_text)
        except Exception as exc:
            QMessageBox.critical(self, tr("dlg.export_fail"),
                                 f"{exc}\n\n{traceback.format_exc(limit=2)}")
            return
        self._status(f"{tr('dlg.save_html')}: {path}")
        if QMessageBox.question(self, tr("dlg.export_done"), tr("dlg.open_now"),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QDesktopServices.openUrl(f"file:///{path}")

    def export_csv(self) -> None:
        if self.bundle is None:
            QMessageBox.information(self, tr("dlg.info"), tr("dlg.need_compute"))
            return
        default = tr("fname.csv", label=self.bundle.sample.label or "sample")
        path, _ = QFileDialog.getSaveFileName(self, tr("dlg.save_csv"), default, "CSV (*.csv)")
        if not path:
            return
        b = self.bundle
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow([tr("csv.h_2th"), tr("csv.h_d"), tr("csv.h_fwhm_obs"),
                            tr("csv.h_fwhm_inst"), tr("csv.h_beta"), tr("csv.h_D"),
                            tr("csv.h_eta"), tr("csv.h_rwp"), tr("csv.h_status"),
                            tr("csv.h_quality")])
                for i, p in enumerate(b.scherrer.peaks):
                    fit = b.fits[i] if i < len(b.fits) else None
                    w.writerow([f"{p.two_theta:.4f}", f"{p.d:.5f}", f"{p.fwhm_obs:.4f}",
                                _fmt(p.fwhm_inst, 4), _fmt(p.beta_deg, 4),
                                _fmt(p.size_nm, 3), f"{p.eta:.3f}",
                                _fmt(fit.rwp if fit else None, 2),
                                tr("csv.ok") if p.ok else p.flag, "；".join(p.quality)])
                w.writerow([])
                s = b.scherrer
                w.writerow([tr("csv.mean_n"), _fmt(s.mean_number, 3)])
                w.writerow([tr("csv.mean_i"), _fmt(s.mean_intensity, 3)])
                w.writerow([tr("csv.mean_v"), _fmt(s.mean_volume, 3)])
                w.writerow([tr("csv.spread"), _fmt(s.spread(), 2)])
                w.writerow([tr("csv.wh_d"), _fmt(b.wh.size_nm, 3)])
                w.writerow([tr("csv.wh_strain"), _fmt(b.wh.strain_pct, 4)])
                w.writerow([tr("csv.wh_r2"), _fmt(b.wh.r2, 4)])
                w.writerow([tr("csv.instr_corr"),
                            tr("csv.corrected") if b.corrected else tr("csv.uncorrected")])
                if b.instrument is not None:
                    w.writerow(["U(deg²)", f"{b.instrument.U:.6e}"])
                    w.writerow(["V(deg²)", f"{b.instrument.V:.6e}"])
                    w.writerow(["W(deg²)", f"{b.instrument.W:.6e}"])
                # v2.0.0：7 种方法横向对比（同一组峰拟合，非独立重算）
                w.writerow([])
                w.writerow([tr("csv.h_method"), tr("rep.m_th_group"),
                            tr("rep.m_th_size"), tr("rep.m_th_sec"),
                            tr("rep.m_th_r2"), tr("rep.m_th_n")])
                for mid in METHOD_IDS:
                    o = b.outcomes.get(mid)
                    if o is None:
                        continue
                    sec = "" if (o.secondary_kind == "none"
                                 or not np.isfinite(o.secondary)) else f"{o.secondary:.4f}"
                    w.writerow([method_name(mid), group_name(spec_of(mid).group),
                                _fmt(o.size_nm, 3), sec, _fmt(o.r2, 4), o.n_used])
        except Exception as exc:
            QMessageBox.critical(self, tr("dlg.export_fail"), str(exc))
            return
        self._status(f"{tr('dlg.save_csv')}: {path}")

    # ------------------------------------------------------------------
    def show_method(self) -> None:
        QMessageBox.information(self, tr("method.title"), tr("method.body"))

    def show_method_guide(self) -> None:
        """5 组 7 种方法的选择场景说明。"""
        QMessageBox.information(self, tr("method2.title"), tr("method2.body"))

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def show_copyright(self) -> None:
        CopyrightDialog(self).exec()
