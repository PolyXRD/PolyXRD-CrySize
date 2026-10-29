"""分析编排：从两条谱图到可出报告的结果对象。

这一层只做串联与边界处理，不做数学（数学在 profile/instrument/size 里），
保证「界面显示」「报告数值」「控制台调试」永远取自同一个对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from crysize.core.instrument import InstrumentModel, build_instrument_model
from crysize.core.pattern import KA2, Pattern
from crysize.core.peaks import PeakCandidate, auto_select, find_candidates
from crysize.core.profile import PeakFit, fit_region
from crysize.i18n import tr
from crysize.core.size import (K_FWHM, ScherrerResult, WHResult, compute_scherrer,
                               compute_wh)


@dataclass
class AnalysisConfig:
    """两个标签页共用的分析参数。"""

    n_peaks: int = 5                 # 参与计算的峰数
    window_max: float = 3.0          # 单峰拟合半窗宽上限（度），实际按 3.2×FWHM 自适应
    strip_ka2: bool = True           # 拟合时含 Kα2 卫星分量
    width_mode: str = "fwhm"         # fwhm | integral（谢乐法口径）
    K: float | None = None           # None → 按 width_mode 取默认值
    two_theta_range: tuple[float, float] | None = None
    min_prominence_frac: float = 0.03
    standard_positions: list[float] = field(default_factory=list)  # 空 → 自动找峰
    standard_window: float = 2.0
    zero_shift: float | None = None  # None → 自动由标样估计；数值则强制使用

    def effective_K(self) -> float:
        if self.K:
            return float(self.K)
        return K_FWHM if self.width_mode == "fwhm" else 1.0


@dataclass
class AnalysisBundle:
    sample: Pattern
    standard: Pattern | None
    fits: list[PeakFit]
    instrument: InstrumentModel | None
    scherrer: ScherrerResult
    wh: WHResult
    config: AnalysisConfig
    candidates: list[PeakCandidate] = field(default_factory=list)

    @property
    def corrected(self) -> bool:
        return self.instrument is not None and self.instrument.usable

    def warnings(self) -> list[str]:
        return list(dict.fromkeys(self.scherrer.warnings + self.wh.warnings))


def fit_window(fwhm_est: float, window_max: float) -> float:
    """拟合半窗宽：3.2 倍 FWHM（覆盖峰尾 1 个数量级衰减），受上限约束。"""
    return float(np.clip(3.2 * max(fwhm_est, 0.02), 0.8, max(window_max, 0.8)))


def fit_targets(
    pattern: Pattern,
    targets: list[float],
    candidates: list[PeakCandidate],
    config: AnalysisConfig,
    aux: list[PeakCandidate] | None = None,
) -> list[PeakFit]:
    """对每个目标峰做局部多峰拟合（窗口内邻峰一起拟，避免宽度污染）。

    ``aux`` 为低阈值辅助峰表：重叠区的肩峰单靠 prominence 检测不到，但它们
    的长尾会污染主峰，因此窗口内用辅助表补充邻峰（最多 3 个，取最强）。
    """
    pool = aux or candidates
    fwhm_map = {c.two_theta: c.fwhm_est for c in candidates}
    fwhm_map.update({c.two_theta: c.fwhm_est for c in pool})
    lam2 = KA2.get(pattern.anode)
    fits: list[PeakFit] = []
    for tgt in sorted(targets):
        est = fwhm_map.get(tgt, 0.2)
        win = fit_window(est, config.window_max)
        near = [c for c in pool if abs(c.two_theta - tgt) <= win and abs(c.two_theta - tgt) > 1e-6]
        near.sort(key=lambda c: c.prominence, reverse=True)
        inside = sorted([tgt] + [c.two_theta for c in near[:3]])
        m = pattern.mask(tgt - win, tgt + win)
        if m.sum() < 12:
            continue
        fits.append(fit_region(
            pattern.two_theta[m], pattern.intensity[m], inside, window=win,
            wavelength=pattern.wavelength,
            wavelength2=lam2 if config.strip_ka2 else None,
            anode=pattern.anode, strip_ka2=config.strip_ka2,
            target=tgt, fwhm_guess=fwhm_map,
        ))
    return fits


def _apply_angle_correction(pattern: Pattern, corr) -> Pattern:
    """把样品谱的 2θ 平移到校正后的角度坐标系。"""
    if corr is None or not getattr(corr, "applied", False):
        return pattern
    new_tt = corr.apply(pattern.two_theta)
    if np.allclose(new_tt, pattern.two_theta, atol=1e-9):
        return pattern
    return Pattern(
        two_theta=new_tt, intensity=pattern.intensity,
        label=pattern.label, path=pattern.path, anode=pattern.anode,
        wavelength=pattern.wavelength, step=pattern.step,
        meta={**pattern.meta, "angle_correction": corr.describe()},
    )


def run_analysis(
    sample: Pattern,
    standard: Pattern | None = None,
    config: AnalysisConfig | None = None,
) -> AnalysisBundle:
    cfg = config or AnalysisConfig()

    # 先建仪器模型（顺便估零位偏移），样品谱再平移到校正后的角度坐标系，
    # 保证标样宽度曲线与样品峰位处在同一个 2θ 坐标里。
    instrument = None
    if standard is not None:
        instrument = build_instrument_model(
            standard,
            cfg.standard_positions or None,
            window=cfg.standard_window,
            strip_ka2=cfg.strip_ka2,
            zero_shift=cfg.zero_shift,
        )
    shift_corr = instrument.correction if instrument else None
    sample_used = _apply_angle_correction(sample, shift_corr)

    candidates = find_candidates(
        sample_used,
        min_prominence_frac=cfg.min_prominence_frac,
        two_theta_range=cfg.two_theta_range,
    )
    if not candidates:
        raise ValueError(tr("ana.no_peaks"))

    selected = auto_select(candidates, cfg.n_peaks,
                           min_angle=cfg.two_theta_range[0] if cfg.two_theta_range else None,
                           max_angle=cfg.two_theta_range[1] if cfg.two_theta_range else None)
    aux = find_candidates(sample_used, min_prominence_frac=0.008,
                          two_theta_range=cfg.two_theta_range)
    fits = fit_targets(sample_used, [c.two_theta for c in selected], candidates, cfg, aux=aux)
    if not fits:
        raise ValueError(tr("ana.window"))

    scherrer = compute_scherrer(
        fits, wavelength=sample.wavelength, instrument=instrument,
        width_mode=cfg.width_mode, K=cfg.effective_K(),
    )
    wh = compute_wh(fits, wavelength=sample.wavelength, instrument=instrument)

    return AnalysisBundle(
        sample=sample_used, standard=standard, fits=fits, instrument=instrument,
        scherrer=scherrer, wh=wh, config=cfg, candidates=candidates,
    )


def refit_with_positions(
    bundle: AnalysisBundle, positions: list[float], config: AnalysisConfig | None = None
) -> AnalysisBundle:
    """用户手动增删峰后重算（复用已建好的仪器模型）。"""
    cfg = replace(config or bundle.config)
    fits = fit_targets(bundle.sample, positions, bundle.candidates, cfg)
    scherrer = compute_scherrer(fits, wavelength=bundle.sample.wavelength,
                                instrument=bundle.instrument,
                                width_mode=cfg.width_mode, K=cfg.effective_K())
    wh = compute_wh(fits, wavelength=bundle.sample.wavelength, instrument=bundle.instrument)
    return AnalysisBundle(sample=bundle.sample, standard=bundle.standard, fits=fits,
                          instrument=bundle.instrument, scherrer=scherrer, wh=wh,
                          config=cfg, candidates=bundle.candidates)
