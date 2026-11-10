# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（PolyXRD 家族模板，参照 PolyXRD-RutAna.spec）。

单文件（onefile）**内部评估版**免安装 exe：
- 入口 crysize/gui/__main__.py（等价于 ``python -m crysize.gui``）；
- datas 携带 resources/（品牌资产：图标、启动图、logo、横幅）；
- bootloader Splash 启动画面（resources/splash-screen.png，480×270）：
  onefile 解压阶段即显示，主窗口 show() 后由 __main__._close_boot_splash
  调 ``pyi_splash.close()`` 关闭，与上层 QSplashScreen 视觉连续；
- ``runtime_hooks=["installer/rthook_internal.py"]`` 把版次覆写为 internal
  （状态栏显示「内部评估版本」）；注册版走 PolyXRD-CrySize-Setup.spec，
  不加该 hook；
- 版本号从 crysize/version.py 读取，exe 名与 build_exe.bat 的副本逻辑对应。
"""

import re
from pathlib import Path

_ver = re.search(
    r'__version__\s*=\s*"([^"]+)"',
    Path("crysize/version.py").read_text(encoding="utf-8"),
).group(1)

datas = [("resources", "resources")]
if Path("data").is_dir() and any(Path("data").iterdir()):
    datas.append(("data", "data"))

a = Analysis(
    ["crysize/gui/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "crysize",
        "crysize.version",
        "crysize.edition",
        "crysize.registration",
        # i18n（三语翻译表必须显式收集，否则运行时缺表）
        "crysize.i18n",
        "crysize.i18n.i18n_manager",
        "crysize.i18n.translations.zh_CN",
        "crysize.i18n.translations.en_US",
        "crysize.i18n.translations.ja_JP",
        # core 算法模块（含 5 个峰的局部联合拟合、仪器模型、标样识别）
        "crysize.core.analysis",
        "crysize.core.instrument",
        "crysize.core.pattern",
        "crysize.core.peaks",
        "crysize.core.profile",
        "crysize.core.size",
        "crysize.core.standards",
        # gui 层（主窗口内均为静态 import，此处显式补全作双保险）
        "crysize.gui.canvas",
        "crysize.gui.dialogs",
        "crysize.gui.main_window",
        "crysize.gui.report",
        "crysize.gui.resources",
        "crysize.gui.theme",
    ],
    hookspath=[],
    hooksconfig={},
    # 内部评估版：运行时把版次覆写为 internal（状态栏徽章）
    runtime_hooks=["installer/rthook_internal.py"],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# bootloader 启动画面 —— onefile 解压阶段（数秒）即显示品牌图。
# 图上已烙品牌与版本号，故 text_pos=None 不叠加文本。
splash = Splash(
    "resources/splash-screen.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    min_font_color="white",
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    # bootloader splash 的运行时依赖（tcl86t.dll/tk86t.dll 与 _tcl_data/_tk_data
    # 脚本树）：必须作为独立 TOC 参数传入 EXE，否则 onefile 解压期找不到
    # Tcl/Tk，启动画面静默失败（PyInstaller 官方模板 + 家族实证）。
    splash.binaries,
    [],
    name=f"PolyXRD-CrySize-v{_ver}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["resources/app-icon.ico"],
)
