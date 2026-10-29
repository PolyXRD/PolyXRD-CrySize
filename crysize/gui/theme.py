"""家族视觉常量。

家族 GUI 的做法是 **Fusion 样式 + 局部内联样式 + 统一配色常量**（不设全局 QSS）：
这样控件在不同 Windows 主题下保持原生观感，只有需要强调的地方才着色。
这里的常量与 ``tools/build_artwork.py`` 的品牌色、``gui/report.py`` 的 HTML 配色
三处必须一致 —— 任何一处单独改都会让界面、图标、报告出现色差。
"""

from __future__ import annotations

#: 墨黑：正文与坐标轴文字（slate-900）
INK = "#0F172A"
#: 品牌蓝：主色、强调数值、曲线（sky-600）
BRAND = "#0284C7"
#: 子工具强调色（青，与家族其它工具一致）
CYAN = "#22D3EE"
#: 次级文字（slate-500）
MUTED = "#64748B"
#: 分隔线 / 网格（slate-200）
LINE = "#E2E8F0"
#: 更深一档的正文（slate-700）
BODY = "#334155"
#: 弱化文字（slate-400）
FAINT = "#94A3B8"

#: 状态色（与报告一致）
OK_GREEN = "#15803D"
WARN_AMBER = "#B45309"
ERR_RED = "#B91C1C"

#: 特性 chip（关于对话框，家族统一的青色药丸样式）
CHIP_BG = "#ECFEFF"
CHIP_BORDER = "#CFFAFE"
CHIP_TEXT = "#0E7490"

#: UI 字体（家族统一）
UI_FONT = "Microsoft YaHei"
