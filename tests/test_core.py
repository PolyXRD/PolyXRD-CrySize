"""核心算法测试。

重点不是"跑通"，而是**闭环验证**：用谢乐方程正演生成已知晶粒尺寸的合成谱，
再让程序反演，检查能否还原真值。这是判断数学实现是否正确的唯一可靠方法
（真实样品没有真值可对）。

运行：``python -m unittest discover -s tests -v``
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crysize.core.analysis import AnalysisConfig, run_analysis  # noqa: E402
from crysize.core.instrument import build_instrument_model  # noqa: E402
from crysize.core.pattern import KA1, Pattern  # noqa: E402
from crysize.core.profile import (fwhm_from_integral, integral_width,  # noqa: E402
                                 pseudo_voigt)
from crysize.core.standards import SI, estimate_angle_correction  # noqa: E402

LAM = KA1["Cu"]
DEG2RAD = np.pi / 180.0


def synth(
    positions: list[float],
    fwhm_deg: list[float],
    amps: list[float],
    *,
    lo: float = 20.0,
    hi: float = 90.0,
    step: float = 0.01,
    bg: float = 80.0,
    eta: float = 0.6,
    noise: float = 0.0,
    seed: int = 0,
) -> Pattern:
    """按给定峰位/半高宽/峰高生成合成谱（pseudo-Voigt + 常数背景）。"""
    x = np.arange(lo, hi + step / 2, step)
    y = np.full_like(x, bg)
    for c, f, a in zip(positions, fwhm_deg, amps):
        y = y + a * pseudo_voigt(x, c, f, eta)
    if noise > 0:
        rng = np.random.default_rng(seed)
        y = rng.poisson(np.maximum(y, 1.0)).astype(float)
    return Pattern(x, y, label="synthetic", wavelength=LAM)


def size_fwhm_deg(d_nm: float, two_theta: float, k: float = 0.89) -> float:
    """由晶粒尺寸正演 FWHM（度）—— 谢乐方程的逆用。"""
    theta = two_theta / 2.0 * DEG2RAD
    beta_rad = k * LAM / (d_nm * 10.0 * np.cos(theta))
    return beta_rad / DEG2RAD


def strain_fwhm_deg(strain: float, two_theta: float) -> float:
    """由微应变正演 FWHM（度）：β = 4ε tanθ。"""
    theta = two_theta / 2.0 * DEG2RAD
    return 4.0 * strain * np.tan(theta) / DEG2RAD


#: 合成标样/样品的峰位（取 Si 的低角反射，峰间距足够）
PEAKS = [28.4426, 47.3024, 56.1213, 69.1301, 76.3767, 88.0325]
AMPS = [3000.0, 1400.0, 900.0, 400.0, 520.0, 380.0]
INST_FWHM = 0.10


class TestPatternIO(unittest.TestCase):
    def test_read_shimadzu_header(self):
        p = Path("D:/Project/XRD/XRData/smz geshi/1. Si.txt")
        if not p.exists():
            self.skipTest("示例数据不存在")
        from crysize.core.pattern import read_pattern
        pat = read_pattern(p)
        self.assertEqual(pat.anode, "Cu")
        self.assertEqual(pat.n, 9001)
        self.assertAlmostEqual(pat.step, 0.01, places=4)
        self.assertAlmostEqual(pat.wavelength, 1.540598, places=5)
        self.assertLess(pat.two_theta[0], pat.two_theta[-1])

    def test_descending_flipped(self):
        x = np.linspace(90, 20, 200)
        pat = Pattern(x, np.ones_like(x), wavelength=LAM)
        self.assertLess(pat.two_theta[0], pat.two_theta[-1])


class TestInstrumentModel(unittest.TestCase):
    def test_constant_width_recovered(self):
        # 合成谱不含 Kα₂ 分量，故关闭剥离（真实 Cu 靶数据应保持开启）
        std = synth(PEAKS, [INST_FWHM] * len(PEAKS), AMPS)
        model = build_instrument_model(std, strip_ka2=False)
        self.assertTrue(model.usable)
        self.assertEqual(model.method, "caglioti")
        for tt in (30.0, 50.0, 70.0):
            self.assertAlmostEqual(model.fwhm_at(tt), INST_FWHM, delta=0.012)

    def test_angle_correction_on_si(self):
        """观测峰位整体比理论大 +0.04°，Δ=理论−观测 应为 −0.04°。"""
        shifted = [p + 0.04 for p in PEAKS]
        corr = estimate_angle_correction(shifted, LAM)
        self.assertTrue(corr.applied)
        self.assertAlmostEqual(corr.delta0, -0.04, delta=0.006)
        self.assertEqual(corr.method, "zero")  # 纯零偏不应拟合成假位移项
        self.assertLess(corr.rms, 0.01)


class TestScherrer(unittest.TestCase):
    def _run(self, d_nm: float, strain: float = 0.0):
        std = synth(PEAKS, [INST_FWHM] * len(PEAKS), AMPS)
        fw = [float(np.sqrt(size_fwhm_deg(d_nm, p) ** 2
                           + strain_fwhm_deg(strain, p) ** 2 + INST_FWHM**2))
              for p in PEAKS]
        smp = synth(PEAKS, fw, AMPS, noise=1.0, seed=7)
        cfg = AnalysisConfig(n_peaks=4, width_mode="fwhm", K=0.89, strip_ka2=False)
        return run_analysis(smp, std, cfg)

    def test_recover_20nm(self):
        b = self._run(20.0)
        self.assertTrue(b.corrected)
        self.assertGreaterEqual(b.scherrer.n_valid, 3)
        self.assertAlmostEqual(b.scherrer.mean_number, 20.0, delta=1.5)

    def test_recover_50nm(self):
        b = self._run(50.0)
        self.assertAlmostEqual(b.scherrer.mean_number, 50.0, delta=6.0)

    def test_angular_dependence_of_broadening(self):
        """谢乐宽化 β ∝ 1/cosθ：同一晶粒尺寸下，高角峰的 β 应大于低角峰。"""
        b = self._run(15.0)
        betas = [p.beta_deg for p in b.scherrer.peaks if p.ok]
        self.assertGreater(betas[-1], betas[0])

    def test_no_standard_gives_larger_apparent_size(self):
        """未扣仪器宽化时 β 更大 → 表观尺寸应更小（而非更大）。"""
        b_std = self._run(20.0)
        std = synth(PEAKS, [INST_FWHM] * len(PEAKS), AMPS)
        fw = [float(np.sqrt(size_fwhm_deg(20.0, p) ** 2 + INST_FWHM**2)) for p in PEAKS]
        smp = synth(PEAKS, fw, AMPS, noise=1.0, seed=7)
        b_none = run_analysis(smp, None, AnalysisConfig(n_peaks=4, strip_ka2=False))
        self.assertFalse(b_none.corrected)
        self.assertTrue(b_none.warnings())
        # 不扣仪器 → β 更大 → D 更小
        self.assertLess(b_none.scherrer.mean_number, b_std.scherrer.mean_number)


class TestWilliamsonHall(unittest.TestCase):
    def test_recover_size_and_strain(self):
        """W-H 反演用积分宽度，故正演也按积分宽度加和构造，闭环才自洽。"""
        d_true, eps_true, eta = 30.0, 0.0015, 0.6
        std = synth(PEAKS, [INST_FWHM] * len(PEAKS), AMPS)
        inst_int = integral_width(INST_FWHM, eta)
        fw = []
        for p in PEAKS:
            theta = p / 2.0 * DEG2RAD
            beta_int = (LAM / (d_true * 10.0 * np.cos(theta))
                        + 4.0 * eps_true * np.tan(theta) + inst_int * DEG2RAD)
            fw.append(float(fwhm_from_integral(beta_int / DEG2RAD, eta)))
        smp = synth(PEAKS, fw, AMPS, noise=1.0, seed=3)
        b = run_analysis(smp, std, AnalysisConfig(n_peaks=6, strip_ka2=False))
        wh = b.wh
        self.assertGreaterEqual(wh.n_valid, 4)
        self.assertGreater(wh.r2, 0.9)
        self.assertAlmostEqual(wh.size_nm, d_true, delta=0.2 * d_true)
        self.assertAlmostEqual(wh.strain_pct, eps_true * 100, delta=0.35 * eps_true * 100)


class TestEdgeCases(unittest.TestCase):
    def test_data_too_short(self):
        with self.assertRaises(ValueError):
            Pattern(np.arange(5.0), np.arange(5.0), wavelength=LAM)

    def test_no_peak_raises(self):
        flat = Pattern(np.arange(20, 80, 0.02), np.full(3000, 100.0), wavelength=LAM)
        with self.assertRaises(ValueError):
            run_analysis(flat, None, AnalysisConfig(n_peaks=3))

    def test_integral_width_relation(self):
        for eta in (0.0, 0.5, 1.0):
            beta = integral_width(1.0, eta)
            self.assertGreater(beta, 1.0)
            self.assertLess(beta, 1.6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
