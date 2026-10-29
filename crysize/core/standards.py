"""标准物质参考数据与 2θ 零位偏移估计。

内置两种线宽标样的晶体学数据（晶格常数取自 IUCr / NIST 证书）：

* **Si**（NIST SRM 640f）：``a = 5.431194 Å``，Fd-3m，金刚石型
* **LaB₆**（NIST SRM 660c）：``a = 4.156826 Å``，Pm-3m

用途有两个：
1. 给出理论峰位，用于**峰位偏移诊断**；
2. 由标样实测峰位与理论峰位的偏差估计仪器 **2θ 零位偏移**。

关于零位偏移的边界
------------------
严格地，平板样品的角度误差含两部分：常数零位偏移 Δ0 与样品位移项
``Δ2θ = -2s·cosθ/R``（Wilson 等，J. Sci. Instrum. 27 (1950)）。两者都随
2θ 变化的部分需要多峰才能分离。本程序只估**常数零偏**（取各峰偏差的中位
数），因为：一是稳健、不会被个别误匹配峰带偏；二是它已能消除报告里 d 值
系统性偏离 PDF 卡片的问题。样品位移项在报告中列为未校正项。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from crysize.i18n import tr


@dataclass(frozen=True)
class StandardRef:
    """标样参考：晶格常数与主要反射 (hkl, 相对强度)。"""

    name: str
    a: float
    space_group: str
    reflections: tuple[tuple[int, int, int, float], ...]
    note: str = ""

    def d_of(self, hkl: tuple[int, int, int]) -> float:
        h, k, l = hkl
        return self.a / np.sqrt(h * h + k * k + l * l)

    def two_theta(self, hkl: tuple[int, int, int], wavelength: float) -> float:
        d = self.d_of(hkl)
        s = wavelength / (2.0 * d)
        if s >= 1.0:
            return float("nan")
        return float(np.degrees(2.0 * np.arcsin(s)))

    def peak_list(self, wavelength: float) -> list[tuple[float, tuple[int, int, int], float]]:
        """在给定波长下的峰位表：(2θ, hkl, 相对强度)。"""
        out = []
        for h, k, l, inten in self.reflections:
            tt = self.two_theta((h, k, l), wavelength)
            if np.isfinite(tt):
                out.append((tt, (h, k, l), inten))
        return sorted(out)


#: Si SRM 640f —— 金刚石结构，Fd-3m，唯象允许的反射为全奇或全偶
SI = StandardRef(
    name="Si", a=5.431194, space_group="Fd-3m",
    reflections=(
        (1, 1, 1, 100.0), (2, 2, 0, 55.0), (3, 1, 1, 30.0), (4, 0, 0, 6.0),
        (3, 3, 1, 11.0), (4, 2, 2, 9.0), (5, 1, 1, 8.0), (3, 3, 3, 3.0),
        (4, 4, 0, 3.0), (5, 3, 1, 5.0), (4, 4, 2, 2.0), (6, 2, 0, 4.0),
        (5, 3, 3, 3.0), (6, 2, 2, 2.0), (4, 4, 4, 1.0),
    ),
    note="NIST SRM 640f",
)

#: LaB₆ SRM 660c —— 立方钙钛矿型，Pm-3m，全 hkl 允许
LAB6 = StandardRef(
    name="LaB6", a=4.156826, space_group="Pm-3m",
    reflections=(
        (1, 0, 0, 8.0), (1, 1, 0, 100.0), (1, 1, 1, 52.0), (2, 0, 0, 41.0),
        (2, 1, 0, 25.0), (2, 1, 1, 33.0), (2, 2, 0, 18.0), (3, 0, 0, 13.0),
        (3, 1, 0, 16.0), (3, 1, 1, 12.0), (2, 2, 2, 8.0), (3, 2, 0, 9.0),
        (3, 2, 1, 11.0), (4, 0, 0, 6.0), (4, 1, 0, 5.0),
    ),
    note="NIST SRM 660c",
)

STANDARDS: dict[str, StandardRef] = {"Si": SI, "LaB6": LAB6}

#: 匹配容差（度）：超过此偏差不认为是同一反射
MATCH_TOL = 1.2


@dataclass
class AngleCorrection:
    """2θ 角度校正：``2θ_corr = 2θ_obs + Δ0 + k·cosθ``。

    Δ0 为测角仪零位偏移；k·cosθ 项对应平板样品表面偏离测角圆心的位移
    （``k = -2s/R``，s 为样品位移、R 为测角仪半径）。两者都由标样峰位
    拟合得到，残差即角度系统的自洽性指标。
    """

    delta0: float = 0.0
    k: float = 0.0
    applied: bool = False
    method: str = "none"          # none | zero | zero+displacement
    rms: float = 0.0
    note: str = ""
    standard: StandardRef | None = None
    matched: list = None

    def __post_init__(self):
        if self.matched is None:
            self.matched = []

    def at(self, two_theta) -> np.ndarray:
        tt = np.asarray(two_theta, dtype=float)
        return self.delta0 + self.k * np.cos(np.radians(tt / 2.0))

    def apply(self, two_theta):
        tt = np.asarray(two_theta, dtype=float)
        return tt + self.at(tt)

    @property
    def shift_at_zero(self) -> float:
        """2θ→0 时的等效偏移（供报告标注"零位偏移"）。"""
        return self.delta0 + self.k

    def sample_displacement_mm(self, goniometer_radius_mm: float = 250.0) -> float:
        """按 Δ2θ = -2s·cosθ/R 反算等效样品位移（经验换算，仅供参考）。"""
        return -self.k * goniometer_radius_mm / 2.0

    def describe(self) -> str:
        if not self.applied:
            return self.note or tr("corr.not_applied")
        if self.method == "zero+displacement":
            return tr("corr.desc.zero_disp", d0=self.delta0, k=self.k, rms=self.rms)
        return tr("corr.desc.zero", v=self.delta0)


def identify_standard(
    observed: list[float], wavelength: float, candidates: dict[str, StandardRef] | None = None
) -> tuple[StandardRef | None, list[tuple[float, float, tuple[int, int, int], float]]]:
    """按峰位匹配判断标样种类，返回 (标样, 匹配列表)。

    匹配列表元素为 ``(观测 2θ, 理论−观测, hkl, 相对强度)``；同一反射只保留
    偏差最小的那一次，避免 Kα2 肩或噪声被重复计数。
    """
    refs = candidates or STANDARDS
    best_ref, best_pairs = None, []
    for ref in refs.values():
        plist = ref.peak_list(wavelength)
        if not plist:
            continue
        seen: dict[tuple[int, int, int], tuple[float, float, tuple[int, int, int], float]] = {}
        for pos in observed:
            diffs = [abs(tt - pos) for tt, _h, _i in plist]
            j = int(np.argmin(diffs))
            if diffs[j] <= MATCH_TOL:
                tt, hkl, inten = plist[j]
                cand = (pos, tt - pos, hkl, inten)
                if hkl not in seen or abs(cand[1]) < abs(seen[hkl][1]):
                    seen[hkl] = cand
        uniq = list(seen.values())
        if len(uniq) > len(best_pairs):
            best_ref, best_pairs = ref, uniq
    if best_ref is None or len(best_pairs) < 3:
        return None, []
    return best_ref, best_pairs


def estimate_angle_correction(
    observed: list[float],
    wavelength: float,
    candidates: dict[str, StandardRef] | None = None,
    *,
    min_peaks_two_param: int = 5,
    min_span_two_param: float = 40.0,
    zero_residual_tol: float = 0.008,
) -> AngleCorrection:
    """由标样峰位估计角度校正参数。

    先用常数零偏（中位数）试拟合：若残差已足够小（默认 < 0.008°），说明数据
    只需常数校正，直接采用单参数模型。

    否则再拟合 ``Δ = Δ0 + k·cosθ`` 两参数。注意这两项在有限 2θ 范围内高度
    相关（cosθ 变化范围小），参数分解本质上是病态的：因此只在两参数确实把
    残差降低 40% 以上、且 k 的量级合理时才接受，避免把纯零偏数据拟合成
    虚假的"样品位移"。这也是本程序不把 k 解释为真实样品位移（毫米）的原因。
    """
    ref, pairs = identify_standard(observed, wavelength, candidates)
    if ref is None:
        return AngleCorrection(note=tr("corr.no_match"))

    tt = np.array([p[0] for p in pairs], dtype=float)
    delta = np.array([p[1] for p in pairs], dtype=float)
    span = float(np.ptp(tt)) if tt.size else 0.0
    corr = AngleCorrection(standard=ref, matched=pairs, applied=True)

    shift = float(np.median(delta))
    res_zero = float(np.sqrt(np.mean((delta - shift) ** 2)))

    if tt.size >= min_peaks_two_param and span >= min_span_two_param \
            and res_zero > zero_residual_tol:
        A = np.column_stack([np.ones_like(tt), np.cos(np.radians(tt / 2.0))])
        coef, *_ = np.linalg.lstsq(A, delta, rcond=None)
        resid = delta - A @ coef
        rms2 = float(np.sqrt(np.mean(resid**2)))
        if rms2 < 0.6 * res_zero and abs(coef[1]) < 0.6:
            corr.delta0, corr.k = float(coef[0]), float(coef[1])
            corr.rms = rms2
            corr.method = "zero+displacement"
            corr.note = tr("corr.match2", name=ref.name, a=ref.a,
                           n=len(pairs), rms=rms2)
            return corr

    corr.delta0, corr.k = shift, 0.0
    corr.rms = res_zero
    corr.method = "zero"
    corr.note = tr("corr.match1", name=ref.name, n=len(pairs),
                   rms=res_zero, shift=shift)
    return corr


#: 兼容旧名
def estimate_zero_shift(observed, wavelength, candidates=None) -> AngleCorrection:
    return estimate_angle_correction(observed, wavelength, candidates)
