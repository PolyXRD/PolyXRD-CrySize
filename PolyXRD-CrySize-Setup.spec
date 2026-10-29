# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 —— 注册版（Setup 安装包用 onedir）。

与 PolyXRD-CrySize.spec（内部评估版 onefile）的差异：
- onedir 目录版（COLLECT），供 Inno Setup 打成安装包（installer/PolyXRD-CrySize.iss）；
- 不加 runtime_hook：版次保持 crysize/edition.py 默认 registered；
- exe 名不带版本号（dist/PolyXRD-CrySize/PolyXRD-CrySize.exe），版本号烙在
  安装包文件名与 version.py 里；
- bootloader Splash 启动画面与内部版一致保留。
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
        # i18n（三语翻译表必须显式收集，否则运行时缺表）
        "crysize.i18n",
        "crysize.i18n.i18n_manager",
        "crysize.i18n.translations.zh_CN",
        "crysize.i18n.translations.en_US",
        "crysize.i18n.translations.ja_JP",
        "crysize.core.analysis",
        "crysize.core.instrument",
        "crysize.core.pattern",
        "crysize.core.peaks",
        "crysize.core.profile",
        "crysize.core.size",
        "crysize.core.standards",
        "crysize.gui.canvas",
        "crysize.gui.dialogs",
        "crysize.gui.main_window",
        "crysize.gui.report",
        "crysize.gui.resources",
        "crysize.gui.theme",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# bootloader 启动画面：与内部版一致（图已烙品牌+版本号，不附加文本）。
# onedir 模板：EXE 只挂 splash 对象；splash.binaries 归入 COLLECT。
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
    splash,
    [],
    exclude_binaries=True,
    name="PolyXRD-CrySize",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["resources/app-icon.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PolyXRD-CrySize",
)
