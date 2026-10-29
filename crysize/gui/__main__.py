"""GUI 入口：``python -m crysize.gui``。

启动次序与家族一致：
``QSplashScreen(resources/splash-screen.png)`` → 建主窗口 → ``show()`` →
才挂关闭启动图的定时器。这个顺序不能反：若先挂定时器，冷启动（matplotlib
字体缓存、首次 .pyc）期间一旦事件循环处理到该定时器，启动图会在主窗口显形前
关闭，此时"最后一个窗口已关闭" 触发 quitOnLastWindowClosed，进程直接退出 ——
表现为"闪退且不留任何日志"（家族 v0.15.2 实证）。

打包态（PyInstaller onefile）下 bootloader 解压阶段由 spec 的 ``Splash`` 显示
同图启动画面（冷启动即显），主窗口 show 后由 :func:`_close_boot_splash` 关闭该
下层启动图，与 QSplashScreen（上层）视觉连续；开发态无 ``pyi_splash`` 模块，
行为与家族其它工具一致。
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from crysize.gui.resources import app_icon_path, splash_path
from crysize.gui.theme import UI_FONT
from crysize.version import APP_NAME, __version__

#: 启动图最短展示时长（毫秒）；主窗口已显示时按下限收掉
SPLASH_MS = 900


def _close_boot_splash() -> None:
    """关闭 PyInstaller bootloader 启动图（仅打包态存在 pyi_splash）。"""
    try:
        import pyi_splash       # type: ignore[import-not-found]

        pyi_splash.close()
    except Exception:
        pass                    # 开发态无该模块 —— 静默跳过


def _make_splash(app: QApplication) -> QSplashScreen | None:
    """建启动图；资源缺失或图片损坏时返回 None（绝不阻塞启动）。"""
    path = splash_path()
    if not path:
        return None
    try:
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return None
        # 磁盘上已是 480×270 预缩放图；只有拿到更大的图才缩放（省一次重采样）
        if pixmap.width() > 480 or pixmap.height() > 270:
            pixmap = pixmap.scaled(
                480, 270,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
        splash = QSplashScreen(pixmap)
        splash.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        splash.show()
        app.processEvents()
        return splash
    except Exception:           # noqa: BLE001 - 启动图失败不能拦住主窗口
        return None


def main(argv: list[str] | None = None) -> int:
    """创建应用、启动图与主窗口，进入事件循环。"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setFont(QFont(UI_FONT, 9))

    icon = app_icon_path()
    if icon:
        app.setWindowIcon(QIcon(icon))

    splash = _make_splash(app)

    # 延迟导入主窗口，让启动图先出现
    from crysize.gui.main_window import MainWindow

    win = MainWindow()
    win.show()
    _close_boot_splash()

    if splash is not None:
        # 关闭动作统一放在 window.show() 之后（顺序原因见模块 docstring）
        QTimer.singleShot(SPLASH_MS, splash.close)

    # 命令行直接带谱图路径：python -m crysize.gui sample.txt [standard.txt]
    args = [a for a in (argv or sys.argv)[1:] if not a.startswith("-")]
    if args:
        from crysize.core.pattern import read_pattern
        try:
            win.sample = read_pattern(args[0])
            win.lbl_sample.setText(f"样品：{win.sample.label}")
            if len(args) > 1:
                win.standard = read_pattern(args[1])
                win.lbl_std.setText(f"标样：{win.standard.label}")
            win.recompute()
        except Exception as exc:  # 启动失败不应静默
            win.statusBar().showMessage(f"命令行文件载入失败：{exc}")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
