"""Warren-Averbach 分析：单峰 Voigt 近似与多级反射傅里叶法。

Warren-Averbach（Warren & Averbach, *J. Appl. Phys.* 21 (1950) 595；
Warren, *X-ray Diffraction*, Addison-Wesley (1969)）不做"总宽化 = 尺寸 +
应变"的线性叠加，而是在**傅里叶空间**把衍射峰的 Fourier 系数分解为尺寸项
与应变项::

    A(L) = A^S(L) · A^D(L)
    A^D(L) = exp(−2π² L² ⟨ε_L²⟩ / d²)

其中 L 是傅里叶长度（Å，沿衍射方向的实际距离），d 是面间距。对固定的 L，
把所有可用反射的 ln A(L) 对 1/d² 作线性回归：截距给出 ln A^S(L)（尺寸项），
斜率给出 −2π² L² ⟨ε_L²⟩（应变项）。尺寸项在小 L 处满足
A^S(L) ≈ 1 − L/D_v，故 D_v = −1/(dA^S/dL)│_{L→0}，为**体积加权**晶粒尺寸。

两种落地方式
------------
**单峰近似（wa_single）** —— 只需孤立单峰，用 Voigt 分解代替傅里叶：
伪 Voigt 的 Lorentzian 分量归尺寸宽化、Gaussian 分量归应变宽化（Warren
的尺寸宽化呈 Cauchy 型、应变宽化呈 Gauss 型的经典假设）::

    β_L = η · (π/2) · FWHM          →  D = Kλ / (β_L cosθ)
    β_G = (1−η) · √(π/4ln2) · FWHM  →  ε = β_G / (4 tanθ)

依据：de Keijser, Langford, Mittemeijer & Vogels, *J. Appl. Cryst.* 15
(1982) 308；Langford, Delhez, de Keijser & Mittemeijer, *Aust. J. Phys.*
41 (1988) 173。优点：不要求测到多级反射；缺点：尺寸/应变的分配依赖
线型假设，与真实线型偏离时偏差可达 20% 以上。

**多级反射傅里叶法（wa_fourier）** —— 真 Warren-Averbach。要求：
① 至少 3 个有效峰，且 d 值至少有 2 个不同（否则 1/d² 无法回归）；
② 峰两侧有足够干净的窗口（≥ 6×FWHM）；
③ 仪器宽化已由标样给出（Stokes 解卷积要除仪器 Fourier 系数）。

峰形用拟合得到的伪 Voigt 参数解析重建（已剥离 Kα₂、已扣背景），因此不
依赖原始数据的步长均匀性；再在 s = 2sinθ/λ 空间等间隔重采样后做 FFT。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from crysize.core.instrument import InstrumentModel
from crysize.core.profile import PeakFit, pseudo_voigt
from crysize.core.size import DEG2RAD, K_INTEGRAL, _corrected_width, _DOUBTFUL_CODES
from crysize.i18n import tr

#: Gaussian / Lorentzian 的积分宽度 — FWHM 换算系数
_GAUSS_FACTOR = float(np.sqrt(np.pi / (4.0 * np.log(2.0))))   # 1.0645
_LORENTZ_FACTOR = float(np.pi / 2.0)                          # 1.5708


@dataclass
class WAPeak:
    """单个峰在 Warren-Averbach 下的结果。"""

    two_theta: float
    d: float
    beta_g: float = float("nan")      # Gaussian 积分宽度（rad）
    beta_l: float = float("nan")      # Lorentzian 积分宽度（rad）
    size_nm: float = float("nan")
    strain: float = float("nan")
    ok: bool = True
    note: str = ""


@dataclass
class WAResult:
    mode: str = "single"              # single | fourier
    size_nm: float = float("nan")     # 主结果：single→算术平均，fourier→体积加权 D_v
    size_mean_nm: float = float("nan")
    strain_rms: float = float("nan")  # ⟨ε²⟩^½
    strain_pct: float = float("nan")
    peaks: list[WAPeak] = field(default_factory=list)
    L: np.ndarray = field(default_factory=lambda: np.empty(0))
    As: np.ndarray = field(default_factory=lambda: np.empty(0))   # A^S(L)
    eps2: np.ndarray = field(default_factory=lambda: np.empty(0)) # ⟨ε_L²⟩
    r2: float = float("nan")
    warnings: list[str] = field(default_factory=list)

    @property
    def n_valid(self) -> int:
        return len([p for p in self.peaks if p.ok and np.isfinite(p.size_nm)])


# ----------------------------------------------------------------------
# 单峰 Voigt 近似
# ----------------------------------------------------------------------
def compute_wa_single(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    K: float = K_INTEGRAL,
) -> WAResult:
    """逐峰 Voigt 单线法：Lorentzian→尺寸，Gaussian→应变。"""
    res = WAResult(mode="single")
    for fit in fits:
        beta, _fw, flag = _corrected_width(fit, instrument, "integral")
        codes = list(fit.quality_codes())
        unreliable = bool(_DOUBTFUL_CODES & set(codes))
        theta = np.radians(fit.center / 2.0)
        d = wavelength / (2.0 * np.sin(theta))
        p = WAPeak(two_theta=fit.center, d=d)
        if not fit.success or not np.isfinite(beta) or beta <= 0 or unreliable:
            p.ok = False
            p.note = tr("wa.excluded")
            res.peaks.append(p)
            continue
        if flag == "no_standard":
            p.note = tr("wa.no_standard")
        # 用仪器校正后的积分宽度反推等效物理 FWHM，再按 η 拆分
        eta = float(np.clip(fit.eta, 0.0, 1.0))
        fw_phys = float(beta / (eta * _LORENTZ_FACTOR + (1.0 - eta) * _GAUSS_FACTOR))
        p.beta_l = eta * _LORENTZ_FACTOR * fw_phys * DEG2RAD
        p.beta_g = (1.0 - eta) * _GAUSS_FACTOR * fw_phys * DEG2RAD
        if p.beta_l > 1e-12 and np.cos(theta) > 1e-6:
            p.size_nm = float(K * wavelength / (p.beta_l * np.cos(theta)) / 10.0)
        if np.tan(theta) > 1e-6:
            p.strain = float(p.beta_g / (4.0 * np.tan(theta)))
        res.peaks.append(p)

    sizes = [p.size_nm for p in res.peaks if p.ok and np.isfinite(p.size_nm)]
    if sizes:
        res.size_nm = float(np.mean(sizes))
        res.size_mean_nm = res.size_nm
    strains = [p.strain for p in res.peaks if p.ok and np.isfinite(p.strain)]
    if strains:
        res.strain_rms = float(np.sqrt(np.mean(np.square(strains))))
        res.strain_pct = res.strain_rms * 100.0
    if not sizes:
        res.warnings.append(tr("wa.no_valid"))
    if instrument is None or not instrument.usable:
        res.warnings.append(tr("wa.need_standard"))
    res.warnings.append(tr("wa.single_note"))
    return res


# ----------------------------------------------------------------------
# 多级反射傅里叶法
# ----------------------------------------------------------------------
def _rebuild_profile(fit: PeakFit, n: int = 512) -> tuple[np.ndarray, np.ndarray, float]:
    """用拟合参数在等 2θ 网格上重建纯 Kα₁ 单峰（去背景、无 Kα₂）。

    返回 (2θ 网格, 强度, 2θ 步长)。
    """
    half = max(4.0 * fit.fwhm, 0.4)
    lo, hi = fit.center - half, fit.center + half
    x = np.linspace(lo, hi, n)
    y = pseudo_voigt(x, fit.center, fit.fwhm, fit.eta) * fit.height
    return x, y, float(x[1] - x[0])


def _fourier_coeffs(x: np.ndarray, y: np.ndarray, wavelength: float
                    ) -> tuple[np.ndarray, np.ndarray]:
    """在 s = 2sinθ/λ 空间等间隔重采样后做 FFT。

    返回 (L 数组 Å, A(L))，A 已按 n=0 项归一化。
    """
    s = 2.0 * np.sin(np.radians(x / 2.0)) / wavelength
    si = np.linspace(s[0], s[-1], s.size)
    yi = np.interp(si, s, y)
    yi = yi - yi.min()                       # 去残余基线
    n = yi.size
    ds = float(si[1] - si[0])
    if ds <= 0 or n < 16:
        return np.empty(0), np.empty(0)
    f = np.abs(np.fft.rfft(yi))
    a = f / max(f[0], 1e-30)
    idx = np.arange(a.size)
    L = idx / (n * ds)                       # 傅里叶长度 Å
    return L, a


def _inst_profile(fwhm_inst: float, eta: float, x: np.ndarray) -> np.ndarray:
    return pseudo_voigt(x, float(np.mean(x)), fwhm_inst, eta)


def compute_wa_fourier(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    n_grid: int = 512,
) -> WAResult:
    """完整 Warren-Averbach：需要多级反射（多个不同 d）与标样线宽。"""
    res = WAResult(mode="fourier")
    eta_inst = 0.5
    if instrument is not None and getattr(instrument, "peaks", None):
        etas = [p.eta for p in instrument.peaks if p.ok and np.isfinite(p.eta)]
        if etas:
            eta_inst = float(np.mean(etas))

    series: list[tuple[np.ndarray, np.ndarray, float, float]] = []  # (L, A, d, 2θ)
    peaks: list[WAPeak] = []
    for fit in fits:
        codes = list(fit.quality_codes())
        unreliable = bool(_DOUBTFUL_CODES & set(codes))
        theta = np.radians(fit.center / 2.0)
        d = wavelength / (2.0 * np.sin(theta))
        p = WAPeak(two_theta=fit.center, d=d)
        if not fit.success or unreliable or not np.isfinite(fit.fwhm) or fit.fwhm <= 0:
            p.ok = False
            p.note = tr("wa.excluded")
            peaks.append(p)
            continue
        x, y, _dx = _rebuild_profile(fit, n_grid)
        L, a = _fourier_coeffs(x, y, wavelength)
        if L.size < 8:
            p.ok = False
            p.note = tr("wa.excluded")
            peaks.append(p)
            continue
        if instrument is not None and instrument.usable:
            fw = instrument.fwhm_at(fit.center)
            if np.isfinite(fw) and fw > 1e-6:
                _, ai = _fourier_coeffs(x, _inst_profile(fw, eta_inst, x), wavelength)
                if ai.size == a.size:
                    a = a / np.clip(ai, 1e-6, None)
        a = np.clip(a, 1e-9, 1.0)
        series.append((L, a, d, fit.center))
        peaks.append(p)
    res.peaks = peaks

    if len(series) < 3:
        res.warnings.append(tr("wa.fourier_need_peaks", n=len(series)))
        return res
    d_vals = {round(s[2], 5) for s in series}
    if len(d_vals) < 2:
        res.warnings.append(tr("wa.fourier_need_orders"))
        return res
    if instrument is None or not instrument.usable:
        res.warnings.append(tr("wa.fourier_need_std"))

    # 公共 L 网格：取所有峰 L 范围的交集，避开 A→0 的噪声区
    l_max = min(s[0][-1] for s in series)
    l_min = max(s[0][1] for s in series)
    if not np.isfinite(l_max) or l_max <= l_min:
        res.warnings.append(tr("wa.fourier_window"))
        return res
    Lg = np.linspace(l_min, min(l_max, 200.0), 60)

    inv_d2 = np.array([1.0 / (s[2] ** 2) for s in series])
    used_L: list[float] = []
    As, eps2, r2s = [], [], []
    for L in Lg:
        xs: list[float] = []
        ys: list[float] = []
        # 逐峰配对收集：跳过某个峰时，它的 1/d² 也必须一起跳，否则横纵轴错配
        for (Li, ai, _d, _tt), inv in zip(series, inv_d2):
            v = float(np.interp(L, Li, np.log(np.clip(ai, 1e-9, 1.0))))
            if v > 0:                      # A > 1（解卷积过冲）不参与对数回归
                continue
            xs.append(float(inv))
            ys.append(v)
        if len(xs) < 2 or np.ptp(np.asarray(xs)) < 1e-12:
            continue
        m, b = np.polyfit(np.asarray(xs), np.asarray(ys), 1)
        used_L.append(float(L))
        As.append(float(np.exp(b)))
        eps2.append(float(-m / (2.0 * np.pi**2 * L * L)))
        yv = np.asarray(ys)
        pred = m * np.asarray(xs) + b
        ss_res = float(np.sum((yv - pred) ** 2))
        ss_tot = float(np.sum((yv - yv.mean()) ** 2))
        r2s.append(1.0 - ss_res / max(ss_tot, 1e-18))

    if len(As) < 3:
        res.warnings.append(tr("wa.fourier_no_fit"))
        return res

    res.L = np.asarray(used_L)
    res.As = np.clip(np.asarray(As), 1e-6, 1.0)
    res.eps2 = np.clip(np.asarray(eps2), 0.0, None)
    res.r2 = float(np.mean(r2s)) if r2s else float("nan")

    # 尺寸：柱模型给出 ln A^S(L) = −L/D_v，故对 ln A^S 作线性回归取斜率，
    # 而不是直接对 A^S 拟合 —— A^S 在 L 接近 D 时明显下弯，直接拟合会高估 D。
    sel = res.As > 0.35
    if sel.sum() >= 3:
        slope, _icpt = np.polyfit(res.L[sel], np.log(res.As[sel]), 1)
        if slope < -1e-9:
            res.size_nm = float(-1.0 / slope / 10.0)      # Å → nm
    if not np.isfinite(res.size_nm):
        res.warnings.append(tr("wa.fourier_no_size"))
    elif res.size_nm > 500.0 or res.size_nm < 0.5:
        res.warnings.append(tr("wa.fourier_out_of_range", d=res.size_nm))

    # 应变：取 L = D_v/2 处的 ⟨ε²⟩^½（惯例取值点）
    if np.isfinite(res.size_nm):
        Lpick = res.size_nm / 2.0
        idx = int(np.argmin(np.abs(res.L - Lpick)))
        res.strain_rms = float(np.sqrt(res.eps2[idx]))
    else:
        res.strain_rms = float(np.sqrt(np.mean(res.eps2)))
    res.strain_pct = res.strain_rms * 100.0 if np.isfinite(res.strain_rms) else float("nan")
    return res
