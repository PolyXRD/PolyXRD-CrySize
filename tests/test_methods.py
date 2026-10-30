"""v2.0.0 新增方法（弹性/指标化、W-H 三变体、Warren-Averbach）的测试。

原则与 test_core.py 一致：**闭环验证** —— 能解析手算的先对解析值，
能正演的先正演再反演；只有"能不能出数"才用冒烟式断言。

运行：``python -m unittest discover -s tests -v``
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crysize.core.elasticity import PRESETS, ElasticParams, index_cubic  # noqa: E402
from crysize.core.methods import METHOD_IDS, evaluate_all  # noqa: E402
from crysize.core.pattern import KA1, Pattern  # noqa: E402
from crysize.core.profile import fwhm_from_integral, pseudo_voigt  # noqa: E402
from crysize.core.size import compute_scherrer  # noqa: E402
from crysize.core.warren import compute_wa_fourier, compute_wa_single  # noqa: E402
from crysize.core.wh_models import compute_wh_variant  # noqa: E402

LAM = KA1["Cu"]
DEG2RAD = np.pi / 180.0


class TestElasticity(unittest.TestCase):
    """E(hkl) 与指标化 —— 对可手算的解析值。"""

    def test_si_youngs_analytic(self) -> None:
        """Si 的 E(100)/E(110)/E(111) 对柔度公式的手算值。

        S11 = (c11+c12)/[(c11−c12)(c11+2c12)] = 7.6846e-3 /GPa → E(100) = 130.1 GPa
        Γ(110) = 1/4 → E(110) = 169.1 GPa；Γ(111) = 1/3 → E(111) = 187.9 GPa
        """
        si = PRESETS["Si"]
        s11, s12, s44 = si.compliances()
        self.assertAlmostEqual(s11, 7.6846e-3, places=6)
        self.assertAlmostEqual(s12, -2.1387e-3, places=6)
        self.assertAlmostEqual(s44, 1.0 / 79.6, places=6)
        self.assertAlmostEqual(si.youngs(1, 0, 0), 130.1, delta=0.3)
        self.assertAlmostEqual(si.youngs(1, 1, 0), 169.1, delta=0.3)
        self.assertAlmostEqual(si.youngs(1, 1, 1), 187.9, delta=0.3)
        # 各向异性：Si 的 A = 2c44/(c11−c12) ≈ 1.56 > 1，故 E(111) > E(100)
        self.assertGreater(si.youngs(1, 1, 1), si.youngs(1, 0, 0))
        self.assertAlmostEqual(si.anisotropy_factor, 2 * 79.6 / (165.7 - 63.9), places=3)

    def test_gamma_bounds(self) -> None:
        """Γ ∈ [0, 1/3]：0 对应 [100]，1/3 对应 [111]。"""
        si = PRESETS["Si"]
        self.assertAlmostEqual(si.gamma(1, 0, 0), 0.0)
        self.assertAlmostEqual(si.gamma(1, 1, 0), 0.25)
        self.assertAlmostEqual(si.gamma(1, 1, 1), 1.0 / 3.0)
        self.assertAlmostEqual(si.gamma(2, 0, 0), 0.0)   # 与 [100] 同向

    def test_index_si_111(self) -> None:
        """Si(111) 的 2θ = 28.442° 应指标化为 (1,1,1)。"""
        tt = 2 * np.degrees(np.arcsin(LAM / (2 * (PRESETS["Si"].a / np.sqrt(3)))))
        self.assertAlmostEqual(tt, 28.442, delta=0.01)
        cand = index_cubic(tt, LAM, PRESETS["Si"].a, "fcc")
        self.assertEqual(cand[0], (1, 1, 1))

    def test_fcc_extinction(self) -> None:
        """fcc 消光：(211) 奇偶混合被禁阻，simple 点阵允许。

        取 N = h²+k²+l² = 6 —— 7 无法表示为三个平方数之和（Legendre），
        不能用来做这条断言。
        """
        a = PRESETS["Si"].a
        d = a / np.sqrt(6.0)
        tt = 2 * np.degrees(np.arcsin(LAM / (2 * d)))
        self.assertEqual(index_cubic(tt, LAM, a, "fcc"), [])
        self.assertIn((2, 1, 1), index_cubic(tt, LAM, a, "simple"))

    def test_unusable_without_data(self) -> None:
        self.assertFalse(ElasticParams().usable)
        self.assertTrue(PRESETS["CeO2"].usable)


class TestWHVariants(unittest.TestCase):
    """三变体：退化一致性 + 闭环反演。"""

    @staticmethod
    def _synth_fits(d_nm: float, strain: float, positions: list[float],
                    eta: float = 0.5) -> list:
        """按 W-H 关系正演：β = Kλ/(D cosθ) + 4ε tanθ（积分宽度口径，K=1）。

        注意：``fit_region`` 在**传入数组**的全范围上拟合，窗口要由调用方
        先切片（与 ``analysis.fit_targets`` 一致），否则会把整条谱当一个窗口。
        """
        from crysize.core.profile import fit_region
        lo, hi = min(positions) - 8, max(positions) + 8
        grid = np.arange(lo, hi + 0.005, 0.01)
        y = np.full_like(grid, 50.0)
        fwhms: dict[float, float] = {}
        for c in positions:
            theta = c / 2.0 * DEG2RAD
            beta = LAM / (d_nm * 10.0 * np.cos(theta)) + 4 * strain * np.tan(theta)
            fwhms[c] = fwhm_from_integral(beta / DEG2RAD, eta)
            y = y + 4000.0 * pseudo_voigt(grid, c, fwhms[c], eta)
        pat = Pattern(grid, y, label="synth", wavelength=LAM)
        fits = []
        for c in positions:
            win = float(np.clip(3.2 * max(fwhms[c], 0.05), 0.8, 3.0))
            m = pat.mask(c - win, c + win)
            fits.append(fit_region(pat.two_theta[m], pat.intensity[m], [c], window=win,
                                   wavelength=LAM, anode="Cu", strip_ka2=False,
                                   target=c, fwhm_guess={c: fwhms[c]}))
        return fits

    def test_degenerate_identical_without_elastic(self) -> None:
        """无弹性常数时，三变体必须给出完全相同的 D 与 R²（只是重参数化）。"""
        positions = [30.0, 42.0, 52.0, 61.0, 69.0]
        fits = self._synth_fits(25.0, 0.004, positions)
        res = {}
        for model in ("udm", "usdm", "udedm"):
            res[model] = compute_wh_variant(fits, wavelength=LAM, model=model)
        self.assertAlmostEqual(res["udm"].size_nm, res["usdm"].size_nm, places=9)
        self.assertAlmostEqual(res["udm"].size_nm, res["udedm"].size_nm, places=9)
        self.assertAlmostEqual(res["udm"].r2, res["udedm"].r2, places=9)
        for model in ("usdm", "udedm"):
            self.assertTrue(res[model].degenerate)

    def test_udm_recovers_truth(self) -> None:
        """闭环：正演 D=25 nm、ε=0.4%，UDM 反演应在 3% 内还原。"""
        positions = [30.0, 42.0, 52.0, 61.0, 69.0]
        fits = self._synth_fits(25.0, 0.004, positions)
        r = compute_wh_variant(fits, wavelength=LAM, model="udm")
        self.assertAlmostEqual(r.size_nm, 25.0, delta=25.0 * 0.03)
        self.assertAlmostEqual(r.strain_pct, 0.4, delta=0.4 * 0.05)

    @staticmethod
    def _si_positions() -> list[float]:
        """Si（fcc, a=5.431194）的 111/220/311/400/331 峰位（Cu Kα1）。"""
        a = PRESETS["Si"].a
        out = []
        for n in (3, 8, 11, 16, 19):
            s = LAM / (2 * (a / np.sqrt(n)))
            out.append(float(np.degrees(2 * np.arcsin(s))))
        return sorted(out)

    def test_usdm_uses_E_hkl(self) -> None:
        """给了弹性常数 + 真实立方峰位后，USDM 的横轴随 E(hkl) 变化。"""
        positions = self._si_positions()
        self.assertAlmostEqual(positions[0], 28.442, delta=0.01)
        fits = self._synth_fits(25.0, 0.004, positions)
        el = ElasticParams(a=5.431194, c11=165.7, c12=63.9, c44=79.6, lattice="fcc")
        udm = compute_wh_variant(fits, wavelength=LAM, model="udm", elastic=el)
        usdm = compute_wh_variant(fits, wavelength=LAM, model="usdm", elastic=el)
        self.assertFalse(usdm.degenerate)
        self.assertNotAlmostEqual(udm.r2, usdm.r2, places=3)
        self.assertGreater(usdm.stress_mpa, 0)

    def test_grouping_falls_back_without_higher_orders(self) -> None:
        """没有同族高级次时，分组必须退回整体回归而不是出空结果。"""
        positions = [30.0, 42.0, 52.0, 61.0, 69.0]
        fits = self._synth_fits(25.0, 0.004, positions)
        el = ElasticParams(a=5.431194, c11=165.7, c12=63.9, c44=79.6, lattice="fcc")
        r = compute_wh_variant(fits, wavelength=LAM, model="udm", elastic=el,
                               group_by_direction=True)
        self.assertTrue(np.isfinite(r.size_nm), f"warnings={r.warnings}")
        # 合成峰不是立方晶系真实峰位，指标化可能失败；无论回退还是分组，
        # 都必须给出有限尺寸，不能返回空结果
        self.assertGreater(r.n, 1)


class TestWarrenAverbach(unittest.TestCase):
    """Warren-Averbach：单峰近似与多级傅里叶法。"""

    @staticmethod
    def _multi_order_pattern(a: float = 4.05, d_nm: float = 15.0,
                             strain: float = 0.003) -> tuple[Pattern, list[float]]:
        """立方 a=4.05 的 111/200/220/311/222/400 六峰（含多级反射对）。"""
        positions = []
        for n in (3, 4, 8, 11, 12, 16):
            d = a / np.sqrt(n)
            s = LAM / (2 * d)
            if s >= 1:
                continue
            positions.append(2 * np.degrees(np.arcsin(s)))
        positions = sorted(positions)
        grid = np.arange(20.0, 130.0, 0.01)
        y = np.full_like(grid, 40.0)
        for c in positions:
            theta = c / 2.0 * DEG2RAD
            beta = LAM / (d_nm * 10.0 * np.cos(theta)) + 4 * strain * np.tan(theta)
            fwhm = fwhm_from_integral(beta / DEG2RAD, 0.5)
            y = y + 3000.0 * pseudo_voigt(grid, c, fwhm, 0.5)
        return Pattern(grid, y, label="multi", wavelength=LAM), positions

    @staticmethod
    def _fits(pat: Pattern, positions: list[float], eta: float = 0.5) -> list:
        from crysize.core.profile import fit_region
        fits = []
        for c in positions:
            win = 1.8
            m = pat.mask(c - win, c + win)
            fits.append(fit_region(pat.two_theta[m], pat.intensity[m], [c], window=win,
                                   wavelength=LAM, anode="Cu", strip_ka2=False,
                                   target=c, fwhm_guess={c: 0.4}))
        return fits

    def test_single_line_gives_finite_size(self) -> None:
        pat, positions = self._multi_order_pattern()
        fits = self._fits(pat, positions)
        r = compute_wa_single(fits, wavelength=LAM)
        self.assertGreater(r.n_valid, 0)
        self.assertTrue(np.isfinite(r.size_nm))
        # 单峰法与谢乐法同量级（都在 5–40 nm）
        sch = compute_scherrer(fits, wavelength=LAM, width_mode="integral", K=1.0)
        self.assertTrue(0.3 < r.size_nm / sch.mean_number < 3.0,
                        f"wa_single={r.size_nm:.2f} vs scherrer={sch.mean_number:.2f}")

    def test_fourier_runs_with_higher_orders(self) -> None:
        pat, positions = self._multi_order_pattern()
        fits = self._fits(pat, positions)
        r = compute_wa_fourier(fits, wavelength=LAM)
        self.assertEqual(len(r.peaks), len(fits))
        self.assertTrue(np.isfinite(r.size_nm), f"warnings={r.warnings}")
        self.assertTrue(0.5 < r.size_nm < 200.0, f"D_v={r.size_nm:.2f} nm 超出合理区间")
        self.assertGreater(r.L.size, 3)

    def test_fourier_rejects_single_d(self) -> None:
        """d 值只有一种时（无多级/多族），傅里叶法必须拒算。"""
        pat, positions = self._multi_order_pattern()
        fits = self._fits(pat, [positions[0]]) * 3      # 同一个峰重复三次
        r = compute_wa_fourier(fits, wavelength=LAM)
        self.assertFalse(np.isfinite(r.size_nm))
        self.assertTrue(bool(r.warnings))


class TestMethodRegistry(unittest.TestCase):
    """注册表自身：5 组 7 种，且一次评估全部出结果。"""

    def test_groups_and_counts(self) -> None:
        self.assertEqual(len(METHOD_IDS), 7)
        from crysize.core.methods import GROUPS
        self.assertEqual(len(GROUPS), 5)
        self.assertEqual(sum(len(m) for _g, m in GROUPS), 7)

    def test_evaluate_all(self) -> None:
        pat, positions = TestWarrenAverbach._multi_order_pattern()
        fits = TestWarrenAverbach._fits(pat, positions)
        out = evaluate_all(fits, wavelength=LAM,
                           elastic=PRESETS["Si"], group_by_direction=False)
        self.assertEqual(len(out), 7)
        for mid in METHOD_IDS:
            self.assertIn(mid, out)
            self.assertIsNotNone(out[mid].detail)
        # 谢乐两种口径都必须出数
        self.assertTrue(np.isfinite(out["scherrer_fwhm"].size_nm))
        self.assertTrue(np.isfinite(out["scherrer_integral"].size_nm))


def tr_(key: str) -> str:
    from crysize.i18n import tr
    return tr(key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
