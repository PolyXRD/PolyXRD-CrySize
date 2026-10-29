"""峰形函数与局部多峰拟合。

模型
----
pseudo-Voigt（Thompson-Cox-Hastings 的两参数简化形式）::

    pV(x) = h·[ η·L(x) + (1-η)·G(x) ] + b0 + b1·(x - x_ref)

    G(x) = exp(-4ln2·(x-x0)²/F²)          （高斯，F 为 FWHM）
    L(x) = 1 / (1 + 4·(x-x0)²/F²)         （洛伦兹，F 为 FWHM）

选 pV 而非纯高斯/纯洛伦兹：纳米晶样品的峰同时含尺寸宽化（近洛伦兹）与
仪器/应变宽化（近高斯），η 恰好把两者比例作为可拟合参数；η 同时决定
FWHM 与积分宽度的换算系数。若强制用纯洛伦兹（η=1）或纯高斯（η=0），
宽度与积分宽度都会系统偏差 5–50%。

为什么要"局部多峰"
------------------
纳米晶峰宽可达 1–2°，而相邻反射间距可能只有 2–3°。单峰窗口一旦为了
容纳峰宽而放宽，就必然把邻峰尾部卷进来，拟合出的 FWHM 是"主峰+邻峰"
的混合宽度（实测中可导致 W-H 图完全散乱）。因此拟合窗口内**所有候选峰
一起参与拟合**：目标峰与邻峰各有独立 (中心, FWHM, η, 高度)，共享一条
线性背景。这样窗口可以开到 3–4 倍 FWHM 而不被污染。

Kα2 处理
--------
Cu 靶未单色化时 Kα2 在主峰右侧形成卫星峰（Δ2θ 随 θ 增大），直接拟单峰
会把双线宽度误当作物相宽化，高角峰偏差可达 20% 以上。``strip_ka2=True``
时每个峰按同一 FWHM/η 加一个位置由 Bragg 方程约束、强度比固定的卫星
分量，等价于在拟合层面完成 Rachinger 剥离（Rachinger, J. Sci. Instrum.
25 (1948) 254）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares

from crysize.i18n import tr

#: 高斯函数的积分宽度 / FWHM = √π / (2√ln2)
GAUSS_INT_RATIO = float(np.sqrt(np.pi) / (2.0 * np.sqrt(np.log(2.0))))  # 1.06447
#: 洛伦兹函数的积分宽度 / FWHM = π/2
LORENTZ_INT_RATIO = float(np.pi / 2.0)  # 1.57080

#: Kα2/Kα1 强度比（Cu 靶 0.497，IUCr 表值；其他靶材约 0.5）
KA2_RATIO = {"Cu": 0.497, "Co": 0.5, "Cr": 0.5, "Fe": 0.5, "Mo": 0.5, "Ag": 0.5}


def pseudo_voigt(x: np.ndarray, center: float, fwhm: float, eta: float) -> np.ndarray:
    """单位高度的 pseudo-Voigt 剖面。"""
    dx2 = (np.asarray(x, dtype=float) - center) ** 2
    g = np.exp(-4.0 * np.log(2.0) * dx2 / fwhm**2)
    l = 1.0 / (1.0 + 4.0 * dx2 / fwhm**2)
    return eta * l + (1.0 - eta) * g


def integral_width(fwhm: float, eta: float) -> float:
    """pseudo-Voigt 的积分宽度 β_int（与 FWHM 同单位）。"""
    return fwhm * (eta * LORENTZ_INT_RATIO + (1.0 - eta) * GAUSS_INT_RATIO)


def fwhm_from_integral(beta: float, eta: float) -> float:
    """由积分宽度反算 FWHM。"""
    k = eta * LORENTZ_INT_RATIO + (1.0 - eta) * GAUSS_INT_RATIO
    return beta / k


def ka2_position(two_theta1: float, lam1: float, lam2: float) -> float:
    """由 Kα1 峰位换算同 d 值的 Kα2 峰位。"""
    th1 = np.radians(two_theta1 / 2.0)
    s = lam2 / lam1 * np.sin(th1)
    if s >= 1.0:
        return two_theta1
    return float(np.degrees(2.0 * np.arcsin(s)))


@dataclass
class PeakFit:
    """单峰拟合结果（宽度为 FWHM，单位度；β_int 为积分宽度）。"""

    center: float
    fwhm: float
    eta: float
    height: float
    area: float
    beta_int: float
    bg0: float
    bg1: float
    fwhm_err: float = 0.0
    center_err: float = 0.0
    rwp: float = 0.0
    success: bool = True
    message: str = ""
    window: tuple[float, float] = (0.0, 0.0)
    ka2_used: bool = False
    neighbors: int = 0              # 同窗口内一起拟合的其它峰数
    region_two_theta: np.ndarray = field(default_factory=lambda: np.empty(0))
    region_observed: np.ndarray = field(default_factory=lambda: np.empty(0))
    region_calculated: np.ndarray = field(default_factory=lambda: np.empty(0))
    profile: np.ndarray = field(default_factory=lambda: np.empty(0))

    @property
    def background(self) -> np.ndarray:
        return self.region_calculated - self.profile if self.profile.size else np.empty(0)

    def quality_codes(self) -> list[str]:
        """稳定的结构化质量码（语言无关，供程序门控用）。

        门控（是否参与平均与 W-H 回归）绝不能用译文做子串匹配 —— 换语言就崩。
        文案层（quality_flags）与逻辑层（quality_codes）严格分离。
        """
        codes: list[str] = []
        if not self.success:
            codes.append("not_converged")
        if self.success and self.eta >= 0.98:
            codes.append("eta_lorentz")
        elif self.success and self.eta <= 0.02:
            codes.append("eta_gauss")
        if self.success and self.rwp > 10.0:
            codes.append("rwp_high")
        if self.success and self.fwhm_err > 0.15 * self.fwhm > 0:
            codes.append("fwhm_err")
        return codes

    def quality_flags(self) -> list[str]:
        """拟合可信度标记（当前语言的文案）。这些标记会进入报告，避免"看起来精确其实不可靠"。"""
        flags: list[str] = []
        if not self.success:
            flags.append(self.message or tr("pf.not_converged"))
            return flags
        if self.eta >= 0.98:
            flags.append(tr("pf.eta_lorentz"))
        elif self.eta <= 0.02:
            flags.append(tr("pf.eta_gauss"))
        if self.rwp > 10.0:
            flags.append(tr("pf.rwp_high", v=self.rwp))
        if self.fwhm_err > 0.15 * self.fwhm > 0:
            flags.append(tr("pf.fwhm_err"))
        if self.neighbors > 0:
            flags.append(tr("pf.neighbors", n=self.neighbors))
        return flags

    def summary(self) -> str:
        return (f"2θ={self.center:.4f}°  FWHM={self.fwhm:.4f}°  "
                f"η={self.eta:.2f}  Rwp={self.rwp:.2f}%")


def _local_fwhm_estimate(x: np.ndarray, y: np.ndarray, center: float, step: float) -> float:
    """用半高宽估初值：在 center 附近找连续高于半高的段长度。"""
    i = int(np.argmin(np.abs(x - center)))
    base = float(np.percentile(y, 15))
    peak_h = float(y[i] - base)
    if peak_h <= 0:
        return max(step * 3, 0.05)
    half = base + 0.5 * peak_h
    j = i
    while j > 0 and y[j] > half:
        j -= 1
    k = i
    while k < y.size - 1 and y[k] > half:
        k += 1
    w = (k - j) * step
    return float(np.clip(w, step * 2.0, 8.0))


def fit_region(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    centers: list[float],
    *,
    window: float = 1.5,
    wavelength: float = 1.5405980,
    wavelength2: float | None = 1.5444260,
    anode: str = "Cu",
    strip_ka2: bool = True,
    target: float | None = None,
    fwhm_guess: dict[float, float] | None = None,
) -> PeakFit:
    """在窗口中同时拟合 ``centers`` 里的所有峰，返回 ``target`` 峰的结果。

    ``centers`` 应包含目标峰与其窗口内的邻峰（按 2θ 升序）。
    ``target`` 默认取 centers[0]。
    """
    x = np.asarray(two_theta, dtype=float)
    y = np.asarray(intensity, dtype=float)
    lo, hi = float(x.min()), float(x.max())
    if x.size < 8 or not centers:
        return PeakFit(float("nan"), float("nan"), 0.5, 0.0, 0.0, float("nan"),
                       0.0, 0.0, success=False, message=tr("pf.no_points"))

    tgt = float(target if target is not None else centers[0])
    ref = float(np.mean(centers))
    step = float(np.median(np.diff(x))) if x.size > 2 else 0.01

    # -- 初值与边界 -------------------------------------------------------
    p0: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    base_lo = float(np.percentile(y, 10))
    ymax = float(np.max(y)) if y.size else 1.0
    for c in centers:
        i = int(np.argmin(np.abs(x - c)))
        h0 = max(float(y[i] - base_lo), ymax * 0.02, 1.0)
        f0 = (fwhm_guess or {}).get(c) or _local_fwhm_estimate(x, y, c, step)
        p0 += [c, f0, 0.5, h0]
        lower += [max(c - 0.35 * window, lo), max(step * 1.05, 1e-3), 0.0, 0.0]
        upper += [min(c + 0.35 * window, hi), window * 2.2, 1.0, h0 * 8 + 1.0]
    p0 += [base_lo, 0.0]
    lower += [-np.inf, -np.inf]
    upper += [np.inf, np.inf]

    shift = 0.0
    ratio = 0.0
    lam2 = wavelength2
    if strip_ka2 and lam2 and lam2 > wavelength:
        ratio = KA2_RATIO.get(anode, 0.5)

    def model(p: np.ndarray) -> np.ndarray:
        n = len(centers)
        out = np.full_like(x, p[4 * n] + p[4 * n + 1] * (x - ref))
        for k in range(n):
            c, f, e, h = p[4 * k:4 * k + 4]
            yk = pseudo_voigt(x, c, f, e)
            if ratio > 0:
                yk = yk + ratio * pseudo_voigt(x, c + ka2_position(c, wavelength, lam2) - c, f, e)
            out = out + h * yk
        return out

    sigma = np.sqrt(np.maximum(y, 1.0))
    x_scale = []
    for _ in centers:
        x_scale += [0.05, 0.05, 0.1, max(ymax, 1.0)]
    x_scale += [max(base_lo, 1.0), 0.1]

    try:
        sol = least_squares(lambda p: (model(p) - y) / sigma, p0,
                            bounds=(lower, upper), method="trf",
                            x_scale=x_scale, max_nfev=6000)
    except Exception as exc:  # pragma: no cover - 数值兜底
        return PeakFit(tgt, float("nan"), 0.5, 0.0, 0.0, float("nan"), 0.0, 0.0,
                       success=False, message=tr("pf.fit_error", exc=exc), window=(lo, hi))

    p = sol.x
    n = len(centers)
    calc = model(p)
    wss = float(np.sum(((calc - y) / sigma) ** 2))
    rwp = float(np.sqrt(wss / max(np.sum((y / sigma) ** 2), 1e-12)) * 100.0)

    # 定位目标峰参数
    idx = int(np.argmin([abs(p[4 * k] - tgt) for k in range(n)]))
    c, f, e, h = (float(v) for v in p[4 * idx:4 * idx + 4])
    eta = float(np.clip(e, 0.0, 1.0))
    area = h * integral_width(f, eta)
    profile = h * pseudo_voigt(x, c, f, eta)
    if ratio > 0:
        profile = profile + h * ratio * pseudo_voigt(
            x, c + ka2_position(c, wavelength, lam2) - c, f, eta)

    # 参数不确定度
    fwhm_err = center_err = 0.0
    try:
        cov = np.linalg.pinv(sol.jac.T @ sol.jac)
        dof = max(x.size - p.size, 1)
        s2 = 2.0 * sol.cost / dof
        fwhm_err = float(np.sqrt(max(cov[4 * idx + 1, 4 * idx + 1] * s2, 0.0)))
        center_err = float(np.sqrt(max(cov[4 * idx, 4 * idx] * s2, 0.0)))
    except Exception:
        pass

    ok = bool(sol.success) and np.isfinite(f) and f > 0
    return PeakFit(
        center=c, fwhm=f, eta=eta, height=h, area=area,
        beta_int=integral_width(f, eta),
        bg0=float(p[4 * n]), bg1=float(p[4 * n + 1]),
        fwhm_err=fwhm_err, center_err=center_err, rwp=rwp,
        success=ok, message="" if ok else (sol.message or tr("pf.not_converged")),
        window=(lo, hi), ka2_used=ratio > 0, neighbors=n - 1,
        region_two_theta=x, region_observed=y, region_calculated=calc,
        profile=profile,
    )


def fit_single_peak(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    center_guess: float,
    window: float = 1.2,
    *,
    wavelength: float = 1.5405980,
    wavelength2: float | None = 1.5444260,
    anode: str = "Cu",
    strip_ka2: bool = True,
) -> PeakFit:
    """单峰（无邻峰）拟合，兼容旧接口。"""
    x = np.asarray(two_theta, dtype=float)
    y = np.asarray(intensity, dtype=float)
    m = (x >= center_guess - window) & (x <= center_guess + window)
    if m.sum() < 8:
        return PeakFit(center_guess, float("nan"), 0.5, 0.0, 0.0, float("nan"),
                       0.0, 0.0, success=False, message=tr("pf.no_points"),
                       window=(center_guess - window, center_guess + window))
    return fit_region(x[m], y[m], [center_guess], window=window,
                      wavelength=wavelength, wavelength2=wavelength2,
                      anode=anode, strip_ka2=strip_ka2, target=center_guess)
