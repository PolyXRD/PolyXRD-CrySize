"""计算方法注册表：5 组、7 种方法，以及统一的选型说明。

分组与细分
----------
===========  ====================================  =============================
组           细分方法（7 种）                       额外输入要求
===========  ====================================  =============================
① 谢乐法      scherrer_fwhm（FWHM 口径，K=0.89）     标样（可选，推荐）
             scherrer_integral（积分宽度，K=1.0）
② W-H/UDM    wh_udm                                标样（强烈推荐）
③ W-H/USDM   wh_usdm                               标样 + 晶格参数与弹性常数
④ W-H/UDEDM  wh_udedm                              标样 + 晶格参数与弹性常数
⑤ Warren     wa_single（单峰 Voigt 近似）           标样
   -Averbach  wa_fourier（多级反射傅里叶法）         标样 + 同族多级反射
===========  ====================================  =============================

另外，"按晶向分组"是 ②③④ 共用的**增强开关**（不是独立方法）：开启后按
Γ = (h²k²+k²l²+l²h²)/(h²+k²+l²)² 分组，组内分别回归，用于各向异性样品。
它需要晶格参数才能指标化，故与 USDM/UDEDM 的输入要求同源。

选型总原则
---------
1. 只想要一个"晶粒尺寸量级"→ ①（最省事，但不能分尺寸与应变）。
2. 尺寸与微应变要分开 → ②；各向同性、无弹性数据时 ②③④ 结果一致。
3. 有可靠弹性常数且各向异性明显 → ③（应力型）或 ④（能量型），比较三者
   R² 与残差结构，取最优。
4. 有同族多级反射、谱质量好 → ⑤ Fourier 法，它给出体积加权尺寸与
   随 L 变化的均方应变，是唯一不预设线型叠加的方法。
5. 无多级反射但要"类 W-A"结果 → ⑤ 单峰近似，代价是强依赖线型假设。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from crysize.core.elasticity import ElasticParams
from crysize.core.instrument import InstrumentModel
from crysize.core.profile import PeakFit
from crysize.core.size import (K_FWHM, ScherrerResult, WHResult,
                               compute_scherrer)
from crysize.core.warren import WAResult, compute_wa_fourier, compute_wa_single
from crysize.core.wh_models import WHVariantFit, compute_wh_variant
from crysize.i18n import tr

#: 次级量的类型
SECONDARY_NONE = "none"
SECONDARY_STRAIN = "strain"
SECONDARY_STRESS = "stress"
SECONDARY_ENERGY = "energy"


@dataclass(frozen=True)
class MethodSpec:
    """一种方法的静态描述（不随数据变化）。"""

    id: str
    group: str
    secondary: str = SECONDARY_NONE
    needs_standard: bool = False           # 无标样时结果不可信（仅提示）
    needs_elastic: bool = False            # 缺弹性常数则退化
    needs_indexing: bool = False           # 缺晶格参数则不可用（分组/多级）
    needs_multiorder: bool = False         # 需同族多级反射
    supports_grouping: bool = False        # 是否响应"按晶向分组"开关


SPECS: tuple[MethodSpec, ...] = (
    MethodSpec("scherrer_fwhm", "scherrer"),
    MethodSpec("scherrer_integral", "scherrer"),
    MethodSpec("wh_udm", "udm", SECONDARY_STRAIN, needs_standard=True,
               supports_grouping=True),
    MethodSpec("wh_usdm", "usdm", SECONDARY_STRESS, needs_standard=True,
               needs_elastic=True, supports_grouping=True),
    MethodSpec("wh_udedm", "udedm", SECONDARY_ENERGY, needs_standard=True,
               needs_elastic=True, supports_grouping=True),
    MethodSpec("wa_single", "warren", SECONDARY_STRAIN, needs_standard=True),
    MethodSpec("wa_fourier", "warren", SECONDARY_STRAIN, needs_standard=True,
               needs_indexing=True, needs_multiorder=True),
)

SPECS_BY_ID: dict[str, MethodSpec] = {s.id: s for s in SPECS}

#: 5 组及其细分方法（顺序即界面/报告展示顺序）
GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("scherrer", ("scherrer_fwhm", "scherrer_integral")),
    ("udm", ("wh_udm",)),
    ("usdm", ("wh_usdm",)),
    ("udedm", ("wh_udedm",)),
    ("warren", ("wa_single", "wa_fourier")),
)

GROUP_IDS: tuple[str, ...] = tuple(g for g, _ in GROUPS)
METHOD_IDS: tuple[str, ...] = tuple(m for _g, ms in GROUPS for m in ms)


def spec_of(method_id: str) -> MethodSpec:
    return SPECS_BY_ID.get(method_id, SPECS[0])


def group_of(method_id: str) -> str:
    return spec_of(method_id).group


def method_name(method_id: str) -> str:
    return tr(f"m.{method_id}.name")


def group_name(group_id: str) -> str:
    return tr(f"g.{group_id}.name")


def method_scene(method_id: str) -> str:
    """选择场景（i18n）。"""
    return tr(f"m.{method_id}.scene")


def method_assume(method_id: str) -> str:
    return tr(f"m.{method_id}.assume")


def method_need(method_id: str) -> str:
    return tr(f"m.{method_id}.need")


def method_limit(method_id: str) -> str:
    return tr(f"m.{method_id}.limit")


@dataclass
class MethodOutcome:
    """一种方法在同一次分析下的结果（统一封装，供界面/报告/CSV 共用）。"""

    method_id: str
    size_nm: float = float("nan")
    secondary: float = float("nan")       # ε% / σ(MPa) / u(MJ·m⁻³)
    secondary_kind: str = SECONDARY_NONE
    r2: float = float("nan")
    n_used: int = 0
    available: bool = True
    reason: str = ""                      # 不可用/退化原因（已翻译）
    warnings: list[str] = field(default_factory=list)
    detail: ScherrerResult | WHVariantFit | WAResult | WHResult | None = None

    @property
    def secondary_label(self) -> str:
        if self.secondary_kind == SECONDARY_STRAIN:
            return tr("m.sec.strain")
        if self.secondary_kind == SECONDARY_STRESS:
            return tr("m.sec.stress")
        if self.secondary_kind == SECONDARY_ENERGY:
            return tr("m.sec.energy")
        return "—"

    @property
    def secondary_unit(self) -> str:
        if self.secondary_kind == SECONDARY_STRAIN:
            return "%"
        if self.secondary_kind == SECONDARY_STRESS:
            return "MPa"
        if self.secondary_kind == SECONDARY_ENERGY:
            return "MJ·m⁻³"
        return ""


def evaluate(
    method_id: str,
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    elastic: ElasticParams | None = None,
    group_by_direction: bool = False,
) -> MethodOutcome:
    """按方法 ID 计算，返回统一结果对象。"""
    spec = spec_of(method_id)
    out = MethodOutcome(method_id=method_id, secondary_kind=spec.secondary)

    if method_id == "scherrer_fwhm":
        res = compute_scherrer(fits, wavelength=wavelength, instrument=instrument,
                               width_mode="fwhm", K=K_FWHM)
        out.detail = res
        out.size_nm = res.mean_number
        out.n_used = res.n_valid
        out.warnings = list(res.warnings)
        out.available = res.n_valid > 0
        if not out.available:
            out.reason = tr("m.reason.no_valid_peak")
        return out

    if method_id == "scherrer_integral":
        res = compute_scherrer(fits, wavelength=wavelength, instrument=instrument,
                               width_mode="integral", K=1.0)
        out.detail = res
        out.size_nm = res.mean_number
        out.n_used = res.n_valid
        out.warnings = list(res.warnings)
        out.available = res.n_valid > 0
        if not out.available:
            out.reason = tr("m.reason.no_valid_peak")
        return out

    if method_id in ("wh_udm", "wh_usdm", "wh_udedm"):
        model = method_id.split("_", 1)[1]
        res = compute_wh_variant(fits, wavelength=wavelength, instrument=instrument,
                                 model=model, elastic=elastic,
                                 group_by_direction=group_by_direction)
        out.detail = res
        out.size_nm = res.size_nm
        out.r2 = res.r2
        out.n_used = res.n
        out.warnings = list(res.warnings)
        if model == "usdm":
            out.secondary = res.stress_mpa
        elif model == "udedm":
            out.secondary = res.energy_mjm3
        else:
            out.secondary = res.strain_pct
        out.available = bool(np.isfinite(res.size_nm) and res.n >= 2)
        if not out.available:
            out.reason = tr("m.reason.too_few")
        elif res.degenerate:
            out.reason = tr("m.reason.degenerate")
        if group_by_direction and (elastic is None or not elastic.usable):
            out.reason = tr("m.reason.no_lattice")
        return out

    if method_id == "wa_single":
        res = compute_wa_single(fits, wavelength=wavelength, instrument=instrument)
        out.detail = res
        out.size_nm = res.size_nm
        out.secondary = res.strain_pct
        out.n_used = res.n_valid
        out.warnings = list(res.warnings)
        out.available = res.n_valid > 0
        if not out.available:
            out.reason = tr("m.reason.no_valid_peak")
        return out

    if method_id == "wa_fourier":
        res = compute_wa_fourier(fits, wavelength=wavelength, instrument=instrument)
        out.detail = res
        out.size_nm = res.size_nm
        out.secondary = res.strain_pct
        out.r2 = res.r2
        out.n_used = len([p for p in res.peaks if p.ok])
        out.warnings = list(res.warnings)
        out.available = bool(np.isfinite(res.size_nm))
        if not out.available:
            out.reason = res.warnings[0] if res.warnings else tr("m.reason.wa_unmet")
        return out

    out.available = False
    out.reason = tr("m.reason.unknown")
    return out


def evaluate_all(
    fits: list[PeakFit],
    *,
    wavelength: float,
    instrument: InstrumentModel | None = None,
    elastic: ElasticParams | None = None,
    group_by_direction: bool = False,
) -> dict[str, MethodOutcome]:
    """一次算完 7 种方法（计算量很小，便于横向对比）。"""
    return {
        mid: evaluate(mid, fits, wavelength=wavelength, instrument=instrument,
                      elastic=elastic, group_by_direction=group_by_direction)
        for mid in METHOD_IDS
    }
