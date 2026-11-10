"""版次标识：registered=注册版（Setup 安装包）| internal=内部评估版（单文件 exe）。

默认 registered（源码运行即注册版行为）；打包时经 PyInstaller runtime_hook
（installer/rthook_internal.py）覆写为 internal。

运行期只读：主窗口按 ``edition.IS_INTERNAL`` 决定状态栏是否标「内部评估版本」，
以及是否启用注册机制（见 crysize/registration.py）。

自 v2.0.1 起，注册版（Setup 安装包）接入 PolyXRD 家族统一注册机制：
未注册时启动提示版权声明，帮助菜单可「输入注册码」自助注册，注册成功后
状态栏最右侧显示「已注册：<单位部门名称>」。内部评估版不启用该机制。
版次只影响标识显示与注册入口，不影响任何计算功能。
"""

EDITION = "registered"
IS_INTERNAL = EDITION == "internal"

#: 状态栏右侧的版次徽章文字
EDITION_LABEL = "内部评估版本" if IS_INTERNAL else ""
