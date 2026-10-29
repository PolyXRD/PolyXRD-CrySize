"""晶粒尺寸计算：Scherrer 单峰法与 Williamson-Hall 全谱法。

Scherrer 方程（Scherrer, Gött. Nachr. 2 (1918) 98）::

    D = K·λ / (β·cosθ)

    D   晶粒尺寸（垂直于衍射面方向的相干散射柱长）
    K   形状因子：球状晶体用 FWHM 时 K=0.89；用积分宽度时 K=1.0
    λ   波长（Å）
    β   纯物理宽化（FWHM 或积分宽度，rad）
    θ   布拉格角（rad）

Williamson-Hall（Williamson & Hall, Acta Metall. 1 (1953) 22）::

    β·cosθ = K·λ/D + 4·ε·sinθ

    斜率给出微应变 ε（横轴取 4sinθ 时），截距给出 Kλ/D（尺寸）。该式由积分宽度推导，
    因此 β 取**积分宽度**且 K=1 才是标准用法。

宽度校正的两条路径
------------------
* **FWHM 口径**：FWHM 不可相加，只有各分量均近似高斯时才有
  FWHM² = ΣFWHM_i²，故用平方差 β = √(FWHM_obs² − FWHM_inst²)。
* **积分宽度口径**：卷积的积分宽度等于各分量之和（Stokes, Proc. Phys.
  Soc. A 61 (1948) 382），与线形无关，故 β = β_obs − β_inst 更严格。

若仪器宽度 ≥ 观测宽度，该峰没有可测的物理宽化（晶粒过大，或标样线宽
取得偏宽），β 无解：标记并排除出平均，不强行填 0。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from crysize.core.instrument import InstrumentModel
from crysize.core.peaks import d_spacing
from crysize.core.profile import PeakFit
from crysize.i18n import tr

DEG2RAD = np.pi / 180.0

#: 默认形状因子
K_FWHM = 0.89
K_INTEGRAL = 1.0


@dataclass
class PeakSize:
    """单峰晶粒尺寸结果。"""

    two_theta: float
    d: float                 # 面间距 Å
    fwhm_obs: float          # 观测 FWHM（度）
    fwhm_inst: float         # 仪器 FWHM（度）；无标样时为 nan
    beta_deg: float          # 用于计算的纯物理宽化（度）
    beta_rad: float
    size_nm: float
    intensity: float = 0.0   # 净峰高（加权用）
    eta: float = 0.5
    width_mode: str = "fwhm"
    ok: bool = True
    flag: str = ""
    quality: list[str] = field(default_factory=list)          # 当前语言文案
    quality_codes: list[str] = field(default_factory=list)    # 语言无关质量码

    @property
    def beta_arcsec(self) -> float:
        return self.beta_deg * 3600.0


@dataclass
class ScherrerResult:
    peaks: list[PeakSize] = field(default_factory=list)
    mean_number: float = float("nan")     # 数目平均 Σ D_i / N
    mean_intensity: float = float("nan")  # 强度加权 Σ(I·D)/ΣI
    mean_volume: float = float("nan")     # 体积加权 Σ(I·D⁴)/Σ(I·D³)
    std_number: float = float("nan")
    K: float = K_FWHM
    wavelength: float = 1.5405980
    width_mode: str = "fwhm"
    corrected: bool = False               # 是否做了仪器宽化校正
    instrument_note: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def n_valid(self) -> int:
        return len([p for p in self.peaks if p.ok and np.isfinite(p.size_nm)])

    def spread(self) -> float:
        """各峰 D 值的相对离散度（标准差/均值，%）。"""
        vals = [p.size_nm for p in self.peaks if p.ok and np.isfinite(p.size_nm)]
        if len(vals) < 2:
            return 0.0
        m = float(np.mean(vals))
        return 100.0 * float(np.std(vals, ddof=1)) / m if m > 0 else 0.0


@dataclass
class WHPoint:
    two_theta: float
    x: float          # 4 sinθ
    y: float          # β_int·cosθ（rad）
    beta_deg: float
    ok: bool = True
    quality: list[str] = field(default_factory=list)          # 当前语言文案
    quality_codes: list[str] = field(default_factory=list)    # 语言无关质量码


@dataclass
class WHResult:
    points: list[WHPoint] = field(default_factory=list)
    slope: float = float("nan")      # 斜率 = ε（横轴取 4sinθ）
    intercept: float = float("nan")  # Kλ/D（rad）
    size_nm: float = float("nan")
    strain: float = float("nan")     # ε（无量纲）
    strain_pct: float = float("nan")
    r2: float = float("nan")
    K: float = K_INTEGRAL
    wavelength: float = 1.5405980
    corrected: bool = False
    instrument_note: str = ""
    warnings: list[str] = field(default_factory=list)
    mean_size_nm: float = float("nan")   # 各峰独立 Scherrer 的算术平均（积分宽度，K=1，对照用）

    @property
    def n_valid(self) -> int:
        return len([p for p in self.points if p.ok])


def scherrer_size(beta_deg: float, two_theta: float, wavelength: float, K: float) -> float:
    """谢乐方程，返回 nm。β 为度，2θ 为度。"""
    theta = np.radians(two_theta / 2.0)
    beta_rad = beta_deg * DEG2RAD
    if beta_rad <= 0 or theta <= 0:
        return float("nan")
    return float(K * wavelength / (beta_rad * np.cos(theta)) / 10.0)


#: 判定"拟合可信度不足"的结构化质量码（命中即不参与统计）。
#: 绝不能用译文做子串匹配 —— 换语言门控就失效，故用 profile.quality_codes()。
_DOUBTFUL_CODES = frozenset({"not_converged", "eta_lorentz", "rwp_high", "fwhm_err"})


def _is_doubtful(peak: "PeakSize") -> bool:
    return bool(_DOUBTFUL_CODES & set(peak.quality_codes))


def _corrected_width(
    fit: PeakFit,
    instrument: InstrumentModel | None,
    mode: str,
) -> tuple[float, float, str]:
    """返回 (校正后宽度°, 仪器 FWHM°, 标记)。"""
    obs = fit.fwhm if mode == "fwhm" else fit.beta_int
    if instrument is None or not instrument.usable:
        return obs, float("nan"), "no_standard"

    fw_inst = instrument.fwhm_at(fit.center)
    if mode == "fwhm":
        if fit.fwhm <= fw_inst:
            return float("nan"), fw_inst, "instrument_exceeds"
        return float(np.sqrt(fit.fwhm**2 - fw_inst**2)), fw_inst, ""

    b_inst = instrument.beta_int_at(fit.center)
    if fit.beta_int <= b_inst:
        return float("nan"), fw_inst, "instrument_exceeds"
    return float(fit.beta_int - b_inst), fw_inst, ""


def compute_scherrer(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    width_mode: str = "fwhm",
    K: float | None = None,
) -> ScherrerResult:
    """由一组峰拟合结果计算各峰晶粒尺寸与平均值。"""
    if K is None:
        K = K_FWHM if width_mode == "fwhm" else K_INTEGRAL
    res = ScherrerResult(K=K, wavelength=wavelength, width_mode=width_mode,
                         corrected=instrument is not None and instrument.usable,
                         instrument_note=instrument.note if instrument else "")

    n_exceed = 0
    for fit in fits:
        beta, fw_inst, flag = _corrected_width(fit, instrument, width_mode)
        size = scherrer_size(beta, fit.center, wavelength, K) if np.isfinite(beta) else float("nan")
        if flag == "instrument_exceeds":
            n_exceed += 1
        ok = bool(fit.success and np.isfinite(size) and size > 0)
        codes = fit.quality_codes()
        ps = PeakSize(
            two_theta=fit.center,
            d=d_spacing(fit.center, wavelength),
            fwhm_obs=fit.fwhm,
            fwhm_inst=fw_inst,
            beta_deg=beta,
            beta_rad=beta * DEG2RAD if np.isfinite(beta) else float("nan"),
            size_nm=size,
            intensity=max(fit.height, 1e-9),
            eta=fit.eta,
            width_mode=width_mode,
            ok=ok,
            flag=flag if not ok else ("no_standard" if flag == "no_standard" else ""),
            quality=fit.quality_flags(),
            quality_codes=codes,
        )
        # 拟合质量不达标的峰：保留数值供查看，但不参与平均值与 W-H 回归
        if ok and _is_doubtful(ps):
            ps.ok = False
            ps.flag = "unreliable"
        res.peaks.append(ps)

    good = [p for p in res.peaks if p.ok and np.isfinite(p.size_nm)]
    if good:
        vals = np.array([p.size_nm for p in good], dtype=float)
        inten = np.array([p.intensity for p in good], dtype=float)
        res.mean_number = float(vals.mean())
        res.std_number = float(vals.std(ddof=1)) if vals.size > 1 else 0.0
        res.mean_intensity = float(np.sum(inten * vals) / np.sum(inten)) if inten.sum() > 0 else float("nan")
        num = float(np.sum(inten * vals**4))
        den = float(np.sum(inten * vals**3))
        res.mean_volume = num / den if den > 0 else float("nan")

    if not res.corrected:
        res.warnings.append(tr("w.no_standard"))
    if n_exceed:
        res.warnings.append(tr("w.n_exceed", n=n_exceed))
    if res.n_valid == 0:
        res.warnings.append(tr("w.all_exceed"))
    elif max((p.size_nm for p in res.peaks if p.ok), default=0) > 150:
        res.warnings.append(tr("w.too_large"))
    if res.spread() > 40 and res.n_valid >= 3:
        res.warnings.append(tr("w.spread", sp=res.spread()))

    doubtful = [p for p in res.peaks if p.ok and _is_doubtful(p)]
    if doubtful:
        pos = "、".join(f"{p.two_theta:.2f}°" for p in doubtful)
        res.warnings.append(tr("w.doubtful", pos=pos))
    return res


def compute_wh(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    K: float = K_INTEGRAL,
) -> WHResult:
    """Williamson-Hall 线性拟合。β 一律取积分宽度（rad）。"""
    res = WHResult(K=K, wavelength=wavelength,
                   corrected=instrument is not None and instrument.usable,
                   instrument_note=instrument.note if instrument else "")

    for fit in fits:
        beta, _fw_inst, flag = _corrected_width(fit, instrument, "integral")
        theta = np.radians(fit.center / 2.0)
        codes = fit.quality_codes()
        unreliable = bool(_DOUBTFUL_CODES & set(codes))
        ok = bool(fit.success and np.isfinite(beta) and beta > 0 and not unreliable)
        res.points.append(WHPoint(
            two_theta=fit.center,
            x=float(4.0 * np.sin(theta)),
            y=float(beta * DEG2RAD * np.cos(theta)) if ok else float("nan"),
            beta_deg=beta if np.isfinite(beta) else float("nan"),
            ok=ok,
            quality=fit.quality_flags(),
            quality_codes=codes,
        ))
        if ok is False and unreliable:
            res.warnings.append(tr("w.wh_dropped", tt=fit.center))

    good = [p for p in res.points if p.ok]
    if len(good) < 2:
        res.warnings.append(tr("w.wh_too_few"))
        return res

    x = np.array([p.x for p in good])
    y = np.array([p.y for p in good])
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    res.slope = float(slope)
    res.intercept = float(intercept)
    res.r2 = 1.0 - ss_res / max(ss_tot, 1e-18)
    # 横轴取 4sinθ 时，β·cosθ = Kλ/D + ε·(4sinθ)，故斜率即 ε（不要再除以 4）
    res.strain = float(slope)
    res.strain_pct = res.strain * 100.0

    if intercept > 0:
        res.size_nm = float(K * wavelength / intercept / 10.0)
    else:
        res.size_nm = float("nan")
        res.warnings.append(tr("w.wh_neg_intercept"))

    if len(good) < 4:
        res.warnings.append(tr("w.wh_few_peaks", n=len(good)))
    if slope < 0:
        res.warnings.append(tr("w.wh_neg_slope"))
    if res.r2 < 0.6:
        res.warnings.append(tr("w.wh_low_r2", r2=res.r2))

    # 对照：各峰独立 Scherrer 值。这里 β 是**积分宽度**，故必须用 K=1.0
    # （与 W-H 截距同一口径）；若沿用 K=0.89（FWHM 口径）会系统性偏小 11%，
    # 与本行的对照意义相悖。
    per = [scherrer_size(p.beta_deg, p.two_theta, wavelength, K_INTEGRAL)
           for p in good if np.isfinite(p.beta_deg)]
    if per:
        res.mean_size_nm = float(np.mean(per))

    if not res.corrected:
        res.warnings.append(tr("w.wh_no_standard"))
    return res
