"""版次标识：registered=注册版（Setup 安装包）| internal=内部评估版（单文件 exe）。

默认 registered（源码运行即注册版行为）；打包时经 PyInstaller runtime_hook
（installer/rthook_internal.py）覆写为 internal。

运行期只读：主窗口按 ``edition.IS_INTERNAL`` 决定状态栏是否标「内部评估版本」。
CrySize 目前不含注册校验模块（家族注册服务由 PolyXRD RegTool 提供），
版次只影响标识显示与帮助菜单项，不影响任何计算功能。
"""

EDITION = "registered"
IS_INTERNAL = EDITION == "internal"

#: 状态栏右侧的版次徽章文字
EDITION_LABEL = "内部评估版本" if IS_INTERNAL else ""
