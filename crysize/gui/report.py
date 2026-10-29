"""自包含 HTML 报告（图片 base64 内嵌，浏览器直接打开或打印为 PDF）。

报告结构对齐粉晶衍射峰宽分析的通行报告要素：样品与测量条件 → 角度校正与
仪器线宽 → 各峰晶粒尺寸 → 平均值 → W-H 图 → 方法与局限。

数值一律来自 :class:`crysize.core.analysis.AnalysisBundle`，报告层不做任何
再计算，避免"界面显示与报告数值不一致"。
"""

from __future__ import annotations

import base64
import datetime
import html
import io
import math

import numpy as np

from crysize.core.analysis import AnalysisBundle
from crysize.i18n import current_language, tr
from crysize.version import APP_CONTACT_EMAIL, APP_COPYRIGHT, APP_NAME, __version__

_STYLE = """
:root{ --ink:#1A1A1A; --muted:#646464; --line:#D8D8D8; --brand:#0284C7; --warn:#B45309; }
*{ box-sizing:border-box; }
body{ margin:0; padding:0; background:#F4F5F7;
      font-family:"Source Han Sans CN","思源黑体 CN","Noto Sans CJK SC",
                  "Microsoft YaHei",sans-serif;
      color:var(--ink); font-size:13.2px; line-height:1.66; }
.page{ width:210mm; min-height:297mm; margin:18px auto; background:#fff;
       padding:20mm 18mm 16mm; box-shadow:0 6px 24px rgba(0,0,0,.08); }
h1{ font-size:19px; margin:0 0 4px; font-weight:700; letter-spacing:.5px; }
.sub{ font-size:12px; color:var(--muted); margin-bottom:6px; }
.rule{ height:2px; background:var(--ink); margin:10px 0 4px; }
h2{ font-size:13px; font-weight:700; margin:22px 0 8px; padding-left:8px;
    border-left:3px solid var(--brand); letter-spacing:.4px; }
h3{ font-size:12.4px; font-weight:700; margin:14px 0 6px; color:#333; }
table{ width:100%; border-collapse:collapse; font-size:11.9px;
       font-variant-numeric:tabular-nums; }
caption{ caption-side:top; text-align:left; font-size:11.4px; color:var(--muted);
         padding-bottom:5px; }
th{ text-align:left; font-weight:700; padding:6px 4px; border-top:1.4px solid var(--ink);
    border-bottom:1px solid var(--ink); background:#FAFAFA; white-space:nowrap; }
td{ padding:4.4px 4px; border-bottom:1px solid #EFEFEF; white-space:nowrap; }
tbody tr:last-child td{ border-bottom:1.4px solid var(--ink); }
.num{ text-align:right; }
.hero{ display:flex; gap:14px; margin:12px 0 4px; flex-wrap:wrap; }
.card{ flex:1 1 150px; border:1px solid var(--line); border-radius:6px;
       padding:10px 14px; background:#FCFCFD; }
.card .k{ font-size:11.4px; color:var(--muted); }
.card .v{ font-size:22px; font-weight:700; color:var(--brand); line-height:1.3; }
.card .u{ font-size:11.4px; color:var(--muted); font-weight:400; }
.warn{ border-left:3px solid var(--warn); background:#FFF8ED; color:#7C4A03;
       padding:9px 12px; font-size:12.2px; margin:10px 0; border-radius:0 4px 4px 0; }
.note{ font-size:11.6px; color:var(--muted); margin-top:6px; }
.grey{ color:var(--muted); }
.figcap{ font-size:11.4px; color:var(--muted); text-align:center; margin:4px 0 12px; }
img{ width:100%; border:1px solid var(--line); border-radius:4px; }
dl{ margin:6px 0; display:grid; grid-template-columns:130px 1fr;
    gap:3px 12px; font-size:12.2px; }
dt{ color:var(--muted); }
dd{ margin:0; }
.foot{ margin-top:26px; padding-top:10px; border-top:1px solid var(--line);
       font-size:10.8px; color:#9A9A9A; display:flex; justify-content:space-between; }
.tag{ display:inline-block; font-size:11px; padding:1px 7px; border-radius:3px;
      margin-left:6px; vertical-align:2px; }
.t-ok{ background:#E8F3EA; color:#256B3A; }
.t-warn{ background:#FDF0D8; color:#8A5300; }
.t-bad{ background:#FBE4E4; color:#9B2226; }
@media print{ body{ background:#fff; } .page{ box-shadow:none; margin:0;
  width:auto; min-height:0; padding:0; } h2{ page-break-after:avoid; }
  table{ page-break-inside:auto; } tr{ page-break-inside:avoid; } }
"""

_STATUS_KEY = {
    "": "",
    "unreliable": "rep.st_unreliable",
    "instrument_exceeds": "rep.st_insexceed",
    "no_standard": "rep.st_nostd",
}


def _fmt(v, nd: int = 2, dash: str = "—") -> str:
    if v is None:
        return dash
    try:
        f = float(v)
    except (TypeError, ValueError):
        return dash
    if not math.isfinite(f):
        return dash
    return f"{f:.{nd}f}"


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _mpl_figure(*args, **kwargs):
    """建 Figure 并确保中文字体可用。

    不切换 backend：``matplotlib.use()`` 会重置 rcParams，在 GUI 里还会影响
    已加载的画布；纯 Figure 的 savefig 本身不需要 pyplot。
    """
    import matplotlib
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    from matplotlib.figure import Figure
    return Figure(*args, **kwargs)


def _wh_png(bundle: AnalysisBundle, dpi: int = 130) -> str:
    """W-H 图，返回 base64（不依赖 GUI）。"""
    wh = bundle.wh
    good = [p for p in wh.points if p.ok]
    if not good:
        return ""
    fig = _mpl_figure(figsize=(6.2, 3.9), dpi=dpi, facecolor="white")
    ax = fig.add_subplot(111)
    gx = np.array([p.x for p in good])
    gy = np.array([p.y for p in good]) * 1000.0
    ax.plot(gx, gy, "o", ms=6.5, color="#0F5C8C", label=tr("rep.wp_points"), zorder=3)
    for p in good:
        ax.annotate(f"{p.two_theta:.1f}°", xy=(p.x, p.y * 1000), xytext=(5, 5),
                    textcoords="offset points", fontsize=8, color="#646464")
    if np.isfinite(wh.slope) and np.isfinite(wh.intercept):
        xs = np.linspace(0, max(gx.max() * 1.08, 0.2), 50)
        ax.plot(xs, (wh.slope * xs + wh.intercept) * 1000, color="#B03A2E", lw=1.3,
                label=tr("rep.wp_fit"), zorder=2)
        ax.plot([0], [wh.intercept * 1000], "s", ms=5.5, color="#B03A2E", zorder=4)
    ax.set_xlabel("4 sinθ", fontsize=10, color="#646464")
    ax.set_ylabel(r"$\beta\cdot\cos\theta$  $(\times10^{-3}\ \mathrm{rad})$",
                  fontsize=10, color="#646464")
    ax.set_xlim(left=0)
    ax.grid(True, color="#E6E6E6", lw=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CFCFCF")
    ax.tick_params(colors="#646464", labelsize=9)
    ax.legend(fontsize=8.5, frameon=False)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.95, bottom=0.16)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _spectrum_png(bundle: AnalysisBundle, dpi: int = 130) -> str:
    """谱图 + 拟合区间标记，返回 base64。"""
    fig = _mpl_figure(figsize=(6.2, 3.2), dpi=dpi, facecolor="white")
    ax = fig.add_subplot(111)
    x, y = bundle.sample.two_theta, bundle.sample.intensity
    ax.plot(x, y, color="#9AA5B1", lw=0.6, zorder=1)
    base = float(np.percentile(y, 5))
    for fit in bundle.fits:
        ax.plot(fit.region_two_theta, fit.region_calculated, color="#B03A2E", lw=1.0, zorder=3)
        ax.axvspan(fit.window[0], fit.window[1], color="#0F5C8C", alpha=0.09, lw=0)
        ax.annotate(f"{fit.center:.2f}°", xy=(fit.center, np.interp(fit.center, x, y)),
                    xytext=(0, 5), textcoords="offset points", ha="center",
                    fontsize=7.5, color="#0F5C8C")
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(bottom=max(base * 0.85, 0))
    ax.set_xlabel("2θ (°)", fontsize=10, color="#646464")
    ax.set_ylabel(tr("cv.intensity"), fontsize=10, color="#646464")
    ax.grid(True, color="#EEEEEE", lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CFCFCF")
    ax.tick_params(colors="#646464", labelsize=9)
    fig.subplots_adjust(left=0.105, right=0.98, top=0.96, bottom=0.16)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _status_tag(peak) -> str:
    label = tr(_STATUS_KEY.get(peak.flag, ""))
    if not peak.ok and peak.flag == "unreliable":
        return f'<span class="tag t-warn">{label}</span>'
    if peak.flag == "instrument_exceeds":
        return f'<span class="tag t-bad">{label}</span>'
    if peak.flag == "no_standard":
        return f'<span class="tag t-bad">{tr("rep.st_nostd")}</span>'
    return ""


def build_html(bundle: AnalysisBundle, *, sample_name: str = "", operator: str = "",
               comment: str = "") -> str:
    """生成完整 HTML 报告字符串（语言跟随当前 i18n 设置）。"""
    s = bundle.scherrer
    wh = bundle.wh
    inst = bundle.instrument
    tpl = bundle.sample
    name = sample_name or tpl.label or tr("rep.unnamed")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    width_txt = tr("rep.width_fwhm") if s.width_mode == "fwhm" else tr("rep.width_int")

    # -- 结论卡片 --------------------------------------------------------
    # 卡片数字保留两位，与界面大字、正文表格严格一致；只在位数确实无意义
    # 时才降精度（应变 3 位有效数字即可分辨 0.01% 量级）
    mean_val = _fmt(s.mean_number, 2)
    cards = [
        (tr("rep.card_dn"), mean_val, "nm"),
        (tr("rep.card_nvalid"), f"{s.n_valid}", f"/ {len(s.peaks)}"),
        (tr("rep.card_wh"), _fmt(wh.size_nm, 2), "nm"),
    ]
    if np.isfinite(wh.strain_pct):
        cards.append((tr("rep.card_strain"), f"{wh.strain_pct:.3f}", "%"))
    cards_html = "".join(
        f'<div class="card"><div class="k">{k}</div>'
        f'<div class="v">{v}<span class="u"> {u}</span></div></div>'
        for k, v, u in cards)

    # -- 警告（统一取自 bundle，保证界面与报告口径一致；无标样提示在首位）---
    warns = ""
    for w in bundle.warnings():
        warns += f'<div class="warn">{_esc(w)}</div>'

    # -- 测量条件 --------------------------------------------------------
    cond_rows = [
        (tr("rep.c_sample"), _esc(name)),
        (tr("rep.c_file"), _esc(tpl.path or "—")),
        (tr("rep.c_target"),
         tr("rep.c_target_val", anode=_esc(tpl.anode), wl=tpl.wavelength)),
        (tr("rep.c_range"),
         tr("rep.c_range_val", lo=tpl.range[0], hi=tpl.range[1], st=tpl.step)),
        (tr("rep.c_points"), f"{tpl.n}"),
        (tr("rep.c_model"), "pseudo-Voigt"
         + (tr("rep.c_model_ka2") if bundle.config.strip_ka2 else "")),
        (tr("rep.c_npeaks"),
         f"{bundle.config.n_peaks}{tr('rep.c_npeaks_note')}"),
        (tr("rep.c_width"),
         f"{width_txt}，K = {s.K:.2f}" if current_language().startswith("zh")
         else f"{width_txt}, K = {s.K:.2f}"),
    ]
    if inst is not None:
        cond_rows.append((tr("rep.c_std"),
                          _esc(bundle.standard.path if bundle.standard else "—")))
        cond_rows.append((tr("rep.c_std_id"),
                          _esc(inst.standard_name or tr("rep.c_std_unknown"))))
        cond_rows.append((tr("rep.c_angcorr"), _esc(inst.correction.describe())))
    else:
        cond_rows.append((tr("rep.c_std"), tr("rep.c_std_none")))
    cond_html = "".join(f"<dt>{_esc(k)}</dt><dd>{v}</dd>" for k, v in cond_rows)

    # -- 谢乐峰表 --------------------------------------------------------
    peak_rows = []
    for i, p in enumerate(s.peaks):
        fit = bundle.fits[i] if i < len(bundle.fits) else None
        peak_rows.append(
            "<tr>"
            f'<td class="num">{p.two_theta:.3f}</td>'
            f'<td class="num">{_fmt(p.d, 4)}</td>'
            f'<td class="num">{_fmt(p.fwhm_obs, 4)}</td>'
            f'<td class="num">{_fmt(p.fwhm_inst, 4)}</td>'
            f'<td class="num">{_fmt(p.beta_deg, 4)}</td>'
            f'<td class="num"><b>{_fmt(p.size_nm, 2)}</b></td>'
            f'<td class="num">{_fmt(p.eta, 2)}</td>'
            f'<td class="num">{_fmt(fit.rwp if fit else None, 1)}</td>'
            f'<td>{_status_tag(p)}</td>'
            "</tr>")
    peak_table = (
        '<table><caption>' + tr("rep.t1_cap", mode=width_txt) + "</caption>"
        f"<thead><tr><th>{tr('rep.th_2th')}</th><th class='num'>{tr('rep.th_d')}</th>"
        "<th class='num'>FWHM<sub>obs</sub></th><th class='num'>FWHM<sub>inst</sub></th>"
        "<th class='num'>β (°)</th><th class='num'>D (nm)</th><th class='num'>η</th>"
        "<th class='num'>R<sub>wp</sub></th>"
        f"<th>{tr('rep.th_status')}</th></tr></thead><tbody>"
        + "".join(peak_rows) + "</tbody></table>")

    # -- 平均 ------------------------------------------------------------
    avg_table = (
        '<table><caption>' + tr("rep.t2_cap") + "</caption>"
        f"<thead><tr><th>{tr('rep.t2_th1')}</th>"
        f"<th class='num'>{tr('rep.t2_th2')}</th><th>{tr('rep.t2_th3')}</th></tr></thead><tbody>"
        f"<tr><td>{tr('rep.avg_dn')}</td><td class='num'><b>{_fmt(s.mean_number, 2)}</b></td>"
        f"<td>{tr('rep.avg_dn_note')}</td></tr>"
        f"<tr><td>{tr('rep.avg_di')}</td><td class='num'>{_fmt(s.mean_intensity, 2)}</td>"
        f"<td>{tr('rep.avg_di_note')}</td></tr>"
        f"<tr><td>{tr('rep.avg_dv')}</td><td class='num'>{_fmt(s.mean_volume, 2)}</td>"
        f"<td>{tr('rep.avg_dv_note')}</td></tr>"
        f"<tr><td>{tr('rep.avg_spread')}</td><td class='num'>{_fmt(s.spread(), 1)} %</td>"
        f"<td>{tr('rep.avg_spread_note')}</td></tr>"
        "</tbody></table>")

    # -- 仪器线宽 --------------------------------------------------------
    inst_html = ""
    if inst is not None and inst.usable:
        U, V, W = inst.U, inst.V, inst.W
        Ur, Vr, Wr = inst.coefficients_rad()
        st_rows = "".join(
            f"<tr><td class='num'>{p.position:.3f}</td>"
            f"<td class='num'>{p.position_raw:.3f}</td>"
            f"<td class='num'>{p.fwhm:.4f}</td>"
            f"<td class='num'>{_fmt(inst.fwhm_at(p.position), 4)}</td>"
            f"<td class='num'>{p.fwhm - inst.fwhm_at(p.position):+.4f}</td>"
            f"<td class='num'>{p.eta:.2f}</td>"
            f"<td class='num'>{p.rwp:.1f}</td></tr>"
            for p in inst.peaks if p.ok)
        method_txt = (tr("rep.i_func_caglioti") if inst.method == "caglioti"
                      else tr("rep.i_func_pchip"))
        inst_html = f"""
<h2>{tr('rep.h3_inst')}</h2>
<dl>
  <dt>{tr('rep.i_phase')}</dt><dd>{_esc(inst.standard_name or tr('rep.i_unknown_phase'))}</dd>
  <dt>{tr('rep.i_func')}</dt><dd>{_esc(method_txt)}</dd>
  <dt>{tr('rep.i_uvw_deg')}</dt>
  <dd>{U:.4e} / {V:.4e} / {W:.4e}　<span class="grey">{tr('rep.i_r2', r2=inst.r2, rms=inst.rms)}</span></dd>
  <dt>{tr('rep.i_uvw_rad')}</dt><dd>{Ur:.4e} / {Vr:.4e} / {Wr:.4e}</dd>
  <dt>{tr('rep.i_coverage')}</dt><dd>{inst.coverage()[0]:.1f}° – {inst.coverage()[1]:.1f}°</dd>
  <dt>{tr('rep.i_note')}</dt><dd>{_esc(inst.note)}</dd>
</dl>
<table><caption>{tr('rep.t3_cap')}</caption>
<thead><tr><th class='num'>{tr('rep.t3_corr')}</th><th class='num'>{tr('rep.t3_obs')}</th>
<th class='num'>{tr('rep.t3_fobs')}</th><th class='num'>{tr('rep.t3_fmodel')}</th>
<th class='num'>{tr('rep.t3_res')}</th><th class='num'>η</th><th class='num'>R<sub>wp</sub> (%)</th></tr></thead>
<tbody>{st_rows}</tbody></table>
<p class="note">{tr('rep.i_note_txt')}</p>
"""

    # -- W-H -------------------------------------------------------------
    wh_rows = "".join(
        f"<tr><td class='num'>{p.two_theta:.3f}</td>"
        f"<td class='num'>{p.x:.4f}</td>"
        f"<td class='num'>{_fmt(p.y * 1000 if np.isfinite(p.y) else None, 4)}</td>"
        f"<td class='num'>{_fmt(p.beta_deg, 4)}</td>"
        f"<td>{'' if p.ok else tr('rep.w_not_reg')}</td></tr>"
        for p in wh.points)
    wh_img = _wh_png(bundle)
    wh_img_html = (f'<img src="data:image/png;base64,{wh_img}" alt="W-H plot">'
                   f'<div class="figcap">{tr("rep.fig2")}</div>') if wh_img else ""
    wh_html = f"""
<h2>{tr('rep.h4_wh')}</h2>
<dl>
  <dt>{tr('rep.w_fit')}</dt><dd>{tr('rep.w_fit_val', K=wh.K)}</dd>
  <dt>{tr('rep.w_d')}</dt><dd><b>{_fmt(wh.size_nm, 2)} nm</b></dd>
  <dt>{tr('rep.w_strain')}</dt><dd>{_fmt(wh.strain, 6)}（{_fmt(wh.strain_pct, 3)} %）</dd>
  <dt>{tr('rep.w_goodness')}</dt><dd>{tr('rep.w_goodness_val', r2=_fmt(wh.r2, 4), n=wh.n_valid)}</dd>
  <dt>{tr('rep.w_ref')}</dt><dd>{tr('rep.w_ref_val', mean=_fmt(wh.mean_size_nm, 2))}
      <span class="grey">{tr('rep.w_ref_note')}</span></dd>
</dl>
{wh_img_html}
<table><caption>{tr('rep.t4_cap')}</caption>
<thead><tr><th class='num'>{tr('rep.th_2th')}</th><th class='num'>4 sinθ</th>
<th class='num'>β·cosθ (×10<sup>−3</sup> rad)</th><th class='num'>β (°)</th>
<th>{tr('rep.th_status')}</th></tr></thead>
<tbody>{wh_rows}</tbody></table>
<p class="note">{tr('rep.w_note')}</p>
"""

    # -- 谱图 ------------------------------------------------------------
    spec_png = _spectrum_png(bundle)
    spec_html = (f'<img src="data:image/png;base64,{spec_png}" alt="pattern">'
                 f'<div class="figcap">{tr("rep.fig1")}</div>') if spec_png else ""

    comment_html = (f'<h2>{tr("rep.h_comment")}</h2><p>{_esc(comment)}</p>'
                    if comment.strip() else "")

    how_txt = tr("rep.how_fwhm") if s.width_mode == "fwhm" else tr("rep.how_int")
    formula = tr("rep.f_fwhm") if s.width_mode == "fwhm" else tr("rep.f_int")
    op_line = (f'　|　{tr("rep.operator")}：{_esc(operator)}' if operator else "")

    return f"""<!DOCTYPE html>
<html lang="{current_language()}"><head><meta charset="utf-8">
<title>{_esc(tr('rep.doc_title', name=name))}</title>
<style>{_STYLE}</style></head>
<body><div class="page">
<h1>{tr('rep.title')}</h1>
<div class="sub">{_esc(APP_NAME)} v{__version__}　·　{_esc(tr('about.role'))}</div>
<div class="rule"></div>
<div class="sub">{tr('rep.sample')}：<b>{_esc(name)}</b>　|　{tr('rep.report_time')}：{now}{op_line}</div>

{warns}
<div class="hero">{cards_html}</div>

<h2>{tr('rep.h1_cond')}</h2>
<dl>{cond_html}</dl>

<h2>{tr('rep.h2_scherrer')}</h2>
{spec_html}
{peak_table}
{avg_table}
<p class="note">{tr('rep.note_scherrer', how=how_txt, formula=formula)}</p>

{inst_html}
{wh_html}

<h2>{tr('rep.h5_limits')}</h2>
<h3>{tr('rep.lim1_h')}</h3>
<p>{tr('rep.lim1')}</p>
<h3>{tr('rep.lim2_h')}</h3>
<p>{tr('rep.lim2')}</p>
<h3>{tr('rep.lim3_h')}</h3>
<p>{tr('rep.lim3')}</p>
{comment_html}

<div class="foot"><span>{_esc(APP_NAME)} v{__version__}　·　{_esc(APP_COPYRIGHT)}</span>
<span>{_esc(APP_CONTACT_EMAIL)}</span></div>
<p class="note">{tr('rep.foot_note')}</p>
</div></body></html>"""
