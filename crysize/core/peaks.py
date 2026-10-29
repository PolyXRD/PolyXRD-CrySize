"""衍射峰搜索与自动选峰。

自动选峰的目标不是「找出所有峰」，而是**挑出适合宽度分析的孤立峰**：
重叠峰会让单峰拟合得到偏大的 FWHM（假宽化），Kα2 卫星峰会被误认为独立
反射。因此按 prominence（相对本底的突出度）初筛、按最小间隔去重，再按
强度排序给出候选，最终由用户确认。

同时给出每个峰的半高宽粗估（``fwhm_est``），供拟合层决定自适应窗口宽度：
窗口必须能容下 3–4 倍 FWHM，否则峰尾被截断、η 撞边界、宽度失真。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks, peak_widths, savgol_filter

from crysize.core.pattern import Pattern


@dataclass
class PeakCandidate:
    """候选峰（未精修，仅几何信息）。"""

    two_theta: float
    intensity: float
    prominence: float     # 相对局部本底的突出度（计数）
    rel_intensity: float  # 相对最强峰的百分强度
    fwhm_est: float = 0.1  # 半高宽粗估（度）

    def label(self) -> str:
        return f"{self.two_theta:.3f}°"


def _smooth(y: np.ndarray, step: float) -> np.ndarray:
    """Savitzky-Golay 平滑（窗口约 4° / 40 点，奇数）。"""
    n = y.size
    win = int(max(5, round(0.04 / max(step, 1e-6)) | 1))
    win = min(win, n - 1 if n % 2 == 0 else n - 2)
    if win % 2 == 0:
        win -= 1
    if win < 5 or win >= n:
        return y
    try:
        return savgol_filter(y, win, 2)
    except Exception:
        return y


def find_candidates(
    pattern: Pattern,
    *,
    min_prominence_frac: float = 0.03,
    min_sep_deg: float = 0.6,
    two_theta_range: tuple[float, float] | None = None,
) -> list[PeakCandidate]:
    """返回按突出度降序排列的候选峰。"""
    x, y = pattern.two_theta, pattern.intensity
    if two_theta_range:
        m = pattern.mask(*two_theta_range)
        x, y = x[m], y[m]
    if x.size < 20:
        return []

    ys = _smooth(y, pattern.step)
    imax = float(np.max(ys))
    if imax <= 0:
        return []
    prom = max(imax * min_prominence_frac, 3.0 * float(np.sqrt(max(np.median(y), 1))))
    dist = max(1, int(round(min_sep_deg / max(pattern.step, 1e-6))))

    idx, props = find_peaks(ys, prominence=prom, distance=dist)
    if idx.size == 0:
        return []

    # 半高宽粗估（以采样点为单位，需乘步长）
    widths = np.zeros(idx.size)
    try:
        wres = peak_widths(ys, idx, rel_height=0.5)[0]
        widths = np.asarray(wres, dtype=float) * pattern.step
    except Exception:
        widths = np.full(idx.size, max(pattern.step * 4, 0.1))

    base = float(np.percentile(y, 5))
    out = [
        PeakCandidate(
            two_theta=float(x[i]),
            intensity=float(y[i]),
            prominence=float(props["prominences"][k]),
            rel_intensity=float(100.0 * (y[i] - base) / max(imax - base, 1e-9)),
            fwhm_est=float(max(widths[k], pattern.step * 2)),
        )
        for k, i in enumerate(idx)
    ]
    out.sort(key=lambda p: p.prominence, reverse=True)
    return out


def auto_select(
    candidates: list[PeakCandidate],
    count: int = 5,
    *,
    min_angle: float | None = None,
    max_angle: float | None = None,
) -> list[PeakCandidate]:
    """按突出度取前 ``count`` 个（受 2θ 范围约束），返回按角度升序。"""
    pool = [c for c in candidates
            if (min_angle is None or c.two_theta >= min_angle)
            and (max_angle is None or c.two_theta <= max_angle)]
    picked = pool[: max(count, 1)]
    return sorted(picked, key=lambda p: p.two_theta)


def d_spacing(two_theta: float, wavelength: float) -> float:
    """Bragg 方程：d = λ / (2 sinθ)，单位 Å。"""
    s = np.sin(np.radians(two_theta / 2.0))
    return float(wavelength / (2.0 * s)) if s > 1e-9 else float("nan")
