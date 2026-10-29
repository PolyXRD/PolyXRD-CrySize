"""资源路径定位：开发态用 ``<root>/resources``，PyInstaller 打包态用 ``sys._MEIPASS``。

所有 GUI 代码获取图标/启动图/横幅等静态资源都必须经由本模块，使同一份代码在
源码运行与 onefile 打包两种形态下都能正确定位（与家族其它工具同一实现）。
"""

from __future__ import annotations

import sys
from pathlib import Path

#: 资源文件名（与 tools/build_artwork.py 的产出一一对应）
APP_ICON = "app-icon.png"
APP_ICON_ICO = "app-icon.ico"
SPLASH = "splash-screen.png"
LOGO_HORIZONTAL = "logo-horizontal.png"
CRYSTAL_MARK = "crystal-mark.png"
HERO_BANNER = "hero-banner.png"


def app_root() -> Path:
    """项目根目录（开发态）。crysize/gui/resources.py -> 根目录上溯三级。"""
    return Path(__file__).resolve().parent.parent.parent


def _base() -> Path:
    """资源基目录：打包态为解压目录 sys._MEIPASS，开发态为项目根目录。"""
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return Path(meipass)
    return app_root()


def resources_dir() -> Path:
    """品牌资源目录（build_artwork.py 的产物）。"""
    return _base() / "resources"


def resource_path(name: str) -> Path:
    """返回 resources/ 下指定文件名的路径。"""
    return resources_dir() / name


def app_icon_path() -> str:
    """窗口/任务栏图标。

    优先 PNG：Qt6 的 PNG 解码器内建在 Qt6Gui 里，不加载 imageformats 插件；
    ``.ico`` 需加载 ``qico.dll``，在启动阶段多加载插件会提高原生崩溃概率
    （家族实测结论，v0.13.1）。``.ico`` 只留给 exe 资源与安装器。
    """
    for name in (APP_ICON, APP_ICON_ICO):
        p = resource_path(name)
        if p.exists():
            return str(p)
    return ""


def splash_path() -> str:
    """启动图路径（480×270 PNG，内建解码器）。"""
    p = resource_path(SPLASH)
    return str(p) if p.exists() else ""
