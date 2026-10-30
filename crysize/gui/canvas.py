"""图表画布：谱图/拟合放大图、W-H 图、标样线宽曲线。"""

from __future__ import annotations

import matplotlib
import numpy as np

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402

from crysize.core.analysis import AnalysisBundle  # noqa: E402
from crysize.core.wh_models import WHVariantFit  # noqa: E402
from crysize.i18n import tr  # noqa: E402
from crysize.gui.theme import BRAND, FAINT, INK, LINE, MUTED  # noqa: E402

#: 图线专用色（品牌色之外，仅画布内部使用）
GRID = LINE
ACCENT = "#DC2626"      # 选中峰/拟合线强调
FIT = "#EA580C"         # 拟合曲线
BAND = FAINT            # 观测点/次要元素

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class _BaseCanvas(FigureCanvasQTAgg):
    def __init__(self, width: float = 6.4, height: float = 4.2, dpi: int = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="white")
        super().__init__(self.fig)
        self.fig.subplots_adjust(left=0.075, right=0.985, top=0.94, bottom=0.11)

    @staticmethod
    def _style(ax) -> None:
        ax.tick_params(colors=MUTED, labelsize=8.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.grid(True, color=GRID, lw=0.7, alpha=0.9)
        ax.set_axisbelow(True)


class PatternCanvas(_BaseCanvas):
    """上：全谱 + 峰位；下：选中峰的拟合放大图。"""

    def __init__(self, width: float = 6.6, height: float = 5.6, dpi: int = 100):
        super().__init__(width, height, dpi)
        gs = self.fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.34)
        self.ax_full = self.fig.add_subplot(gs[0])
        self.ax_zoom = self.fig.add_subplot(gs[1])
        for ax in (self.ax_full, self.ax_zoom):
            self._style(ax)
        self.fig.subplots_adjust(left=0.085, right=0.985, top=0.95, bottom=0.09)
        self._bundle: AnalysisBundle | None = None
        self._active: int = 0

    def set_bundle(self, bundle: AnalysisBundle | None, active: int = 0) -> None:
        self._bundle = bundle
        self._active = max(0, min(active, (len(bundle.fits) - 1) if bundle else 0))
        self._draw()

    def set_active(self, index: int) -> None:
        self._active = index
        self._draw()

    # ------------------------------------------------------------------
    def _draw(self) -> None:
        self.ax_full.clear()
        self.ax_zoom.clear()
        self._style(self.ax_full)
        self._style(self.ax_zoom)
        b = self._bundle
        if b is None:
            self.ax_full.text(0.5, 0.5, tr("cv.empty"), ha="center", va="center",
                              color=MUTED, transform=self.ax_full.transAxes)
            self.draw_idle()
            return

        x = b.sample.two_theta
        y = b.sample.intensity
        self.ax_full.plot(x, y, color=BAND, lw=0.7, zorder=1)
        self.ax_full.set_xlabel("2θ (°)", fontsize=9, color=MUTED)
        self.ax_full.set_ylabel(tr("cv.intensity"), fontsize=9, color=MUTED)
        self.ax_full.set_title(tr("cv.full_title"), fontsize=10, color=INK, loc="left")

        for i, fit in enumerate(b.fits):
            is_active = i == self._active
            self.ax_full.axvspan(fit.window[0], fit.window[1],
                                 color=BRAND if is_active else GRID,
                                 alpha=0.16 if is_active else 0.5, lw=0, zorder=0)
            self.ax_full.plot(fit.region_two_theta, fit.region_calculated,
                              color=FIT, lw=1.1, zorder=3)
            self.ax_full.axvline(fit.center, color=ACCENT if is_active else MUTED,
                                 lw=0.9 if is_active else 0.6, ls="--", alpha=0.9)
            size = None
            if b.scherrer.peaks and i < len(b.scherrer.peaks):
                size = b.scherrer.peaks[i].size_nm
            label = f"{fit.center:.2f}°"
            if size and np.isfinite(size):
                label += f"\n{size:.1f} nm"
            self.ax_full.annotate(label, xy=(fit.center, np.interp(fit.center, x, y)),
                                  xytext=(0, 8), textcoords="offset points",
                                  ha="center", fontsize=7.5,
                                  color=ACCENT if is_active else MUTED)
        self.ax_full.relim()
        self.ax_full.autoscale_view()
        y_lo, y_hi = self.ax_full.get_ylim()
        self.ax_full.set_ylim(y_lo, y_hi + 0.14 * (y_hi - y_lo))  # 顶部留白给峰标注

        if not b.fits:
            self.draw_idle()
            return

        fit = b.fits[min(self._active, len(b.fits) - 1)]
        peak = b.scherrer.peaks[self._active] if self._active < len(b.scherrer.peaks) else None
        xz, yz = fit.region_two_theta, fit.region_observed
        self.ax_zoom.plot(xz, yz, "o", ms=2.4, color=BAND, label=tr("cv.obs"), zorder=2)
        self.ax_zoom.plot(xz, fit.region_calculated, color=FIT, lw=1.5, label=tr("cv.fit"), zorder=4)
        if fit.profile.size:
            self.ax_zoom.plot(xz, fit.background, color=MUTED, lw=1.0, ls=":", label=tr("cv.bg"), zorder=3)
            self.ax_zoom.plot(xz, fit.background + fit.profile, color=FIT, lw=0.9, alpha=0.55,
                              ls="--", label=tr("cv.comp"), zorder=3)

        # FWHM 标注
        y_at = fit.bg0 + fit.height
        half = fit.bg0 + 0.5 * fit.height
        x1, x2 = fit.center - fit.fwhm / 2, fit.center + fit.fwhm / 2
        self.ax_zoom.annotate("", xy=(x2, half), xytext=(x1, half),
                              arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=1.1))
        self.ax_zoom.text(fit.center, half, f" FWHM {fit.fwhm:.3f}° ", color=ACCENT,
                          fontsize=8, ha="center", va="bottom",
                          bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
        self.ax_zoom.axhline(y_at, color=GRID, lw=0.8)
        self.ax_zoom.set_xlim(xz[0], xz[-1])
        zl, zh = self.ax_zoom.get_ylim()
        self.ax_zoom.set_ylim(zl, zh + 0.08 * (zh - zl))
        self.ax_zoom.set_xlabel("2θ (°)", fontsize=9, color=MUTED)
        self.ax_zoom.set_ylabel(tr("cv.intensity"), fontsize=9, color=MUTED)

        title = tr("cv.zoom_title", tt=fit.center, eta=fit.eta, rwp=fit.rwp)
        if peak is not None and peak.fwhm_inst and np.isfinite(peak.fwhm_inst):
            title += tr("cv.beta_corr", beta=peak.beta_deg)
        self.ax_zoom.set_title(title, fontsize=9.5, color=INK, loc="left")
        self.ax_zoom.legend(fontsize=7.5, loc="upper right", frameon=False, ncol=2)
        self.draw_idle()


class WHCanvas(_BaseCanvas):
    """Williamson-Hall 图：β·cosθ — 4sinθ。"""

    def __init__(self, width: float = 6.6, height: float = 4.6, dpi: int = 100):
        super().__init__(width, height, dpi)
        self.ax = self.fig.add_subplot(111)
        self._style(self.ax)
        self.fig.subplots_adjust(left=0.11, right=0.975, top=0.9, bottom=0.14)

    def set_bundle(self, bundle: AnalysisBundle | None) -> None:
        self.ax.clear()
        self._style(self.ax)
        if bundle is None:
            self.ax.text(0.5, 0.5, tr("cv.empty"), ha="center", va="center",
                         color=MUTED, transform=self.ax.transAxes)
            self.draw_idle()
            return

        # v2.0.0：当前方法是 W-H 变体时，改用该变体的坐标系与分组结果
        mid = bundle.config.method
        outcome = bundle.outcomes.get(mid)
        detail = getattr(outcome, "detail", None)
        variant = detail if isinstance(detail, WHVariantFit) else None

        if variant is not None and variant.points:
            self._draw_variant(variant, mid)
        else:
            self._draw_classic(bundle.wh)

        self.ax.set_ylabel(r"$\beta\cdot\cos\theta$  $(\times10^{-3}\ \mathrm{rad})$",
                           fontsize=9.5, color=MUTED)
        self.ax.set_xlim(left=0)
        self.ax.legend(fontsize=8, frameon=False, loc="best")
        self.draw_idle()

    # ------------------------------------------------------------------
    def _draw_classic(self, wh) -> None:
        """经典 W-H（UDM）图。"""
        good = [p for p in wh.points if p.ok]
        bad = [p for p in wh.points if not p.ok]
        if good:
            gx = np.array([p.x for p in good])
            gy = np.array([p.y for p in good]) * 1000.0
            self.ax.plot(gx, gy, "o", ms=7, color=BRAND, zorder=3, label=tr("cv.wh_points"))
            for p in good:
                self.ax.annotate(f"{p.two_theta:.1f}°", xy=(p.x, p.y * 1000),
                                 xytext=(5, 5), textcoords="offset points",
                                 fontsize=7.5, color=MUTED)
            if np.isfinite(wh.slope) and np.isfinite(wh.intercept):
                xs = np.linspace(min(gx.min() * 0.9, 0), max(gx.max() * 1.06, 0.1), 50)
                self.ax.plot(xs, (wh.slope * xs + wh.intercept) * 1000, color=ACCENT, lw=1.4,
                             label=tr("cv.wh_fit"), zorder=2)
                xi = wh.intercept * 1000
                self.ax.plot([0], [xi], "s", ms=6, color=ACCENT, zorder=4)
                self.ax.annotate(
                    tr("cv.wh_intercept", xi=xi) + r"$\times10^{-3}$"
                    + tr("cv.wh_to_size", d=wh.size_nm),
                    xy=(0, xi), xytext=(10, 16), textcoords="offset points",
                    fontsize=8.5, color=ACCENT,
                    bbox=dict(fc="white", ec=ACCENT, lw=0.6, alpha=0.92, pad=2.5))
        if bad:
            self.ax.text(0.985, 0.045,
                         tr("cv.excluded", peaks="、".join(f"{p.two_theta:.1f}°" for p in bad)),
                         transform=self.ax.transAxes, ha="right", va="bottom",
                         fontsize=7.8, color=BAND)
        self.ax.set_xlabel("4 sinθ", fontsize=9.5, color=MUTED)
        title = "Williamson-Hall 图"
        if np.isfinite(wh.r2):
            title += f"    ε = {wh.strain_pct:.3f}%    R² = {wh.r2:.3f}"
        self.ax.set_title(title, fontsize=10, color=INK, loc="left")

    def _draw_variant(self, variant: WHVariantFit, mid: str) -> None:
        """UDM/USDM/UDEDM 图；按晶向分组时逐组着色。"""
        model = mid.split("_", 1)[1] if "_" in mid else "udm"
        xlabel = {"udm": "4 sinθ",
                  "usdm": r"$4\sin\theta\,/\,E_{hkl}$  (GPa$^{-1}$)",
                  "udedm": r"$4\sin\theta\,\sqrt{2/E_{hkl}}$  (GPa$^{-1/2}$)"}.get(model, "4 sinθ")
        self.ax.set_xlabel(xlabel, fontsize=9.5, color=MUTED)

        palette = [BRAND, "#7C3AED", "#0891B2", "#B45309", "#15803D"]
        groups = variant.groups or [variant]
        for gi, g in enumerate(groups):
            color = palette[gi % len(palette)]
            pts = g.points if g.points else []
            good = [p for p in pts if p.ok and np.isfinite(p.y)]
            if not good:
                continue
            gx = np.array([p.x for p in good])
            gy = np.array([p.y for p in good]) * 1000.0
            tag = f"（{g.group_label}）" if g.group_label else ""
            self.ax.plot(gx, gy, "o", ms=7, color=color, zorder=3,
                         label=f"{tr('cv.wh_points')}{tag}")
            for p in good:
                self.ax.annotate(f"{p.two_theta:.1f}°", xy=(p.x, p.y * 1000),
                                 xytext=(5, 5), textcoords="offset points",
                                 fontsize=7.5, color=MUTED)
            if np.isfinite(g.slope) and np.isfinite(g.intercept):
                xs = np.linspace(min(gx.min() * 0.9, 0), max(gx.max() * 1.06, 0.1), 50)
                self.ax.plot(xs, (g.slope * xs + g.intercept) * 1000, color=color,
                             lw=1.3, alpha=0.85, zorder=2)

        title = f"Williamson-Hall（{model.upper()}）"
        if np.isfinite(variant.r2):
            title += f"    R² = {variant.r2:.3f}"
        if np.isfinite(variant.size_nm):
            title += f"    D = {variant.size_nm:.2f} nm"
        if len(groups) > 1:
            title += f"    {len(groups)} {tr('cv.wh_groups')}"
        self.ax.set_title(title, fontsize=10, color=INK, loc="left")


class StandardCanvas(_BaseCanvas):
    """标样线宽曲线：实测点 + 模型。"""

    def __init__(self, width: float = 5.4, height: float = 3.2, dpi: int = 100):
        super().__init__(width, height, dpi)

    def set_instrument(self, model) -> None:
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self._style(ax)
        self.fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.17)
        if model is None or not model.usable:
            ax.text(0.5, 0.5, tr("cv.std_empty"), ha="center", va="center", color=MUTED,
                    transform=ax.transAxes)
            self.draw_idle()
            return
        pts = [(p.position, p.fwhm) for p in model.peaks if p.ok]
        if pts:
            px, py = zip(*pts)
            ax.plot(px, py, "o", ms=6, color=BRAND, label=tr("cv.std_meas"))
        lo, hi = model.coverage()
        xs = np.linspace(max(lo - 3, 2), min(hi + 3, 160), 300)
        ax.plot(xs, [model.fwhm_at(v) for v in xs], color=ACCENT, lw=1.4,
                label=tr("cv.std_model", m=tr("cv.model_caglioti") if model.method == 'caglioti'
                        else tr("cv.model_pchip")))
        ax.set_xlabel("2θ (°)", fontsize=9, color=MUTED)
        ax.set_ylabel(tr("cv.y_instr"), fontsize=9, color=MUTED)
        ax.set_title(tr("cv.std_title"), fontsize=9.5, color=INK, loc="left")
        ax.legend(fontsize=7.5, frameon=False)
        self.draw_idle()
