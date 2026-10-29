"""PyInstaller runtime_hook：内部评估版（单文件 exe，PolyXRD-CrySize.spec）。

在应用代码运行前把版次标识覆写为 internal，使状态栏显示「内部评估版本」；
注册版（Setup 安装包，PolyXRD-CrySize-Setup.spec）不加本 hook，保持默认
registered。与家族 PolyXRD-RutAna/installer/rthook_internal.py 同一实现。
"""

import crysize.edition as _edition

_edition.EDITION = "internal"
_edition.IS_INTERNAL = True
_edition.EDITION_LABEL = "内部评估版本"
