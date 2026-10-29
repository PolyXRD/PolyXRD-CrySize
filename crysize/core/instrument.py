"""仪器宽化模型（标样线宽系数）与零位偏移。

两种建模方式，对应文献中的两类做法：

1. **Caglioti 多项式**（Caglioti, Paoletti & Ricci, Nucl. Instr. 3 (1958) 223）::

       FWHM² = U·tan²θ + V·tanθ + W        （FWHM 与 U,V,W 同单位，此处为度²）

   Rietveld/whole-pattern 的标准仪器分辨函数形式，可平滑外推到标样峰覆盖
   范围之外；缺点是参数强相关，峰少时外推易发散。

2. **实测点 PCHIP 插值**：用标样在相近 2θ 处的实测宽度扣除，不引入模型假设
   （"instrumental standard method" 的原始做法）；无平滑、不能外推。

默认先试 Caglioti，并在拟合质量差（R² < 0.8）或出现非物理（负值/剧烈外推）
时自动退回插值，同时在结果里记录实际使用的方法 —— 报告要如实反映。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import PchipInterpolator

from crysize.core.pattern import KA2, Pattern
from crysize.core.peaks import PeakCandidate, find_candidates
from crysize.core.profile import integral_width
from crysize.core.standards import AngleCorrection, estimate_angle_correction
from crysize.i18n import tr

DEG2RAD = np.pi / 180.0


@dataclass
class StandardPeak:
    """标样单峰拟合记录（位置已做零位校正）。"""

    position: float          # 校正后峰位（2θ，度）
    position_raw: float      # 实测峰位
    fwhm: float              # 观测 FWHM（度）
    eta: float
    beta_int: float          # 观测积分宽度（度）
    height: float
    rwp: float
    ok: bool


@dataclass
class InstrumentModel:
    """仪器分辨函数。宽度单位为**度**，对外换算由调用方负责。"""

    method: str = "caglioti"                  # caglioti | interp | none
    U: float = 0.0
    V: float = 0.0
    W: float = 0.0
    r2: float = 0.0
    rms: float = 0.0
    peaks: list[StandardPeak] = field(default_factory=list)
    eta_median: float = 0.5
    note: str = ""
    correction: AngleCorrection = field(default_factory=AngleCorrection)
    _fwhm_curve: PchipInterpolator | None = None
    _eta_curve: PchipInterpolator | None = None
    _lo: float = 0.0
    _hi: float = 180.0

    @property
    def zero_shift(self) -> float:
        """2θ→0 的等效偏移量（报告标注用）。"""
        return self.correction.shift_at_zero

    @property
    def shift_note(self) -> str:
        return self.correction.note

    @property
    def standard_name(self) -> str:
        return self.correction.standard.name if self.correction.standard else ""

    # -- 查询 -------------------------------------------------------------
    @property
    def usable(self) -> bool:
        return self.method != "none" and len([p for p in self.peaks if p.ok]) >= 1

    def fwhm_at(self, two_theta: float) -> float:
        """仪器 FWHM（度）在给定 2θ 处（已校正角度坐标系）的值。"""
        tt = float(np.clip(two_theta, self._lo, self._hi))
        if self.method == "caglioti":
            th = np.radians(tt / 2.0)
            val = self.U * np.tan(th) ** 2 + self.V * np.tan(th) + self.W
            return float(np.sqrt(max(val, 0.0)))
        if self._fwhm_curve is not None:
            in_range = self._lo <= two_theta <= self._hi
            v = float(self._fwhm_curve(tt))
            if not in_range:
                v *= self._extrap_penalty(two_theta)
            return max(v, 1e-6)
        return float("nan")

    def _extrap_penalty(self, two_theta: float) -> float:
        """超出标样覆盖范围时按 Caglioti 趋势放大，避免低估仪器宽化。"""
        th = np.radians(min(max(two_theta, 1.0), 179.0) / 2.0)
        val = self.U * np.tan(th) ** 2 + self.V * np.tan(th) + self.W
        f_cag = float(np.sqrt(max(val, 0.0))) if val > 0 else 0.0
        edge = self._hi if two_theta > self._hi else self._lo
        f_edge = float(self._fwhm_curve(edge)) if self._fwhm_curve else 0.0
        if f_edge > 1e-9 and f_cag > 0:
            return float(np.clip(f_cag / f_edge, 1.0, 2.0))
        return 1.0

    def eta_at(self, two_theta: float) -> float:
        tt = float(np.clip(two_theta, self._lo, self._hi))
        if self._eta_curve is not None:
            return float(np.clip(self._eta_curve(tt), 0.0, 1.0))
        return self.eta_median

    def beta_int_at(self, two_theta: float) -> float:
        """仪器积分宽度（度）。"""
        return integral_width(self.fwhm_at(two_theta), self.eta_at(two_theta))

    def coefficients_rad(self) -> tuple[float, float, float]:
        """U,V,W 换算为弧度² 形式（文献/软件通用报法）。"""
        k = DEG2RAD**2
        return self.U * k, self.V * k, self.W * k

    def table(self) -> list[tuple[float, float, float, float]]:
        """标样峰实测表：(2θ, FWHM_obs, FWHM_model, 残差)。"""
        rows = []
        for p in self.peaks:
            if not p.ok:
                continue
            fm = self.fwhm_at(p.position)
            rows.append((p.position, p.fwhm, fm, p.fwhm - fm))
        return rows

    def coverage(self) -> tuple[float, float]:
        return self._lo, self._hi


def _caglioti_design(two_theta: np.ndarray) -> np.ndarray:
    th = np.radians(np.asarray(two_theta, dtype=float) / 2.0)
    t = np.tan(th)
    return np.column_stack([t**2, t, np.ones_like(t)])


def _fit_standard_peaks(
    standard: Pattern,
    positions: list[float],
    candidates: list[PeakCandidate],
    window: float,
    strip_ka2: bool,
) -> list:
    from crysize.core.profile import fit_region

    fwhm_map = {c.two_theta: c.fwhm_est for c in candidates}
    lam2 = KA2.get(standard.anode)
    out = []
    for pos in sorted(positions):
        est = fwhm_map.get(pos, 0.15)
        win = float(np.clip(max(3.2 * est, 0.5), 0.4, max(window, 0.5)))
        inside = sorted(c.two_theta for c in candidates if abs(c.two_theta - pos) <= win)
        if not any(abs(pos - p) < 1e-6 for p in inside):
            inside = sorted(inside + [pos])
        m = standard.mask(pos - win, pos + win)
        if m.sum() < 12:
            continue
        fit = fit_region(
            standard.two_theta[m], standard.intensity[m], inside, window=win,
            wavelength=standard.wavelength,
            wavelength2=lam2 if strip_ka2 else None,
            anode=standard.anode, strip_ka2=strip_ka2,
            target=pos, fwhm_guess=fwhm_map,
        )
        ok = (fit.success and np.isfinite(fit.fwhm) and 0 < fit.fwhm < 5.0
              and fit.rwp < 25.0)
        out.append((fit, bool(ok)))
    return out


def build_instrument_model(
    standard: Pattern,
    positions: list[float] | None = None,
    *,
    window: float = 2.0,
    strip_ka2: bool = True,
    min_peaks_caglioti: int = 5,
    zero_shift: float | AngleCorrection | None = None,
) -> InstrumentModel:
    """由标样谱构建仪器分辨函数（含 2θ 角度校正）。

    ``positions`` 为空时自动在标样谱上找峰（取突出度前 12 个）。
    ``zero_shift`` 为 None 时自动估计；给 float 则只校正常数零偏；
    给 AngleCorrection 则直接使用。
    """
    cands = find_candidates(standard, min_prominence_frac=0.01, min_sep_deg=0.5)
    if not positions:
        positions = [c.two_theta for c in cands[:12]]

    fitted = _fit_standard_peaks(standard, positions, cands, window, strip_ka2)
    if not fitted:
        return InstrumentModel(method="none", note=tr("inst.no_peaks"))

    # -- 角度校正 --------------------------------------------------------
    obs_positions = [f.center for f, ok in fitted if ok]
    if isinstance(zero_shift, AngleCorrection):
        corr = zero_shift
    elif zero_shift is None:
        corr = estimate_angle_correction(obs_positions, standard.wavelength)
    else:
        corr = AngleCorrection(delta0=float(zero_shift), k=0.0, applied=True,
                               method="zero", note=tr("inst.zero_fixed", v=zero_shift))

    peaks: list[StandardPeak] = []
    for fit, ok in fitted:
        peaks.append(StandardPeak(
            position=float(fit.center + corr.at(fit.center)), position_raw=fit.center,
            fwhm=fit.fwhm, eta=fit.eta, beta_int=fit.beta_int,
            height=fit.height, rwp=fit.rwp, ok=ok,
        ))

    good = [p for p in peaks if p.ok]
    if not good:
        return InstrumentModel(method="none", peaks=peaks, correction=corr,
                               note=tr("inst.no_quality"))

    tt = np.array([p.position for p in good])
    fw = np.array([p.fwhm for p in good])
    eta = np.array([p.eta for p in good])
    order = np.argsort(tt)
    tt, fw, eta = tt[order], fw[order], eta[order]

    model = InstrumentModel(peaks=peaks, eta_median=float(np.median(eta)),
                            _lo=float(tt.min()), _hi=float(tt.max()),
                            correction=corr)

    # -- Caglioti 优先 ---------------------------------------------------
    if tt.size >= min_peaks_caglioti and float(np.ptp(tt)) > 5.0:
        try:
            A = _caglioti_design(tt)
            coef, *_ = np.linalg.lstsq(A, fw**2, rcond=None)
            U, V, W = (float(c) for c in coef)
            pred = np.sqrt(np.maximum(A @ coef, 1e-9))
            ss_res = float(np.sum((fw - pred) ** 2))
            ss_tot = float(np.sum((fw - fw.mean()) ** 2))
            r2 = 1.0 - ss_res / max(ss_tot, 1e-15)
            physical = (W > 0) and np.all(pred > 0) and np.all(pred < fw.max() * 2.0)
            if r2 >= 0.8 and physical:
                model.method = "caglioti"
                model.U, model.V, model.W = U, V, W
                model.r2, model.rms = r2, float(np.sqrt(np.mean((fw - pred) ** 2)))
                model.note = tr("inst.caglioti_ok", n=tt.size)
                model._eta_curve = _safe_pchip(tt, eta)
                return model
            model.note = tr("inst.caglioti_fallback", r2=r2,
                            phy=tr("inst.phy_ok" if physical else "inst.phy_fail"))
        except Exception as exc:  # pragma: no cover
            model.note = tr("inst.caglioti_error", exc=exc)
    else:
        model.note = tr("inst.few_peaks", n=tt.size, m=min_peaks_caglioti)

    # -- 插值兜底 ---------------------------------------------------------
    model.method = "interp"
    model._fwhm_curve = _safe_pchip(tt, fw)
    model._eta_curve = _safe_pchip(tt, eta)
    # 同时记录一条"仅供参考"的 Caglioti 系数（参与展示，不参与计算）
    try:
        A = _caglioti_design(tt)
        coef, *_ = np.linalg.lstsq(A, fw**2, rcond=None)
        model.U, model.V, model.W = (float(c) for c in coef)
        pred = np.sqrt(np.maximum(A @ coef, 1e-9))
        ss_res = float(np.sum((fw - pred) ** 2))
        ss_tot = float(np.sum((fw - fw.mean()) ** 2))
        model.r2 = 1.0 - ss_res / max(ss_tot, 1e-15)
        model.rms = float(np.sqrt(np.mean((fw - pred) ** 2)))
    except Exception:
        pass
    return model


def _safe_pchip(x: np.ndarray, y: np.ndarray) -> PchipInterpolator | None:
    """去重后建 PCHIP；点数不足 2 返回 None。"""
    if x.size < 2:
        return None
    xu, idx = np.unique(x, return_index=True)
    yu = y[idx]
    if xu.size < 2:
        return None
    return PchipInterpolator(xu, yu, extrapolate=True)
