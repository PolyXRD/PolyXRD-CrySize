"""Williamson-Hall 的三个变体：UDM / USDM / UDEDM，以及按晶向分组。

三个变体共享同一条测量式，区别只在**横轴**（即应变的物理假设）：

===================  ==================================  ==============  ==================
变体                 横轴 X                               斜率含义        应变反算
===================  ==================================  ==============  ==================
UDM  均匀形变        4 sinθ                               ε（无量纲）     ε = slope
USDM 均匀应力        4 sinθ / E(hkl)                       σ（MPa）        ε = σ / E(hkl)
UDEDM 均匀形变能密度  4 sinθ · √(2 / E(hkl))                √u             ε = √(2u / E(hkl))
===================  ==================================  ==============  ==================

纵轴恒为 β·cosθ（β 取积分宽度，rad），截距恒为 Kλ/D。

* UDM 假设微应变在各方向相同（各向同性均匀形变）—— 这是经典 W-H
  （Williamson & Hall, *Acta Metall.* 1 (1953) 22）。
* USDM 假设**应力**在各方向相同，应变则因各晶向刚度不同而不同
  （σ 均匀、ε = σ/E）。W-H 原文已讨论此情形；现代表述见
  Noyan & Cohen, *Residual Stress: Measurement by Diffraction and
  Interpretation*, Springer (1987)。
* UDEDM 假设**形变能密度** u = ε²E/2 各向相同。常用于纳米粉体的
  峰宽分析，见 Bindu & Thomas, *J. Theor. Appl. Phys.* 8 (2014) 123。

**关键退化**：若 E(hkl) 取常数（未给弹性数据），USDM 与 UDEDM 只是 UDM 的
重参数化 —— σ = ε·E、u = ε²E/2，三条拟合线完全相同、R² 相同，不会产生
新信息。此时 ``degenerate=True``，界面与报告必须据此提示。

按晶向分组
----------
各向异性样品的宽化随方向变化，把所有峰放一起回归会拉低 R²、并使 D、ε
失去物理意义。分组做法：按 Γ = (h²k²+k²l²+l²h²)/(h²+k²+l²)² 分组 —— Γ 相同
则 E(hkl) 相同，同一组内做 W-H 才自洽。立方晶系里 {111}/{222}、{200}/{400}、
{220}/{440} 的 Γ 分别相同，正好构成可回归的组，前提是谱里能测到这些级次。
组内不足 2 个峰时该组不回归。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from crysize.core.elasticity import ElasticParams, index_peaks
from crysize.core.instrument import InstrumentModel
from crysize.core.profile import PeakFit
from crysize.core.size import (DEG2RAD, K_INTEGRAL, _corrected_width,
                               _DOUBTFUL_CODES)
from crysize.i18n import tr

MODELS = ("udm", "usdm", "udedm")

#: 斜率 → 应力的单位换算：内部 E 用 GPa，输出 σ 用 MPa、u 用 MJ·m⁻³
_GPA = 1.0


@dataclass
class WHVariantPoint:
    """单个峰在某变体坐标系下的坐标。"""

    two_theta: float
    beta_deg: float
    x: float
    y: float
    hkl: tuple[int, int, int] | None = None
    E_hkl: float = float("nan")      # GPa
    gamma: float = float("nan")
    strain: float = float("nan")     # 该峰反算的 ε
    ok: bool = True
    quality: list[str] = field(default_factory=list)
    quality_codes: list[str] = field(default_factory=list)


@dataclass
class WHVariantFit:
    """某变体（或某个晶向组）的回归结果。"""

    model: str = "udm"
    size_nm: float = float("nan")
    slope: float = float("nan")
    intercept: float = float("nan")
    r2: float = float("nan")
    n: int = 0
    strain_pct: float = float("nan")      # 平均微应变 %
    stress_mpa: float = float("nan")      # USDM 的 σ（MPa）
    energy_mjm3: float = float("nan")     # UDEDM 的 u（MJ·m⁻³）
    points: list[WHVariantPoint] = field(default_factory=list)
    groups: list["WHVariantFit"] = field(default_factory=list)
    gamma: float = float("nan")           # 分组时该组的 Γ
    group_label: str = ""
    degenerate: bool = False              # E(hkl) 为常数 → 与 UDM 等价
    warnings: list[str] = field(default_factory=list)


def _regress(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """最小二乘直线，返回 (slope, intercept, r2)。"""
    if x.size < 2 or np.ptp(x) < 1e-12:
        return float("nan"), float("nan"), float("nan")
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1e-18)
    return float(slope), float(intercept), float(r2)


def _prepare(
    fits: list[PeakFit],
    *,
    instrument: InstrumentModel | None,
    elastic: ElasticParams | None,
) -> tuple[list[WHVariantPoint], bool]:
    """算出每个峰的 (β, θ, hkl, E, Γ)。返回 (点集, 是否可用 E(hkl))。"""
    use_elastic = bool(elastic is not None and elastic.usable)
    pts: list[WHVariantPoint] = []
    for fit in fits:
        beta, _fw, _flag = _corrected_width(fit, instrument, "integral")
        codes = list(fit.quality_codes())
        unreliable = bool(_DOUBTFUL_CODES & set(codes))
        ok = bool(fit.success and np.isfinite(beta) and beta > 0 and not unreliable)
        theta = np.radians(fit.center / 2.0)
        pts.append(WHVariantPoint(
            two_theta=fit.center,
            beta_deg=beta if np.isfinite(beta) else float("nan"),
            x=0.0,
            y=float(beta * DEG2RAD * np.cos(theta)) if ok else float("nan"),
            ok=ok,
            quality=list(fit.quality_flags()),
            quality_codes=codes,
        ))
    return pts, use_elastic


def _attach_hkl(
    pts: list[WHVariantPoint],
    elastic: ElasticParams | None,
    wavelength: float,
) -> bool:
    """指标化并填 hkl / E / Γ。返回 E(hkl) 是否逐峰可用。"""
    if elastic is None or not elastic.usable:
        for p in pts:
            p.E_hkl = float("nan")
        return False
    hkls = index_peaks([p.two_theta for p in pts], wavelength, elastic)
    ok_count = 0
    for p, hkl in zip(pts, hkls):
        p.hkl = hkl
        if hkl is None:
            p.E_hkl = float("nan")
            continue
        p.E_hkl = elastic.youngs(*hkl)
        p.gamma = elastic.gamma(*hkl)
        if np.isfinite(p.E_hkl):
            ok_count += 1
    return ok_count >= max(2, len(pts))


def _x_value(p: WHVariantPoint, model: str, theta: float, E_default: float) -> float:
    s = 4.0 * np.sin(theta)
    E = p.E_hkl if np.isfinite(p.E_hkl) else E_default
    if model == "udm" or not np.isfinite(E) or E <= 0:
        return float(s)
    if model == "usdm":
        return float(s / E)
    return float(s * np.sqrt(2.0 / E))


def _strain_from(p: WHVariantPoint, model: str, slope: float, E_default: float) -> float:
    """由斜率反算该峰的 ε。"""
    if not np.isfinite(slope):
        return float("nan")
    E = p.E_hkl if np.isfinite(p.E_hkl) else E_default
    if model == "udm" or not np.isfinite(E) or E <= 0:
        return float(slope)
    if model == "usdm":
        return float(slope / E)
    return float(np.sqrt(max(2.0 * slope * slope / E, 0.0)))


def _fit_group(pts: list[WHVariantPoint], model: str, K: float,
               wavelength: float, E_default: float) -> WHVariantFit:
    good = [p for p in pts if p.ok and np.isfinite(p.y)]
    out = WHVariantFit(model=model)
    out.n = len(good)
    if out.n < 2:
        out.warnings.append(tr("whv.too_few"))
        return out
    x = np.array([p.x for p in good])
    y = np.array([p.y for p in good])
    out.slope, out.intercept, out.r2 = _regress(x, y)
    if np.isfinite(out.intercept) and out.intercept > 0:
        out.size_nm = float(K * wavelength / out.intercept / 10.0)
    for p in good:
        p.strain = _strain_from(p, model, out.slope, E_default)
    strains = [p.strain for p in good if np.isfinite(p.strain)]
    if strains:
        out.strain_pct = float(np.mean(strains) * 100.0)
    if model == "usdm" and np.isfinite(out.slope):
        out.stress_mpa = float(out.slope * 1000.0)        # GPa → MPa
    if model == "udedm" and np.isfinite(out.slope):
        out.energy_mjm3 = float(out.slope * out.slope * 1000.0)  # GPa → MJ·m⁻³
    if model == "udm" and np.isfinite(out.slope):
        out.strain_pct = float(out.slope * 100.0)
    if out.slope < 0:
        out.warnings.append(tr("whv.neg_slope"))
    if np.isfinite(out.r2) and out.r2 < 0.6:
        out.warnings.append(tr("whv.low_r2", r2=out.r2))
    return out


def compute_wh_variant(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    model: str = "udm",
    elastic: ElasticParams | None = None,
    group_by_direction: bool = False,
    K: float = K_INTEGRAL,
) -> WHVariantFit:
    """计算某一 W-H 变体，可选按晶向分组。"""
    pts, _ = _prepare(fits, instrument=instrument, elastic=elastic)
    has_E = _attach_hkl(pts, elastic, wavelength)
    E_default = elastic.youngs_mean() if (elastic is not None and elastic.usable) else float("nan")
    degenerate = (model in ("usdm", "udedm")) and not has_E
    for p in pts:
        theta = np.radians(p.two_theta / 2.0)
        p.x = _x_value(p, model, theta, E_default)

    if group_by_direction:
        buckets: dict[float, list[WHVariantPoint]] = {}
        for p in pts:
            g = p.gamma if np.isfinite(p.gamma) else float("nan")
            key = round(g, 3) if np.isfinite(g) else None
            if key is None:
                continue
            buckets.setdefault(key, []).append(p)
        if not buckets:
            out = _fit_group(pts, model, K, wavelength, E_default)
            out.degenerate = degenerate
            out.warnings.append(tr("whv.no_index"))
            return out
        groups: list[WHVariantFit] = []
        for g, gpts in sorted(buckets.items()):
            gf = _fit_group(gpts, model, K, wavelength, E_default)
            gf.gamma = g
            gf.group_label = "、".join(
                f"({''.join(str(v) for v in p.hkl)})" for p in gpts if p.hkl) or "—"
            groups.append(gf)
        if not any(g.n >= 2 for g in groups):
            # 每组都不足 2 个峰（谱里没有同族高级次），分组无法回归 —— 退回整体
            out = _fit_group(pts, model, K, wavelength, E_default)
            out.points = pts
            out.degenerate = degenerate
            out.warnings.insert(0, tr("whv.group_fallback"))
            return out
        sizes = [g.size_nm for g in groups if np.isfinite(g.size_nm)]
        r2s = [g.r2 for g in groups if np.isfinite(g.r2)]
        usable = [g for g in groups if g.n >= 2]
        merged = WHVariantFit(model=model, groups=usable, degenerate=degenerate)
        merged.size_nm = float(np.mean(sizes)) if sizes else float("nan")
        merged.r2 = float(np.mean(r2s)) if r2s else float("nan")
        merged.n = sum(g.n for g in usable)
        strains = [g.strain_pct for g in usable if np.isfinite(g.strain_pct)]
        merged.strain_pct = float(np.mean(strains)) if strains else float("nan")
        merged.points = pts
        if len(usable) < 2:
            merged.warnings.append(tr("whv.group_single"))
        for g in usable:
            merged.warnings.extend(g.warnings)
        merged.warnings = list(dict.fromkeys(merged.warnings))
        return merged

    out = _fit_group(pts, model, K, wavelength, E_default)
    out.points = pts
    out.degenerate = degenerate
    if degenerate:
        out.warnings.append(tr("whv.degenerate"))
    if model in ("usdm", "udedm") and not has_E:
        out.warnings.append(tr("whv.no_elastic"))
    if out.n < 4 and out.n >= 2:
        out.warnings.append(tr("whv.few", n=out.n))
    return out
