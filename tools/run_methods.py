"""用真实数据（CeO 样品 + Si 标样）跑通 7 种方法，检查数值与可用性。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crysize.core.analysis import AnalysisConfig, run_analysis          # noqa: E402
from crysize.core.elasticity import PRESETS, index_peaks                # noqa: E402
from crysize.core.methods import METHOD_IDS, method_name                # noqa: E402
from crysize.core.pattern import read_pattern                           # noqa: E402

STD = r"D:/Project/XRD/XRData/smz geshi/1. Si.txt"
SMP = r"D:/Project/XRD/XRData/Shimadzu Data/CRYSIZE/CeO/txt/CeO.txt"


def main() -> int:
    std = read_pattern(STD)
    smp = read_pattern(SMP)
    print(f"sample {smp.label} n={smp.n} range={smp.range} wl={smp.wavelength}")
    print(f"standard {std.label} n={std.n} range={std.range}")

    elastic = PRESETS["CeO2"]
    cfg = AnalysisConfig(method="wh_udm", elastic=elastic, group_by_direction=True)
    b = run_analysis(smp, std, cfg)

    print("\n-- 指标化（CeO2, a=%.4f, fcc）---" % elastic.a)
    hkls = index_peaks([f.center for f in b.fits], smp.wavelength, elastic)
    for f, h in zip(b.fits, hkls):
        E = elastic.youngs(*h) if h else float("nan")
        g = elastic.gamma(*h) if h else float("nan")
        print(f"  {f.center:8.3f}°  d={smp.wavelength/(2*__import__('math').sin(__import__('math').radians(f.center/2))):.4f}"
              f"  hkl={h}  E={E:8.1f} GPa  Γ={g:.3f}  A={elastic.anisotropy_factor:.2f}")

    print("\n-- 7 种方法 --")
    for mid in METHOD_IDS:
        o = b.outcomes[mid]
        flag = "OK" if o.available and not o.reason else ("DEG" if o.reason else "NA")
        print(f"  {mid:20s} D={o.size_nm:9.3f} nm  sec={o.secondary:12.4f} "
              f"R2={o.r2:7.4f}  n={o.n_used}  [{flag}] {o.reason}")

    act = b.active()
    print(f"\nactive={b.active_method} -> D={act.size_nm:.3f} nm")
    if act.detail is not None and getattr(act.detail, "groups", None):
        for g in act.detail.groups:
            print(f"   group Γ={g.gamma:.3f} {g.group_label}: "
                  f"D={g.size_nm:.3f} nm, ε={g.strain_pct:.4f}%, n={g.n}")
    print("\nwarnings:", b.warnings())
    return 0


if __name__ == "__main__":
    sys.exit(main())
