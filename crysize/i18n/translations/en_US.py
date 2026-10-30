"""English (en_US). Key set aligned 1:1 with zh_CN (source of truth).

- Numeric format placeholders (``{K:.2f}`` etc.) must stay identical across
  languages; only the surrounding words may change.
- HTML fragments (<b>/<br>/<sub> …) are kept verbatim; do not add/remove tags.
- Legends and table headers stay short so layouts do not overflow.
"""

TRANSLATIONS = {
    # ------------------------------------------------------------------ #
    # Window & menus
    # ------------------------------------------------------------------ #
    "win.title": "Crystallite Size & Microstrain Analysis",
    "menu.file": "&File",
    "menu.help": "&Help",
    "menu.language": "&Language",
    "menu.open_sample": "Import sample pattern…",
    "menu.open_standard": "Import standard pattern…",
    "menu.export_html": "Export HTML report…",
    "menu.export_csv": "Export CSV…",
    "menu.exit": "Exit",
    "menu.method": "Method notes",
    "menu.copyright": "Copyright & License",
    "menu.about": "About {name}",

    # ------------------------------------------------------------------ #
    # File row / buttons
    # ------------------------------------------------------------------ #
    "btn.sample": "Import sample pattern…",
    "btn.standard": "Import standard pattern…",
    "btn.clear_std": "Clear standard",
    "btn.recalc": "Recalculate",
    "btn.report": "Export report",
    "btn.csv": "Export CSV",
    "lbl.sample_none": "Sample: not loaded",
    "lbl.std_none": "Standard: not loaded",
    "lbl.sample_info": "Sample: {label} ({n} points, {lo:.1f}–{hi:.1f}°, λ={wl:.4f} Å)",
    "lbl.std_info": "Standard: {label} ({n} points)",

    # ------------------------------------------------------------------ #
    # Parameter panel
    # ------------------------------------------------------------------ #
    "group.params": "Analysis parameters",
    "group.corr": "Angle correction (from standard)",
    "group.peaks": "Peaks used (check to include)",
    "param.n_peaks": "Number of peaks",
    "param.width_mode": "Scherrer width convention",
    "param.K": "Shape factor K",
    "param.window": "Max fit window",
    "param.prominence": "Peak detection threshold",
    "suffix.peaks": " peaks",
    "mode.fwhm": "FWHM (K = 0.89)",
    "mode.integral": "Integral breadth β_int (K = 1.0)",
    "param.ka2": "Strip Kα₂ during fitting (recommended)",
    "param.ka2_tip": "Without a monochromator, the Kα₂ satellite spuriously widens high-angle peaks by 10–20%",
    "param.prom_tip": "Peaks below this relative prominence are ignored by auto-selection",
    "corr.lbl_none": "No standard loaded",
    "corr.lbl_none_full": "No standard loaded: no angle or instrumental-broadening correction applied",

    # ------------------------------------------------------------------ #
    # Tabs / peak table
    # ------------------------------------------------------------------ #
    "tab.scherrer": "① Scherrer",
    "tab.wh": "② Williamson-Hall",
    "tab.inst": "③ Standard & instrumental width",
    "th.note": "Note",
    "note.instrument_exceeds": "Instr. ≥ observed",
    "note.unreliable": "Poor fit",
    "note.no_std": "Uncorrected",

    # ------------------------------------------------------------------ #
    # Dialogs / messages / status bar
    # ------------------------------------------------------------------ #
    "filter.patterns": "Diffraction patterns ({exts})",
    "filter.all": "All files (*.*)",
    "dlg.choose_sample": "Choose sample pattern",
    "dlg.choose_standard": "Choose standard pattern (Si or LaB₆)",
    "dlg.read_fail": "Read failed",
    "dlg.calc_fail": "Calculation failed",
    "dlg.refit_fail": "Refit failed",
    "dlg.info": "Notice",
    "dlg.need_compute": "Import a sample pattern and run the calculation first.",
    "dlg.save_html": "Save HTML report",
    "dlg.save_csv": "Export CSV",
    "dlg.export_fail": "Export failed",
    "dlg.export_done": "Export complete",
    "dlg.open_now": "Report saved. Open it now?",
    "dlg.std_loaded": "Standard loaded. Now import the sample pattern.",
    "dlg.min_peaks": "Select at least 2 peaks",
    "dlg.ok": "OK",
    "edition.internal": "Internal evaluation build",
    "about.role": "Powder diffraction peak-width analysis: Scherrer and Williamson-Hall crystallite size and microstrain",
    "about.contact": "Contact",
    "about.chip1": "Per-peak Scherrer",
    "about.chip2": "Williamson-Hall",
    "about.chip3": "Standard correction",
    "about.title": "About {name}",
    "copyright.title": "Copyright & License",
    "status.ready": "Ready: import a sample pattern (two-column text: 2θ, intensity)",
    "status.done": "Done: {valid}/{total} valid peaks, mean size {mean} nm{extra}",
    "status.uncorrected": " (no instrumental correction)",
    "fname.report": "{label}_crystallite_size_report.html",
    "fname.csv": "{label}_crystallite_size.csv",

    # ------------------------------------------------------------------ #
    # Summary panels of the three tabs (rich text)
    # ------------------------------------------------------------------ #
    "sum.no_warn": "✓ No obvious anomalies",
    "sum.scherrer.head": "Mean crystallite size (number average, {valid} of {total} peaks valid)",
    "sum.scherrer.stats": "Intensity-weighted {di} nm　Volume-weighted {dv} nm　Spread {sp}%",
    "sum.scherrer.model": "Model: pseudo-Voigt, {mode} convention, K = {K:.2f}, λ = {wl:.5f} Å, {corr}",
    "sum.mode.fwhm": "FWHM",
    "sum.mode.integral": "integral breadth",
    "sum.corr.done": "instrumental broadening removed",
    "sum.corr.none": "instrumental broadening NOT removed",
    "sum.wh.head": "Williamson-Hall linear fit (β·cosθ = Kλ/D + 4ε·sinθ)",
    "sum.wh.stats": "Microstrain ε = {e} %　R² = {r2}　Valid points {n}",
    "sum.wh.detail": "Slope ε = {slope}, intercept Kλ/D = {intercept} rad, per-peak integral-breadth mean {mean} nm",
    "sum.wh.note": "(integral-breadth convention — not directly comparable with the FWHM values on the Scherrer tab)",
    "sum.inst.head": "Instrumental resolution function (standard: {name})",
    "sum.inst.unknown": "unidentified",
    "sum.inst.caglioti": "Caglioti  U·tan²θ + V·tanθ + W",
    "sum.inst.pchip": "PCHIP interpolation (measured points)",
    "sum.inst.coef": "　U = {u}, V = {v}, W = {w}　(deg², R² = {r2}, RMS = {rms}°)",
    "sum.inst.corr": "Angle correction: {desc}",
    "sum.inst.th_corr": "2θ corrected",
    "sum.inst.th_obs": "2θ observed",
    "sum.inst.th_fwhm_obs": "FWHM obs.",
    "sum.inst.th_fwhm_model": "FWHM model",
    "sum.inst.empty": "No standard pattern loaded.<br>After importing an Si or LaB₆ pattern measured under the "
                      "same conditions, the instrumental resolution function U/V/W, the instrumental width curve "
                      "and the angle-correction parameters are shown here.",

    # ------------------------------------------------------------------ #
    # Canvases (matplotlib)
    # ------------------------------------------------------------------ #
    "cv.empty": "Import a sample pattern to display",
    "cv.std_empty": "No standard loaded",
    "cv.intensity": "Intensity (counts)",
    "cv.full_title": "Sample pattern and peaks used",
    "cv.obs": "Observed",
    "cv.fit": "Total fit",
    "cv.bg": "Background",
    "cv.comp": "Peak component",
    "cv.zoom_title": "Peak fit detail: 2θ = {tt:.3f}°, η = {eta:.2f}, Rwp = {rwp:.1f}%",
    "cv.beta_corr": ", β after instrumental correction = {beta:.3f}°",
    "cv.wh_points": "Peaks used in fit",
    "cv.wh_fit": "Linear fit",
    "cv.wh_intercept": "Intercept {xi:.3f}",
    "cv.wh_to_size": " rad → D = {d:.1f} nm",
    "cv.excluded": "Excluded: {peaks} (poor fit quality)",
    "cv.wh_groups": "direction groups",
    "cv.std_meas": "Standard FWHM (measured)",
    "cv.std_model": "Model ({m})",
    "cv.model_caglioti": "Caglioti U/V/W",
    "cv.model_pchip": "PCHIP interpolation",
    "cv.std_title": "Instrumental width curve",
    "cv.y_instr": "Instrumental FWHM (°)",

    # ------------------------------------------------------------------ #
    # Method dialog
    # ------------------------------------------------------------------ #
    "method.title": "Method notes",
    "method.body": """
<b>Scherrer method</b><br>
D = K·λ/(β·cosθ). β is the pure physical broadening after instrumental
correction (radians); K is the shape factor: K≈0.89 with FWHM (spherical
crystallites), K=1.0 with integral breadth.<br><br>

<b>Instrumental-broadening correction</b><br>
Import an Si or LaB₆ standard measured under the same conditions; the
instrumental resolution function (Caglioti: FWHM² = U·tan²θ + V·tanθ + W)
is fitted from the standard peaks and subtracted at the sample peak
positions:<br>
· FWHM convention: β = √(FWHM_obs² − FWHM_inst²)<br>
· Integral-breadth convention: β = β_obs − β_inst (integral breadths are
additive under convolution — stricter)<br><br>

<b>Williamson-Hall</b><br>
β·cosθ = K·λ/D + 4·ε·sinθ. Linear fit of β·cosθ versus 4sinθ: the intercept
gives D, the slope gives the microstrain ε. β is the integral breadth, K=1.<br><br>

<b>Peak selection</b><br>
Choose 3–6 strong, isolated, well separated in 2θ peaks; overlapping peaks
yield overestimated FWHM and hence underestimated D. W-H needs as many peaks
as possible spanning a wide angle range (≥5 peaks over ≥60° recommended).
""",

    # ------------------------------------------------------------------ #
    # core: peak fit quality flags (profile.py)
    # ------------------------------------------------------------------ #
    "pf.not_converged": "Fit did not converge",
    "pf.eta_lorentz": "Nearly pure Lorentzian shape (η→1); possible unresolved overlap",
    "pf.eta_gauss": "Nearly pure Gaussian shape (η→0)",
    "pf.rwp_high": "High fit residual (Rwp={v:.1f}%)",
    "pf.fwhm_err": "Large FWHM uncertainty",
    "pf.neighbors": "{n} neighbouring peak(s) in window, fitted jointly",
    "pf.no_points": "Not enough data points in window",
    "pf.fit_error": "Fit error: {exc}",

    # ------------------------------------------------------------------ #
    # core: Scherrer / W-H warnings (size.py)
    # ------------------------------------------------------------------ #
    "w.no_standard": "No standard pattern (Si or LaB₆) imported, so no instrumental-broadening "
                     "correction was applied: the sizes below are apparent values that still contain the "
                     "instrumental contribution; D is systematically too small (the coarser the crystallites "
                     "and the broader the instrumental width, the larger the bias). Such values are only "
                     "valid for sample-to-sample comparison on the same instrument and slits — do not report "
                     "them as absolute sizes or compare with literature values.",
    "w.n_exceed": "For {n} peak(s) the instrumental width ≥ observed width, so no physical broadening "
                  "can be extracted (crystallites too large in that direction, or the standard width is "
                  "too broad); excluded from the averages.",
    "w.all_exceed": "No physical broadening could be extracted from any peak: the widths are dominated by "
                    "the instrument, i.e. the crystallite size is beyond the reliable range of peak-width "
                    "methods (≳100–200 nm). Use SEM/TEM instead, or reduce instrumental broadening with "
                    "longer counting times / narrower slits.",
    "w.too_large": "Some peaks give sizes > 150 nm, near the upper limit of peak-width methods "
                   "(β is obtained by subtracting two similar widths, inflating the relative uncertainty); "
                   "treat the values as indicative only.",
    "w.spread": "Large spread of per-peak sizes ({sp:.0f}%): possible preferred orientation, "
                "stacking faults/twins or anisotropic morphology; check the W-H plot for the strain "
                "contribution.",
    "w.doubtful": "Peaks at {pos} fit poorly (high residual or parameter at boundary, typical of "
                  "overlapping peaks); uncheck them in the peak table or choose isolated peaks and recalculate.",
    "w.wh_dropped": "Peak at {tt:.2f}° has poor fit quality and was excluded from the W-H regression.",
    "w.wh_too_few": "Fewer than 2 peaks are usable for W-H; linear regression is not possible.",
    "w.wh_neg_intercept": "Negative W-H intercept (< 0): no physically meaningful size can be derived. "
                          "Usually all broadening was absorbed into the strain term, or the instrumental "
                          "correction is under/over-done — check the standard and the peak widths.",
    "w.wh_few_peaks": "W-H uses only {n} peak(s); very few degrees of freedom — treat the result as "
                      "indicative only.",
    "w.wh_neg_slope": "Negative W-H slope (negative microstrain): usually indicates scattered data or "
                      "an improper correction; do not interpret as compressive strain.",
    "w.wh_low_r2": "Low W-H R² = {r2:.2f}: the two-parameter size–strain model may not suit this sample "
                   "(common with anisotropic broadening / stacking faults).",
    "w.wh_no_standard": "W-H likewise without instrumental-broadening correction: the intercept (Kλ/D) is "
                        "inflated by instrumental broadening so D is too small, and the slope (strain term) "
                        "absorbs the growth of instrumental width with 2θ — do not quote the microstrain "
                        "directly.",

    # ------------------------------------------------------------------ #
    # core: instrument model notes (instrument.py)
    # ------------------------------------------------------------------ #
    "inst.no_peaks": "No usable peaks fitted in the standard pattern; instrumental correction unavailable.",
    "inst.zero_fixed": "User-specified zero offset {v:+.4f}°",
    "inst.no_quality": "No standard peak passed the quality checks; instrumental correction unavailable.",
    "inst.caglioti_ok": "Caglioti fit from {n} standard peaks",
    "inst.caglioti_fallback": "Caglioti fit quality insufficient (R²={r2:.2f}, physicality check {phy}); "
                              "falling back to PCHIP interpolation",
    "inst.phy_ok": "passed",
    "inst.phy_fail": "failed",
    "inst.caglioti_error": "Caglioti fit failed ({exc}); falling back to PCHIP interpolation",
    "inst.few_peaks": "Only {n} usable standard peak(s) (<{m} or insufficient span); using PCHIP interpolation",

    # ------------------------------------------------------------------ #
    # core: angle correction (standards.py)
    # ------------------------------------------------------------------ #
    "corr.not_applied": "No angle correction applied",
    "corr.desc.zero": "Constant zero offset only, Δ0 = {v:+.4f}°",
    "corr.desc.zero_disp": "Δ2θ = Δ0 + k·cosθ, Δ0 = {d0:+.4f}°, k = {k:+.4f}° (residual RMS {rms:.4f}°)",
    "corr.no_match": "Standard peaks could not be matched to the Si/LaB₆ reference positions; "
                     "no angle correction applied.",
    "corr.match2": "Matched {n} reflections to {name} (a = {a:.6f} Å); Δ2θ = Δ0 + k·cosθ fit residual "
                   "RMS = {rms:.4f}°",
    "corr.match1": "Matched {n} reflections to {name} with consistent offsets (RMS {rms:.4f}°); "
                   "constant zero offset {shift:+.4f}° only",

    # ------------------------------------------------------------------ #
    # core: pattern reading / orchestration exceptions (pattern.py / analysis.py)
    # ------------------------------------------------------------------ #
    "pat.len_mismatch": "2θ and intensity arrays have different lengths",
    "pat.too_few": "Too few data points (<10) for analysis",
    "pat.no_data": "No contiguous two-column numeric block found (at least 10 rows required)",
    "ana.no_peaks": "No usable diffraction peaks found in the sample pattern; check the data or lower "
                    "the peak detection threshold.",
    "ana.window": "Peak fitting failed: not enough data points in the fit window; check step size and "
                  "data range.",

    # ------------------------------------------------------------------ #
    # CSV export
    # ------------------------------------------------------------------ #
    "csv.h_2th": "2θ(°)", "csv.h_d": "d(Å)", "csv.h_fwhm_obs": "FWHM_obs(°)",
    "csv.h_fwhm_inst": "FWHM_inst(°)", "csv.h_beta": "β(°)", "csv.h_D": "D(nm)",
    "csv.h_eta": "η", "csv.h_rwp": "Rwp(%)", "csv.h_status": "Status",
    "csv.h_quality": "Quality flags",
    "csv.ok": "valid",
    "csv.mean_n": "Number average (nm)", "csv.mean_i": "Intensity-weighted (nm)",
    "csv.mean_v": "Volume-weighted (nm)", "csv.spread": "Spread (%)",
    "csv.wh_d": "W-H D (nm)", "csv.wh_strain": "W-H microstrain (%)", "csv.wh_r2": "W-H R²",
    "csv.instr_corr": "Instrumental correction", "csv.corrected": "corrected",
    "csv.uncorrected": "uncorrected",

    # ------------------------------------------------------------------ #
    # HTML report
    # ------------------------------------------------------------------ #
    "rep.title": "XRD Crystallite Size Analysis Report",
    "rep.doc_title": "{name} — Crystallite Size Analysis Report",
    "rep.unnamed": "Unnamed sample",
    "rep.sample": "Sample",
    "rep.report_time": "Report date",
    "rep.operator": "Operator",
    "rep.h1_cond": "1. Measurement and calculation conditions",
    "rep.h2_scherrer": "2. Crystallite size per peak (Scherrer)",
    "rep.h3_inst": "3. Instrumental broadening and resolution coefficients",
    "rep.h4_wh": "4. Williamson-Hall method",
    "rep.h5_limits": "5. Method and limitations",
    "rep.h_comment": "Comments",

    "rep.card_dn": "Mean size D<sub>n</sub>",
    "rep.card_nvalid": "Valid peaks",
    "rep.card_wh": "W-H size",
    "rep.card_strain": "Microstrain ε",

    "rep.c_sample": "Sample",
    "rep.c_file": "Data file",
    "rep.c_target": "Target / wavelength",
    "rep.c_range": "Scan range",
    "rep.c_points": "Data points",
    "rep.c_model": "Profile model",
    "rep.c_model_ka2": ", with Kα₂ component",
    "rep.c_npeaks": "Number of peaks used",
    "rep.c_npeaks_note": " (auto-selected strongest peaks; editable)",
    "rep.c_width": "Width convention",
    "rep.c_std": "Standard pattern",
    "rep.c_std_id": "Standard identified",
    "rep.c_angcorr": "2θ angle correction",
    "rep.c_std_none": "not loaded",
    "rep.c_std_unknown": "unidentified",
    "rep.c_range_val": "{lo:.2f}° – {hi:.2f}°, step {st:.4f}°",
    "rep.c_target_val": "{anode} Kα₁, λ = {wl:.7f} Å",
    "rep.width_fwhm": "FWHM",
    "rep.width_int": "integral breadth β_int",

    "rep.t1_cap": "Table 1　Peak widths and Scherrer sizes ({mode} convention; widths in °, "
                  "R<sub>wp</sub> in %)",
    "rep.th_2th": "2θ (°)",
    "rep.th_d": "d (Å)",
    "rep.th_status": "Status",

    "rep.t2_cap": "Table 2　Three averaging conventions for the mean size",
    "rep.t2_th1": "Average",
    "rep.t2_th2": "Value (nm)",
    "rep.t2_th3": "Remarks",
    "rep.avg_dn": "Number average D<sub>n</sub>",
    "rep.avg_dn_note": "Equal-weight arithmetic mean; most common",
    "rep.avg_di": "Intensity-weighted D<sub>I</sub>",
    "rep.avg_di_note": "Weighted by net peak height; strong peaks dominate",
    "rep.avg_dv": "Volume-weighted D<sub>v</sub>",
    "rep.avg_dv_note": "Σ(I·D⁴)/Σ(I·D³); corresponds to specific surface area",
    "rep.avg_spread": "Spread",
    "rep.avg_spread_note": "Std/mean of per-peak D; reflects anisotropy",

    "rep.note_scherrer": "Scherrer equation D = K·λ/(β·cosθ). β is the pure physical broadening after "
                         "instrumental correction: this report uses {how} ({formula}). D is the "
                         "coherence length perpendicular to the diffracting planes, not the particle "
                         "diameter; for spherical particles D is typically a lower bound of the diameter.",
    "rep.how_fwhm": "FWHM difference in quadrature",
    "rep.how_int": "direct subtraction of integral breadths",
    "rep.f_fwhm": "β = √(FWHM_obs² − FWHM_inst²)",
    "rep.f_int": "β = β_obs − β_inst",

    "rep.i_phase": "Standard phase",
    "rep.i_unknown_phase": "unidentified phase",
    "rep.i_func": "Resolution function",
    "rep.i_func_caglioti": "Caglioti polynomial FWHM² = U·tan²θ + V·tanθ + W",
    "rep.i_func_pchip": "PCHIP interpolation of measured points",
    "rep.i_uvw_deg": "U / V / W (deg²)",
    "rep.i_uvw_rad": "U / V / W (rad²)",
    "rep.i_r2": "R² = {r2:.3f}, RMS = {rms:.4f}°",
    "rep.i_coverage": "Standard peak coverage",
    "rep.i_note": "Note",
    "rep.t3_cap": "Table 3　Measured widths of the standard peaks and the resolution function",
    "rep.t3_corr": "2θ<sub>corr.</sub>",
    "rep.t3_obs": "2θ<sub>obs.</sub>",
    "rep.t3_fobs": "FWHM<sub>obs.</sub> (°)",
    "rep.t3_fmodel": "FWHM<sub>model</sub> (°)",
    "rep.t3_res": "Residual (°)",
    "rep.i_note_txt": "U/V/W is the measured resolution function for the Cu target and the slits/scan "
                      "speed listed above; it is valid only for measurements taken under these same "
                      "conditions. Re-measure the standard after changing slits, target or counting time. "
                      "“2θ corrected” refers to peak positions after the angle correction (zero offset "
                      "and cosθ term).",

    "rep.w_fit": "Fitting equation",
    "rep.w_fit_val": "β·cosθ = K·λ/D + 4·ε·sinθ, β = integral breadth, K = {K:.2f}",
    "rep.w_d": "Crystallite size D",
    "rep.w_strain": "Microstrain ε",
    "rep.w_goodness": "Goodness of fit",
    "rep.w_goodness_val": "R² = {r2}, {n} valid points",
    "rep.w_ref": "Cross-check",
    "rep.w_ref_val": "Per-peak integral-breadth mean {mean} nm",
    "rep.w_ref_note": "(K = 1, same convention as W-H; usually smaller than the W-H size once strain is "
                      "separated. Note: not directly comparable with the FWHM/K = 0.89 values in "
                      "Section 2)",
    "rep.t4_cap": "Table 4　W-H plot data points",
    "rep.w_not_reg": "not in regression",
    "rep.w_note": "The W-H method requires the width to vary monotonically with 2θ. Non-monotonic "
                  "behaviour (anisotropic broadening, stacking faults, preferred orientation) invalidates "
                  "the single-line model and lowers R²; use an anisotropic model or analyse by crystal "
                  "direction instead. Treat results based on fewer than 4 valid points as indicative only.",

    "rep.fig1": "Fig. 1　Sample pattern and peaks used (red: fitted profile, shading: fit windows)",
    "rep.fig2": "Fig. 2　Williamson-Hall plot: the intercept gives the size, the slope the microstrain",
    "rep.wp_points": "Peaks used in fit",
    "rep.wp_fit": "Linear fit",

    "rep.st_unreliable": "poor fit",
    "rep.st_insexceed": "unsolvable",
    "rep.st_nostd": "uncorrected",

    "rep.lim1_h": "1. Conventions",
    "rep.lim1": "The Scherrer method uses FWHM with K = 0.89 (spherical crystallites); the W-H method uses "
                "integral breadth with K = 1, because the W-H relation is derived from integral breadths, "
                "which are additive under convolution (Stokes, 1948), whereas FWHM is not. Mixing the two "
                "conventions introduces systematic errors of 5–20%.",
    "rep.lim2_h": "2. Reliable range",
    "rep.lim2": "Peak-width methods are sensitive to 2–100 nm. Above ~100–200 nm, β is obtained by "
                "subtracting two similar widths, the relative uncertainty explodes and the result becomes "
                "meaningless (such peaks are flagged in this report). Below 2 nm, atomic-layer effects and "
                "the Debye–Waller factor matter and the Scherrer equation no longer holds strictly.",
    "rep.lim3_h": "3. Factors not included",
    "rep.lim3": "This report does not separate broadening from stacking faults, twins or dislocations, and "
                "does not model preferred orientation or anisotropic broadening; W-H assumes isotropic "
                "broadening and uniform strain. For clearly anisotropic samples (plate/needle habits) the "
                "W-H plot deviates from a straight line — use an anisotropic model (e.g. Warren-Averbach) "
                "or group by crystal direction.",

    "rep.foot_note": "This report was generated by the software above. The software is released under a "
                     "dual license: the Academic License covers non-commercial academic research and "
                     "teaching only; commercial use requires a separate written license (see the "
                     "accompanying LICENSE / LICENSE-CN). When citing the algorithms, reference the "
                     "original Scherrer and Williamson–Hall papers.",

    # ============ v2.0.0 method system: 5 groups / 7 methods ============
    "g.scherrer.name": "① Scherrer",
    "g.udm.name": "② W-H uniform deformation (UDM)",
    "g.usdm.name": "③ W-H uniform stress (USDM)",
    "g.udedm.name": "④ W-H deformation energy density (UDEDM)",
    "g.warren.name": "⑤ Warren–Averbach",

    "m.scherrer_fwhm.name": "Scherrer (FWHM basis, K=0.89)",
    "m.scherrer_fwhm.assume": "All broadening comes from finite crystallite size; components assumed "
                              "Gaussian, so instrumental width is removed by quadratic difference.",
    "m.scherrer_fwhm.need": "Sample pattern alone gives a number; a matching standard is required to "
                            "make it quantitative.",
    "m.scherrer_fwhm.scene": "Routine screening when only an order-of-magnitude size is needed and "
                             "size/strain separation is not required.",
    "m.scherrer_fwhm.limit": "Microstrain, faults and residual instrumental width are all counted as "
                             "size, so D is biased low; meaningless above ~100 nm.",

    "m.scherrer_integral.name": "Scherrer (integral-breadth basis, K=1.0)",
    "m.scherrer_integral.assume": "Same, but uses integral breadth, which is exactly additive under "
                                  "convolution (Stokes 1948).",
    "m.scherrer_integral.need": "Same; more robust than FWHM when profiles are strongly Lorentzian.",
    "m.scherrer_integral.scene": "Visibly tailed profiles (large η), or when comparing against W-H / "
                                 "W-A results on the same footing.",
    "m.scherrer_integral.limit": "Same bias; integral breadth is more sensitive to residual neighbour "
                                 "intensity inside the window, so overlapping peaks bias it high.",

    "m.wh_udm.name": "W-H uniform deformation model (UDM)",
    "m.wh_udm.assume": "Strain is the same in every direction (isotropic uniform deformation); "
                       "β·cosθ is linear in 4sinθ.",
    "m.wh_udm.need": "≥2 valid peaks; a standard is strongly recommended, otherwise instrumental "
                     "broadening is absorbed into size.",
    "m.wh_udm.scene": "Standard case where size D and microstrain ε must be separated — the least "
                      "demanding of the three variants.",
    "m.wh_udm.limit": "Anisotropic samples give poor linearity (low R²) and D/ε contaminate each other.",

    "m.wh_usdm.name": "W-H uniform stress model (USDM)",
    "m.wh_usdm.assume": "Stress σ is uniform; strain is distributed by directional stiffness "
                        "(ε = σ/E(hkl)).",
    "m.wh_usdm.need": "Cubic lattice parameter a plus elastic constants c11/c12/c44 (otherwise it "
                      "degenerates to UDM).",
    "m.wh_usdm.scene": "Clear elastic anisotropy with stress-type broadening dominant; compare R² "
                       "against UDM/UDEDM and pick the best.",
    "m.wh_usdm.limit": "Depends on the accuracy of E(hkl); a wrong a value or lattice type corrupts "
                       "the whole abscissa.",

    "m.wh_udedm.name": "W-H deformation energy density model (UDEDM)",
    "m.wh_udedm.assume": "Deformation energy density u = ε²E/2 is uniform; the slope gives √u.",
    "m.wh_udedm.need": "As for USDM: a and c11/c12/c44; degenerates to UDM without elastic data.",
    "m.wh_udedm.scene": "Common for nanopowders; often more linear than USDM when deformation is "
                        "dominated by dislocations or interface energy.",
    "m.wh_udedm.limit": "As for USDM; the uniform-energy assumption may fail for dense bulk samples.",

    "m.wa_single.name": "Warren–Averbach single-line approximation (Voigt)",
    "m.wa_single.assume": "Lorentzian component → size broadening, Gaussian component → strain "
                          "broadening (a profile-shape assumption).",
    "m.wa_single.need": "Isolated single peaks suffice, no higher orders required; a standard is "
                        "needed.",
    "m.wa_single.scene": "Compromise when no higher-order reflections are measurable but size/strain "
                         "separation is still wanted.",
    "m.wa_single.limit": "Strongly profile-shape dependent; deviations >20% are possible. Do not mix "
                         "with Warren–Averbach Fourier values.",

    "m.wa_fourier.name": "Warren–Averbach multi-order Fourier method",
    "m.wa_fourier.assume": "Separates the size term A^S(L) from the strain term A^D(L) in Fourier "
                           "space; no profile-shape superposition assumed.",
    "m.wa_fourier.need": "≥3 valid peaks with at least 2 distinct d values (higher orders of one "
                         "family are ideal); a standard is mandatory.",
    "m.wa_fourier.scene": "Highest-tier choice when data quality allows higher orders; yields a "
                          "volume-weighted size and L-dependent r.m.s. strain.",
    "m.wa_fourier.limit": "Neighbour overlap, residual Kα₂ and noise are all amplified by the "
                          "Fourier transform; no result is given when the data do not qualify.",

    "m.sec.strain": "microstrain ε",
    "m.sec.stress": "uniform stress σ",
    "m.sec.energy": "energy density u",
    "m.reason.no_valid_peak": "no valid peak",
    "m.reason.too_few": "fewer than 2 valid peaks",
    "m.reason.degenerate": "no elastic constants — degenerates to the UDM fit",
    "m.reason.no_lattice": "grouping needs a lattice parameter and successful indexing",
    "m.reason.wa_unmet": "data requirements of the Fourier method not met",
    "m.reason.unknown": "unknown method",
    "m.head.assume": "Assumption",
    "m.head.need": "Input required",
    "m.head.scene": "Best used when",
    "m.head.limit": "Limitation",
    "m.status.ok": "OK",
    "m.status.degraded": "degraded",
    "m.status.unavailable": "unavailable",

    "whv.too_few": "fewer than 2 valid peaks — cannot regress",
    "whv.neg_slope": "negative slope — strain term unphysical",
    "whv.low_r2": "poor linearity (R²={r2:.3f}) — check anisotropy or overlapping peaks",
    "whv.no_index": "indexing failed — cannot group by direction",
    "whv.group_single": "only one direction group — equivalent to no grouping",
    "whv.group_fallback": "no group has 2 peaks (no higher orders in the pattern) — reverted to the ungrouped fit",
    "whv.degenerate": "E(hkl) is constant — this variant is algebraically identical to UDM",
    "whv.no_elastic": "no elastic constants — abscissa degenerates to 4sinθ",
    "whv.few": "only {n} peaks in the regression — limited confidence",

    "wa.excluded": "peak excluded by the quality gate",
    "wa.no_standard": "no instrumental broadening correction",
    "wa.need_standard": "no standard loaded — broadening includes the instrument",
    "wa.single_note": "the single-line approximation is profile-shape dependent and is not "
                      "comparable with Fourier results",
    "wa.fourier_need_peaks": "Fourier method needs ≥3 valid peaks, found {n}",
    "wa.fourier_need_orders": "Fourier method needs at least 2 distinct d values (higher orders)",
    "wa.fourier_need_std": "Fourier method needs a standard for Stokes deconvolution",
    "wa.fourier_window": "no common Fourier interval across peak windows",
    "wa.fourier_no_fit": "Fourier coefficient regression did not converge",
    "wa.fourier_no_size": "size could not be obtained from the initial slope of A^S(L)",
    "wa.fourier_out_of_range": "D_v={d:.1f} nm is outside the reliable range of breadth methods (0.5–500 nm) — indicative only",
    "wa.th_l": "L (Å)",
    "wa.th_as": "A^S(L)",
    "wa.th_eps": "⟨ε²⟩^½",

    # GUI
    "group.method": "Calculation method",
    "param.method": "Primary method",
    "param.group_dir": "group by crystal direction (anisotropy)",
    "param.group_dir_tip": "group by Γ — needs a lattice parameter and ≥2 peaks per group",
    "param.elastic": "Phase elastic data (USDM/UDEDM and grouping)",
    "param.preset": "Preset phase",
    "param.preset_none": "custom / disabled",
    "param.a": "lattice a",
    "param.c11": "c₁₁",
    "param.c12": "c₁₂",
    "param.c44": "c₄₄",
    "param.lattice": "lattice type",
    "param.lattice_fcc": "fcc",
    "param.lattice_bcc": "bcc",
    "param.lattice_simple": "simple",
    "btn.method_guide": "Method selection guide",
    "sum.method.head": "Primary method",
    "sum.method.sec": "secondary quantity",
    "sum.method.state": "status",
    "tab.methods": "Method comparison",
    "method2.title": "Method selection guide (5 groups · 7 methods)",
    "method2.body": "① Scherrer: FWHM-basis / integral-breadth — use when only a size magnitude is "
                    "needed; microstrain is folded into size, so D is biased low.\n"
                    "② UDM: standard way to separate size from microstrain, least input required.\n"
                    "③ USDM: uniform stress, strain distributed by directional stiffness; needs "
                    "elastic constants.\n"
                    "④ UDEDM: uniform deformation energy density; common for nanopowders; needs "
                    "elastic constants.\n"
                    "⑤ Warren–Averbach: single-line approximation (no higher orders needed, "
                    "profile-shape dependent); multi-order Fourier method (≥3 peaks, ≥2 distinct d, "
                    "most rigorous).\n\n"
                    "Without elastic constants ②③④ collapse onto the same fit; grouping by direction "
                    "is an add-on switch for ②③④ and requires a lattice parameter for indexing.",
    "rep.h_method": "Methods and cross-comparison",
    "rep.m_sel": "primary method of this run",
    "rep.m_table_cap": "Table 5　Cross-comparison of the 7 methods (same peak fits, not independent "
                       "re-fits)",
    "rep.m_th_method": "Method",
    "rep.m_th_group": "Group",
    "rep.m_th_size": "D (nm)",
    "rep.m_th_sec": "Secondary",
    "rep.m_th_r2": "R²",
    "rep.m_th_n": "peaks",
    "rep.m_th_status": "status",
    "rep.m_note": "The D values have different meanings across methods (Scherrer: number average; "
                  "W-A Fourier: volume weighted), so comparing numbers across methods is meaningless; "
                  "compare consistency within one method instead.",
    "csv.h_method": "method",
}
