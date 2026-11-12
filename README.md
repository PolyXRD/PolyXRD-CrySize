# PolyXRD CrySize

A **crystallite size** and **microstrain** analysis tool for XRD powder diffraction patterns. Import the sample pattern and the
line-width standard (Si / LaB₆) pattern measured under the same conditions; the program automatically identifies diffraction peaks, performs peak-shape fitting, subtracts instrumental broadening,
then uses the **Scherrer equation** and the **Williamson-Hall method** to give the crystallite size.

Two tabs correspond to two methods:

| Tab | Method | Output |
|---|---|---|
| ① Scherrer method | D = K·λ/(β·cosθ), peak-by-peak calculation | Per-peak D, average D (three statistical conventions) |
| ② Williamson-Hall | Switchable among the UDM / USDM / UDEDM three variants | Intercept → D, slope → ε/σ/√u, R² |
| ③ Standard & instrumental line width | Caglioti resolution function | U/V/W, instrumental line-width curve, 2θ angle correction |
| ④ Method comparison | Side-by-side comparison of 5 groups / 7 methods | Per-method D, secondary quantity, R², status and selection notes |

## Running

```bash
python run.py                                  # empty UI, import manually
python run.py sample.txt standard.txt           # launch directly with files
python -m crysize.gui
```

Dependencies: Python ≥ 3.10, numpy, scipy, matplotlib, PySide6 (versions pinned in `requirements.txt`).

The UI and reports are **trilingual** (Simplified Chinese / English / Japanese); the "Language" menu switches at runtime,
and the choice is persisted to `%USERPROFILE%/.crysize/config.json`. Missing translation keys are shown directly in the UI as `⟪key⟫`;
`tests/test_i18n.py` catches mismatches between the trilingual key sets and format placeholders before release.

## Calculation methods: 5 groups / 7 methods

The "Calculation method" drop-down in the sidebar switches the main method, and the "Method comparison" tab gives a
side-by-side comparison of the 7 methods on the same set of peak-fitting results. For full selection notes see [`docs/METHODS.md`](docs/METHODS.md).

| Group | Sub-methods (7) | Main output | Secondary quantity | Extra input |
|---|---|---|---|---|
| ① Scherrer method | FWHM convention (K=0.89) / integral-breadth convention (K=1.0) | Number-average D | — | Standard sample (optional) |
| ② W-H UDM | Uniform deformation model | D | ε (%) | Standard sample (recommended) |
| ③ W-H USDM | Uniform stress model | D | σ (MPa) | Standard sample + a, c₁₁/c₁₂/c₄₄ |
| ④ W-H UDEDM | Uniform deformation energy density model | D | u (MJ·m⁻³) | Same as ③ |
| ⑤ Warren-Averbach | Single-peak Voigt approximation / multi-order reflection Fourier method | D (volume-weighted) | ⟨ε²⟩^½ | Standard sample; the Fourier method additionally needs ≥3 peaks and ≥2 d values |

"Group by crystallographic direction" is an enhanced switch shared by ②③④ (regression within groups after grouping by Γ); it requires the lattice
parameters to be filled in first to complete indexing; if the pattern has no higher-order reflections of the same family, the program automatically falls back to no grouping and notes it.

Three usage boundaries:

1. **Without elastic constants, ②③④ collapse to the same fitted line** (σ = εE, u = ε²E/2 are merely re-parameterizations); the UI marks this as "degraded".
2. **Conventions must not be mixed**: the two Scherrer conventions use different K; single-peak W-A and Fourier W-A have different physical meanings; comparing numerical magnitudes across methods is meaningless.
3. **Without a standard sample**, instrumental broadening is folded into the size, so the result is only a relative reference.

## Two editions

| Edition | Artifact | Build command | Edition marker |
|---|---|---|---|
| Internal evaluation build | `dist/PolyXRD-CrySize-vX.Y.Z.exe` (single-file, no installation) | `build_exe.bat` | Status bar + About box marked "Internal Evaluation Build" (overridden at runtime by `installer/rthook_internal.py`) |
| Registered edition | `dist/PolyXRD-CrySize/PolyXRD-CrySize.exe` (onedir) + `dist/PolyXRD-CrySize-vX.Y.Z-Setup.exe` (Inno Setup installer) | `build_setup.bat` | No marker (`crysize/edition.py` defaults to `registered`), but **enables the family-wide registration mechanism** (`crysize/registration.py`) |

The edition only affects marker display and the registration entry point, not any calculation function. The two specs share the same source code and
`resources/`; the only differences are onefile/onedir and whether a runtime hook is added.

### Registration mechanism (registered edition, since v2.0.1)

The registered edition connects to the PolyXRD family-wide registration mechanism (implementation identical to `PolyXRD-Reg`, the same
key and `PXRD1-` registration code format; codes can be issued with the family `PolyXRD-RegTool` or this project's
`tools/make_reg_code.py`):

- **Unregistered**: on every launch a pop-up shows the copyright notice and contact email; click "OK" to continue (it will prompt again next time); click "Enter Registration Code" to register immediately.
- **Registered**: paste the registration code via Help menu "Enter Registration Code (&R)…"; once validation passes it is permanently registered (status stored in
  `%APPDATA%/PolyXRD/Registration/CrySize.json`, re-validated on every launch; manual edits have no effect).
- **Status bar**: the far right, right-aligned, shows "Registered: <Organization/Department Name>" or "Unregistered".
- **Internal evaluation build** (single-file exe) does not enable this mechanism; it only shows centered red text "Internal Evaluation Build".

Issuing codes (developer side):
```bash
python tools/make_reg_code.py "School of Materials Science and Engineering, Tsinghua University"
python tools/make_reg_code.py --verify PXRD1-XXXX-XXXX-XXXX-XXXX
```

## Workflow

1. **Import the sample pattern**: two-column text (2θ, intensity), supporting `.txt .xy .dat .csv .asc .prn .raw`, etc.
   ASCII exports from Shimadzu/Rigaku/Bruker can be read directly; the program skips the header and extracts target material, step size and scan range.
2. **Import the standard pattern**: Si or LaB₆ measured on the **same day, with the same slit and the same scan speed** as the sample.
   This is the prerequisite for instrumental broadening correction — after changing slit, target or counting time, it must be re-measured.
3. The program automatically selects strong peaks, fits and calculates. Peaks can be checked/unchecked in the peak table on the left; unchecking triggers automatic recalculation.
4. **Export a report** (self-contained HTML, open in a browser and print to PDF) or **CSV**.

## Key conventions (affect numerical results — read carefully)

**1. Width convention and K value**

- Scherrer uses **FWHM**, K = 0.89 (spherical crystals)
- W-H uses **integral breadth β_int**, K = 1.0

Rationale: the W-H relation is derived from integral breadth; and integral breadth is additive under convolution (Stokes, Proc. Phys.
Soc. A 61 (1948) 382), whereas FWHM is not. Mixing the two introduces a 5%–20% systematic bias.
Switching the convention in the UI updates the default K accordingly, and it can also be changed manually.

**2. Instrumental broadening subtraction**

- FWHM convention: β = √(FWHM_obs² − FWHM_inst²)
- Integral-breadth convention: β = β_obs − β_inst

The instrumental resolution function uses the Caglioti form FWHM² = U·tan²θ + V·tanθ + W (Caglioti et al.,
Nucl. Instr. 3 (1958) 223), fitted from the standard peaks; when there are too few peaks or the fit quality is poor, it automatically falls back to
PCHIP interpolation of the measured points, and the UI notes which one is actually used.

**3. 2θ angle correction**

By comparing the measured standard peak positions with the theoretical Si/LaB₆ peak positions (a_Si = 5.431194 Å, a_LaB₆ = 4.156826 Å),
the zero offset is corrected automatically; when the deviation varies with 2θ, a cosθ term is added. After correction the Si peak-position residual is usually
within 0.005°, and d values can be compared directly with PDF cards.

**4. Peak-selection rules**

Select **3–6 strong peaks that are isolated, non-overlapping and spread as widely as possible in 2θ**, rather than simply taking the strongest peaks:

- The FWHM of an overlapping peak is contaminated by neighbouring peaks (this program mitigates it with multi-peak joint fitting within the window, but severe overlap
  still yields unreliable widths; in that case the peak is flagged and excluded from the statistics)
- W-H needs as many peaks as possible with a wide angular span (recommend ≥5 peaks, span ≥60°), otherwise the fit has too few degrees of freedom

**5. When there is no standard sample**

The program computes as usual, but the result is marked "no instrumental broadening correction applied": these D values are **apparent values that include instrumental broadening and are
systematically too small**, usable only for relative comparison between samples measured on the same instrument under the same conditions. The report shows a prominent warning bar.

## Reliable measurement range

| Crystallite size | Reliability |
|---|---|
| 2–100 nm | Main applicable range |
| 100–200 nm | Borderline; β is the difference of two similar widths, so uncertainty grows sharply |
| > 200 nm | Invalid (instrumental broadening ≥ observed broadening; the program flags it and excludes it from the average) |

The W-H method also assumes isotropic broadening and uniform strain. If the sample is markedly anisotropic (plate-like/needle-like crystals, stacking faults),
the W-H plot deviates from a straight line, R² drops noticeably, and the program gives a hint.

## Output

- **HTML report**: conclusion card, measurement conditions, per-peak width and D, three averaging conventions, instrumental line-width coefficients
  U/V/W (in both degree² and rad² units), W-H plot and data points, method and limitations notes
- **CSV**: peak table + summary values, convenient for batch aggregation

## Tests

```bash
python -m pytest tests -q                       # 12 core algorithm tests
python tools/smoke_gui.py sample.txt standard.txt  # GUI smoke: 3 tabs + two dialog screenshots + report generation
python tools/shot_report.py _smoke/report.html   # render the whole HTML report page to PNG to review the layout
```

The tests use a **forward-inverse closed loop** to verify mathematical correctness: generate a synthetic pattern with a known crystallite size from the Scherrer equation,
then let the program invert it and check whether it recovers the true value (20 nm, 50 nm, strain-free and strained cases). This path
once caught two real defects: the W-H microstrain was divided by an extra 4 (the horizontal axis already used 4sinθ), and the direction of "D too large without a standard sample"
was written backwards — showing that closed-loop testing is not a formality but the only correctness criterion.

> GUI smoke tests and report screenshots need a graphical session (`QT_QPA_PLATFORM=windows`); in pure offscreen mode
> CJK glyphs cannot be rendered and you get a row of "tofu blocks".

## Family conventions (PolyXRD)

This tool is a member of the PolyXRD family (project root `D:\Project\XRD`); its visual and engineering conventions match the other family
tools, and any change must be kept aligned with the sibling projects:

| Item | Convention |
|---|---|
| Visual identity | White regular hexagon + tool-specific graphic (here a progressively broadening diffraction peak with FWHM annotation), diagonal gradient from brand dark `#0F172A` → brand blue `#0284C7`, sub-tool accent cyan `#22D3EE` |
| Splash screen | `resources/splash-screen.png` (480×270); in the packaged build it is shown first by PyInstaller `Splash` during unpacking, then handed over via `pyi_splash.close()` after the main window `show()`; the close timer **must** be installed after `show()`, otherwise cold start crashes |
| Icon | The window uses PNG (built-in Qt6 decoding, does not load the `qico.dll` plugin); `.ico` is only for exe resources and the installer |
| Style | Fusion style + local inline styles + unified palette in `gui/theme.py`, no global QSS |
| Font | Microsoft YaHei 9 pt |
| i18n | `crysize/i18n/` (manager + trilingual translation tables); interface identical to RutAna (`tr()` returns `⟪key⟫` for missing keys, no fallback); core-layer warnings/quality flags are also generated via `tr()`, and the main window automatically recomputes and refreshes after a language switch |
| Edition | `crysize/edition.py`: `registered` (installer, enables the `registration.py` registration mechanism) or `internal` (single-file exe, status bar marked "Internal Evaluation Build", overridden by `installer/rthook_internal.py`, no registration) |
| Packaging | `build_exe.bat` → single-file internal evaluation build; `build_setup.bat` → onedir + Inno Setup registered-edition installer |
| License | Dual license: academic (non-commercial research and teaching) free; commercial use requires written authorization. Terms in `LICENSE` / `LICENSE-CN` |
| Contact | sshztx@outlook.com · https://github.com/PolyXRD |

Brand images are generated by `tools/build_artwork.py` (Pillow); to change the palette or graphic you only need to edit this one file
and run it again, avoiding colour differences across the icon, splash screen, logo and report.

## Directory layout

```
crysize/
  version.py      Version and product identity (family-wide fields)
  edition.py      Edition flag (registered / internal)
  registration.py Family-wide registration mechanism (enabled in registered edition: unregistered prompt / enter registration code / status-bar unit name; key identical to PolyXRD-Reg)
  i18n/           Trilingual infrastructure (manager + translations/zh_CN,en_US,ja_JP)
  core/
    pattern.py     Pattern reading (header skip, metadata extraction, descending flip)
    elasticity.py  Cubic hkl indexing and directional Young's modulus E(hkl) (for USDM/UDEDM)
    wh_models.py   W-H three variants UDM / USDM / UDEDM + grouping by Γ
    warren.py      Warren-Averbach: single-peak Voigt approximation + multi-order reflection Fourier method
    methods.py     Registry of 5 groups / 7 methods, unified result and selection-notes entry point
    peaks.py       Peak search and automatic peak selection
    profile.py     pseudo-Voigt fitting (local multi-peak, Kα₂ stripping, quality flags)
    instrument.py  Instrumental resolution function (Caglioti / PCHIP)
    standards.py   Si / LaB₆ reference data and angle correction
    size.py        Scherrer and W-H calculation
    analysis.py    Orchestration layer
  gui/
    __main__.py    Entry point (splash → main window → close splash)
    main_window.py Main window, parameter panel, peak table, language menu
    canvas.py      Pattern / W-H / line-width curve canvas
    report.py      HTML report (language follows the UI)
    dialogs.py     About / copyright and license
    theme.py       Family palette and font constants
    resources.py   Resource location (dev mode / sys._MEIPASS)
resources/         Brand assets (generated by build_artwork.py)
installer/         Inno Setup script, Chinese language file, internal-edition runtime hook
tools/             build_artwork.py, smoke_gui.py, shot_report.py
tests/             test_core.py (algorithm closed loop) + test_i18n.py (trilingual consistency)
                   + test_methods.py (elasticity/indexing, three variants, Warren-Averbach)
docs/              METHODS.md (selection scenarios and literature basis for the 5 groups / 7 methods)
pyproject.toml     Packaging metadata (dual-license LicenseRef, single source of version, pytest/ruff config)
PolyXRD-CrySize.spec / PolyXRD-CrySize-Setup.spec   PyInstaller internal edition / registered edition
build_exe.bat / build_setup.bat                    one-click build scripts
```

> `pip install -e .` requires setuptools ≥ 77 (the `license` / `license-files`
> fields of PEP 639), the same style as the family main program `PolyXRD/pyproject.toml`; for day-to-day development just run
> `python run.py` — no installation needed.

## References

- Scherrer, P. *Gött. Nachr.* **2** (1918) 98
- Williamson, G. K.; Hall, W. H. *Acta Metall.* **1** (1953) 22
- Caglioti, G.; Paoletti, A.; Ricci, F. P. *Nucl. Instr.* **3** (1958) 223
- Stokes, A. R. *Proc. Phys. Soc. A* **61** (1948) 382
- Langford, J. I.; Wilson, A. J. C. *J. Appl. Cryst.* **11** (1978) 102
- Warren, B. E.; Averbach, B. L. *J. Appl. Phys.* **21** (1950) 595
- de Keijser, Th. H.; Langford, J. I.; Mittemeijer, E. J.; Vogels, A. B. P.
  *J. Appl. Cryst.* **15** (1982) 308
- Noyan, I. C.; Cohen, J. B. *Residual Stress: Measurement by Diffraction and
  Interpretation*, Springer (1987)
- Nye, J. F. *Physical Properties of Crystals*, Clarendon Press (1957)
- Bindu, P.; Thomas, S. *J. Theor. Appl. Phys.* **8** (2014) 123

## License and contact

© 2026 PolyXRD Team · All rights reserved

This software is released under a **dual license**:

- **Academic license**: for non-commercial academic research and teaching only, free; may be freely used, copied, modified and distributed,
  with no commercial use permitted.
- **Commercial license**: contact the copyright holder for written authorization before commercial use.

Full terms are in `LICENSE` (English) and `LICENSE-CN` (Chinese). For commercial licensing and technical support:
sshztx@outlook.com.
