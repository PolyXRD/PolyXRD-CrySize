"""立方晶系的方向杨氏模量 E(hkl) 与衍射峰指标化。

USDM / UDEDM 两个 W-H 变体的横轴含 E(hkl)：应变对宽化的贡献按方向上的
刚度加权，因此必须先知道每个峰对应的晶面指数与沿该方向的杨氏模量。

方向杨氏模量（立方晶系）
------------------------
柔度矩阵元由刚度常数给出（Nye, *Physical Properties of Crystals*,
Clarendon Press, 1957）::

    S11 = (c11 + c12) / [(c11 − c12)(c11 + 2c12)]
    S12 = −c12 / [(c11 − c12)(c11 + 2c12)]
    S44 = 1 / c44

沿 [hkl] 方向的杨氏模量倒数::

    1/E(hkl) = S11 − 2·(S11 − S12 − S44/2)·Γ
    Γ = (h²k² + k²l² + l²h²) / (h² + k² + l²)²

Γ 取值 0（[100]）到 1/3（[111]），刻画立方晶体的弹性各向异性。Γ 越分散，
各晶向的 E 差别越大，UDM 与 USDM/UDEDM 的结果差别也越大。

指标化
------
立方晶系 d = a / √(h²+k²+l²)，故 N = (a/d)² 必须是三个平方数之和。给定
d 的拟合误差，N 容差按 ``tol`` 判定；再按点阵类型的消光规则过滤：

* ``fcc``：h,k,l 全奇或全偶
* ``bcc``：h + k + l 为偶数
* ``simple``：无限制

指标化只能给出**可能的**指数。若 a 给错或样品非立方，此处会给出错误指标，
进而污染 E(hkl)。因此本模块只做匹配，不做"必然正确"的承诺，UI 与报告都
要求使用者核对 a 值与点阵类型。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from crysize.core.peaks import d_spacing

#: 内置物相弹性常数（GPa，室温）。数值仅供快速起算，正式报告应替换为
#: 该批样品实测或被引用文献的值 —— 弹性常数随成分、致密度、温度明显变化。
PRESETS: dict[str, "ElasticParams"] = {}


@dataclass
class ElasticParams:
    """立方物相的晶格参数与弹性刚度常数。"""

    a: float = 0.0            # 晶格参数 Å
    c11: float = 0.0          # GPa
    c12: float = 0.0          # GPa
    c44: float = 0.0          # GPa
    lattice: str = "fcc"      # fcc | bcc | simple
    label: str = ""

    @property
    def usable(self) -> bool:
        """弹性数据是否可用于 USDM/UDEDM。"""
        return (self.a > 0.1 and self.c11 > 0 and self.c44 > 0
                and (self.c11 - self.c12) > 1e-6)

    @property
    def anisotropy_factor(self) -> float:
        """Zener 各向异性因子 A = 2c44/(c11 − c12)。A = 1 为弹性各向同性。"""
        den = self.c11 - self.c12
        return float(2.0 * self.c44 / den) if abs(den) > 1e-9 else float("nan")

    def compliances(self) -> tuple[float, float, float]:
        """(S11, S12, S44)，单位 1/GPa。"""
        den = (self.c11 - self.c12) * (self.c11 + 2.0 * self.c12)
        if abs(den) < 1e-12:
            return float("nan"), float("nan"), float("nan")
        return (self.c11 + self.c12) / den, -self.c12 / den, 1.0 / self.c44

    def gamma(self, h: int, k: int, l: int) -> float:
        h2, k2, l2 = float(h * h), float(k * k), float(l * l)
        n = h2 + k2 + l2
        if n <= 0:
            return 0.0
        return (h2 * k2 + k2 * l2 + l2 * h2) / (n * n)

    def youngs(self, h: int, k: int, l: int) -> float:
        """沿 [hkl] 方向的杨氏模量 E(hkl)，GPa。"""
        if not self.usable:
            return float("nan")
        s11, s12, s44 = self.compliances()
        inv = s11 - 2.0 * (s11 - s12 - 0.5 * s44) * self.gamma(h, k, l)
        return float(1.0 / inv) if inv > 1e-12 else float("nan")

    def youngs_mean(self, max_index: int = 4) -> float:
        """所有等价方向的算术平均 E（GPa），作为各向同性退化时的代表值。"""
        vals = [self.youngs(h, k, l)
                for h in range(max_index + 1)
                for k in range(h + 1)
                for l in range(k + 1)
                if h + k + l > 0]
        vals = [v for v in vals if np.isfinite(v)]
        return float(np.mean(vals)) if vals else float("nan")


PRESETS = {
    "Si": ElasticParams(a=5.431194, c11=165.7, c12=63.9, c44=79.6,
                        lattice="fcc", label="Si"),
    "CeO2": ElasticParams(a=5.4113, c11=403.0, c12=105.0, c44=60.0,
                          lattice="fcc", label="CeO₂"),
    "NaCl": ElasticParams(a=5.6402, c11=48.5, c12=12.4, c44=12.6,
                          lattice="fcc", label="NaCl"),
}


def _allowed(h: int, k: int, l: int, lattice: str) -> bool:
    if lattice == "fcc":
        return (h % 2 == k % 2 == l % 2)
    if lattice == "bcc":
        return (h + k + l) % 2 == 0
    return True


def index_cubic(
    two_theta: float,
    wavelength: float,
    a: float,
    lattice: str = "fcc",
    max_index: int = 8,
    tol: float = 0.03,
) -> list[tuple[int, int, int]]:
    """把单个峰位指标化为可能的 (hkl)（h ≥ k ≥ l ≥ 0）。

    ``tol`` 为 N = h²+k²+l² 的相对容差。返回按 N 偏差升序排列的候选，
    空列表表示无法指标化（a 值不符、非该点阵、或峰位误差过大）。
    """
    if a <= 0.1:
        return []
    d = d_spacing(two_theta, wavelength)
    if not np.isfinite(d) or d <= 0.05:
        return []
    n_target = (a / d) ** 2
    out: list[tuple[float, tuple[int, int, int]]] = []
    for h in range(max_index + 1):
        for k in range(h + 1):
            for l in range(k + 1):
                if h + k + l == 0:
                    continue
                n = h * h + k * k + l * l
                if abs(n - n_target) > tol * max(n_target, 1.0):
                    continue
                if not _allowed(h, k, l, lattice):
                    continue
                out.append((abs(n - n_target) / max(n_target, 1.0), (h, k, l)))
    out.sort(key=lambda t: t[0])
    return [idx for _dev, idx in out]


def hkl_str(hkl: tuple[int, int, int] | None) -> str:
    if not hkl:
        return "—"
    return "".join(str(v) for v in hkl)


def index_peaks(
    two_theta_list: list[float],
    wavelength: float,
    params: ElasticParams | None,
) -> list[tuple[int, int, int] | None]:
    """批量指标化，取每个峰的最佳候选（无解为 None）。"""
    if params is None or not params.usable:
        return [None] * len(two_theta_list)
    out = []
    for tt in two_theta_list:
        cand = index_cubic(tt, wavelength, params.a, params.lattice)
        out.append(cand[0] if cand else None)
    return out
