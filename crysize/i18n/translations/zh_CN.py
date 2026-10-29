"""简体中文（源语言）：所有 key 以本表为准，en_US / ja_JP 与之对齐。

约定：
- 数值格式化占位符（``{K:.2f}`` 等）在各语言间必须一致，只改文字不动格式；
- HTML 片段（<b>/<br>/<sub> 等）原样保留，翻译时不得增删标签；
- 图例/表头等短文案保持简短，避免撑破布局。
"""

TRANSLATIONS = {
    # ------------------------------------------------------------------ #
    # 窗口与菜单
    # ------------------------------------------------------------------ #
    "win.title": "晶粒尺寸与微应变分析",
    "menu.file": "文件(&F)",
    "menu.help": "帮助(&H)",
    "menu.language": "语言(&G)",
    "menu.open_sample": "导入样品谱图…",
    "menu.open_standard": "导入标样谱图…",
    "menu.export_html": "导出 HTML 报告…",
    "menu.export_csv": "导出 CSV…",
    "menu.exit": "退出",
    "menu.method": "方法说明",
    "menu.copyright": "版权与许可",
    "menu.about": "关于 {name}",

    # ------------------------------------------------------------------ #
    # 顶部文件行 / 按钮
    # ------------------------------------------------------------------ #
    "btn.sample": "导入样品谱图…",
    "btn.standard": "导入标样谱图…",
    "btn.clear_std": "清除标样",
    "btn.recalc": "重新计算",
    "btn.report": "导出报告",
    "btn.csv": "导出 CSV",
    "lbl.sample_none": "样品：未导入",
    "lbl.std_none": "标样：未导入",
    "lbl.sample_info": "样品：{label}（{n} 点，{lo:.1f}–{hi:.1f}°，λ={wl:.4f} Å）",
    "lbl.std_info": "标样：{label}（{n} 点）",

    # ------------------------------------------------------------------ #
    # 参数面板
    # ------------------------------------------------------------------ #
    "group.params": "分析参数",
    "group.corr": "角度校正（来自标样）",
    "group.peaks": "参与计算的峰（可勾选）",
    "param.n_peaks": "参与计算的峰数",
    "param.width_mode": "谢乐法宽度口径",
    "param.K": "形状因子 K",
    "param.window": "拟合窗上限",
    "param.prominence": "峰识别阈值",
    "suffix.peaks": " 个",
    "mode.fwhm": "FWHM（K = 0.89）",
    "mode.integral": "积分宽度 β_int（K = 1.0）",
    "param.ka2": "拟合时剥离 Kα₂（推荐）",
    "param.ka2_tip": "未单色化光路下，Kα₂ 卫星峰会让高角峰宽化虚增 10–20%",
    "param.prom_tip": "低于该相对突出度的峰不参与自动选峰",
    "corr.lbl_none": "未导入标样",
    "corr.lbl_none_full": "未导入标样：未做角度与仪器宽化校正",

    # ------------------------------------------------------------------ #
    # 标签页 / 峰表
    # ------------------------------------------------------------------ #
    "tab.scherrer": "① 谢乐法 Scherrer",
    "tab.wh": "② Williamson-Hall",
    "tab.inst": "③ 标样与仪器线宽",
    "th.note": "备注",
    "note.instrument_exceeds": "仪器宽化≥观测",
    "note.unreliable": "拟合欠佳",
    "note.no_std": "未校正",

    # ------------------------------------------------------------------ #
    # 对话框 / 消息 / 状态栏
    # ------------------------------------------------------------------ #
    "filter.patterns": "衍射谱图 ({exts})",
    "filter.all": "所有文件 (*.*)",
    "dlg.choose_sample": "选择样品谱图",
    "dlg.choose_standard": "选择标样谱图（Si 或 LaB₆）",
    "dlg.read_fail": "读取失败",
    "dlg.calc_fail": "计算失败",
    "dlg.refit_fail": "重算失败",
    "dlg.info": "提示",
    "dlg.need_compute": "请先导入样品谱图并完成计算。",
    "dlg.save_html": "保存 HTML 报告",
    "dlg.save_csv": "导出 CSV",
    "dlg.export_fail": "导出失败",
    "dlg.export_done": "导出完成",
    "dlg.open_now": "报告已保存，是否立即打开？",
    "dlg.std_loaded": "标样已加载，请再导入样品谱图",
    "dlg.min_peaks": "至少勾选 2 个峰",
    "dlg.ok": "确定",
    "edition.internal": "内部评估版本",
    "about.role": "粉末衍射峰宽分析工具：谢乐法与 Williamson-Hall 法晶粒尺寸、微应变计算",
    "about.contact": "联系方式 / Contact",
    "about.chip1": "谢乐法逐峰",
    "about.chip2": "Williamson-Hall",
    "about.chip3": "标样宽化校正",
    "about.title": "关于 {name}",
    "copyright.title": "版权与许可",
    "status.ready": "就绪：请导入样品谱图（两列文本：2θ, 强度）",
    "status.done": "计算完成：有效峰 {valid}/{total}，平均晶粒尺寸 {mean} nm{extra}",
    "status.uncorrected": "（未做仪器校正）",
    "fname.report": "{label}_晶粒尺寸报告.html",
    "fname.csv": "{label}_晶粒尺寸.csv",

    # ------------------------------------------------------------------ #
    # 三个页签的结论面板（HTML 富文本）
    # ------------------------------------------------------------------ #
    "sum.no_warn": "✓ 未发现明显异常",
    "sum.scherrer.head": "平均晶粒尺寸（数目平均，{total} 峰中有效 {valid} 峰）",
    "sum.scherrer.stats": "强度加权 {di} nm　体积加权 {dv} nm　离散度 {sp}%",
    "sum.scherrer.model": "模型：pseudo-Voigt，{mode}口径，K = {K:.2f}，λ = {wl:.5f} Å，{corr}",
    "sum.mode.fwhm": "FWHM",
    "sum.mode.integral": "积分宽度",
    "sum.corr.done": "已扣除仪器宽化",
    "sum.corr.none": "未扣除仪器宽化",
    "sum.wh.head": "Williamson-Hall 线性拟合（β·cosθ = Kλ/D + 4ε·sinθ）",
    "sum.wh.stats": "微应变 ε = {e} %　R² = {r2}　有效点 {n}",
    "sum.wh.detail": "斜率 ε = {slope}，截距 Kλ/D = {intercept} rad，各峰按积分宽度单独算得平均 {mean} nm",
    "sum.wh.note": "（与谢乐标签的 FWHM 口径不同，两处数值不可直接对比）",
    "sum.inst.head": "仪器分辨函数（标样：{name}）",
    "sum.inst.unknown": "未识别",
    "sum.inst.caglioti": "Caglioti  U·tan²θ + V·tanθ + W",
    "sum.inst.pchip": "PCHIP 插值（实测点）",
    "sum.inst.coef": "　U = {u}，V = {v}，W = {w}　（度²，R² = {r2}，RMS = {rms}°）",
    "sum.inst.corr": "角度校正：{desc}",
    "sum.inst.th_corr": "2θ 校正后",
    "sum.inst.th_obs": "2θ 实测",
    "sum.inst.th_fwhm_obs": "FWHM 实测",
    "sum.inst.th_fwhm_model": "FWHM 模型",
    "sum.inst.empty": "未导入标样谱图。<br>导入与样品同条件测试的 Si 或 LaB₆ 谱图后，此处显示"
                      "仪器分辨函数 U/V/W、仪器线宽曲线与角度校正参数。",

    # ------------------------------------------------------------------ #
    # 画布（matplotlib）
    # ------------------------------------------------------------------ #
    "cv.empty": "导入样品谱图后显示",
    "cv.std_empty": "未导入标样",
    "cv.intensity": "强度 (counts)",
    "cv.full_title": "样品衍射谱与参与计算的峰",
    "cv.obs": "观测",
    "cv.fit": "总拟合",
    "cv.bg": "背景",
    "cv.comp": "峰分量",
    "cv.zoom_title": "峰拟合放大：2θ = {tt:.3f}°，η = {eta:.2f}，Rwp = {rwp:.1f}%",
    "cv.beta_corr": "，扣仪器宽化后 β = {beta:.3f}°",
    "cv.wh_points": "参与拟合的峰",
    "cv.wh_fit": "线性拟合",
    "cv.wh_intercept": "截距 {xi:.3f}",
    "cv.wh_to_size": " rad → D = {d:.1f} nm",
    "cv.excluded": "已剔除：{peaks}（拟合质量不足）",
    "cv.std_meas": "标样实测 FWHM",
    "cv.std_model": "模型（{m}）",
    "cv.model_caglioti": "Caglioti U/V/W",
    "cv.model_pchip": "PCHIP 插值",
    "cv.std_title": "仪器线宽曲线",
    "cv.y_instr": "仪器 FWHM (°)",

    # ------------------------------------------------------------------ #
    # 方法说明对话框
    # ------------------------------------------------------------------ #
    "method.title": "方法说明",
    "method.body": """
<b>谢乐法</b><br>
D = K·λ/(β·cosθ)。β 为扣除仪器宽化后的纯物理宽化（弧度），K 为形状因子：
用 FWHM 时 K≈0.89（球形晶体），用积分宽度时 K=1.0。<br><br>

<b>仪器宽化校正</b><br>
导入与样品同条件测试的 Si 或 LaB₆ 标样，程序拟合标样各峰得到仪器分辨函数
（Caglioti: FWHM² = U·tan²θ + V·tanθ + W），再在样品峰位处扣除：<br>
· FWHM 口径：β = √(FWHM_obs² − FWHM_inst²)<br>
· 积分宽度口径：β = β_obs − β_inst（积分宽度可加和，更严格）<br><br>

<b>Williamson-Hall</b><br>
β·cosθ = K·λ/D + 4·ε·sinθ。以 4sinθ 为横轴、β·cosθ 为纵轴线性拟合，
截距给出 D，斜率给出微应变 ε。β 用积分宽度、K=1。<br><br>

<b>选峰原则</b><br>
选 3–6 个孤立、无重叠、2θ 分布尽量宽的强峰；重叠峰会拟出偏大的 FWHM，
使 D 偏小。W-H 法需要尽量多且角度跨度大的峰（建议 ≥5 个、跨度 ≥60°）。
""",

    # ------------------------------------------------------------------ #
    # core：峰拟合质量标记（profile.py）
    # ------------------------------------------------------------------ #
    "pf.not_converged": "拟合未收敛",
    "pf.eta_lorentz": "峰形近纯洛伦兹（η→1），可能有未分离的重叠峰",
    "pf.eta_gauss": "峰形近纯高斯（η→0）",
    "pf.rwp_high": "拟合残差偏高（Rwp={v:.1f}%）",
    "pf.fwhm_err": "峰宽不确定度偏大",
    "pf.neighbors": "窗口内含 {n} 个邻峰，已联合拟合",
    "pf.no_points": "窗口内数据点不足",
    "pf.fit_error": "拟合异常：{exc}",

    # ------------------------------------------------------------------ #
    # core：Scherrer / W-H 警告（size.py）
    # ------------------------------------------------------------------ #
    "w.no_standard": "未导入标样谱图（Si 或 LaB₆），结果未做仪器宽化校正：下列晶粒尺寸是含仪器展宽的"
                     "表观值，因为把仪器宽化也算进了物相宽化，D 系统性偏小（晶粒越粗、仪器线宽越宽，"
                     "偏低越严重）。此类数值只能用于同仪器、同狭缝条件下的样品之间相对比较，"
                     "不宜作为绝对晶粒尺寸报告或与文献值直接对比。",
    "w.n_exceed": "{n} 个峰的仪器宽化 ≥ 观测宽化，无法解出物理宽化（该方向晶粒过大，"
                  "或标样线宽偏宽），已从平均值中排除。",
    "w.all_exceed": "所有峰的物理宽化都无法解出：峰宽几乎全由仪器决定，说明晶粒尺寸已超出峰宽法"
                    "的可靠量程（约 100–200 nm 以上）。此时应改用 SEM/TEM 观察，或延长计数时间、"
                    "减小狭缝以降低仪器宽化。",
    "w.too_large": "部分峰的晶粒尺寸 > 150 nm，已接近峰宽法量程上限（β 由两个相近的宽度相减得到，"
                   "相对不确定度被放大），数值仅供参考。",
    "w.spread": "各峰晶粒尺寸离散度较大（{sp:.0f}%），可能存在择优取向、"
                "层错/孪晶或各向异性形貌；建议结合 W-H 图判断应变贡献。",
    "w.doubtful": "{pos} 的峰拟合质量欠佳（残差偏高或峰形撞边界，常见于重叠峰），"
                  "建议在峰表中取消这些峰或换用孤立峰后重算。",
    "w.wh_dropped": "{tt:.2f}° 的峰拟合质量不足，已从 W-H 回归中剔除。",
    "w.wh_too_few": "可用于 W-H 拟合的峰不足 2 个，无法做线性回归。",
    "w.wh_neg_intercept": "W-H 截距为负（< 0），无法给出有物理意义的晶粒尺寸：通常意味着全部宽化"
                          "被拟合为微应变、或仪器宽化校正不足/过度，请检查标样与峰宽。",
    "w.wh_few_peaks": "W-H 仅使用 {n} 个峰，拟合自由度很低，结果仅供参考。",
    "w.wh_neg_slope": "W-H 斜率为负（微应变为负），通常说明数据分散或校正不当，"
                      "不能按常规解读为压缩应变。",
    "w.wh_low_r2": "W-H 拟合 R² = {r2:.2f} 偏低，尺寸-应变两参数模型"
                   "可能不适用于该样品（存在各向异性宽化/层错时常见）。",
    "w.wh_no_standard": "W-H 法同样未做仪器宽化校正：截距（Kλ/D）被仪器展宽抬高，D 因而偏小；"
                        "斜率（应变项）也混入了仪器线宽随 2θ 的增长趋势，拟合出的微应变不宜直接引用。",

    # ------------------------------------------------------------------ #
    # core：仪器模型备注（instrument.py）
    # ------------------------------------------------------------------ #
    "inst.no_peaks": "标样谱中未拟合出可用峰，仪器校正不可用。",
    "inst.zero_fixed": "用户指定零位偏移 {v:+.4f}°",
    "inst.no_quality": "标样峰拟合均未通过质量检查，仪器校正不可用。",
    "inst.caglioti_ok": "Caglioti 拟合自 {n} 个标样峰",
    "inst.caglioti_fallback": "Caglioti 拟合质量不足（R²={r2:.2f}，物理性检查{phy}），退回 PCHIP 插值",
    "inst.phy_ok": "通过",
    "inst.phy_fail": "未通过",
    "inst.caglioti_error": "Caglioti 拟合失败（{exc}），退回 PCHIP 插值",
    "inst.few_peaks": "标样可用峰仅 {n} 个（<{m} 或跨度不足），采用 PCHIP 插值",

    # ------------------------------------------------------------------ #
    # core：角度校正（standards.py）
    # ------------------------------------------------------------------ #
    "corr.not_applied": "未做角度校正",
    "corr.desc.zero": "仅校正常数零位偏移 Δ0 = {v:+.4f}°",
    "corr.desc.zero_disp": "Δ2θ = Δ0 + k·cosθ，Δ0 = {d0:+.4f}°，k = {k:+.4f}°（残差 RMS {rms:.4f}°）",
    "corr.no_match": "标样峰位无法匹配 Si/LaB₆ 理论峰位，未做角度校正。",
    "corr.match2": "以 {name}（a = {a:.6f} Å）匹配 {n} 个反射，Δ2θ = Δ0 + k·cosθ 拟合残差 RMS = {rms:.4f}°",
    "corr.match1": "以 {name} 匹配 {n} 个反射，偏差一致（RMS {rms:.4f}°），仅校正常数零位偏移 {shift:+.4f}°",

    # ------------------------------------------------------------------ #
    # core：谱图读取 / 编排异常（pattern.py / analysis.py）
    # ------------------------------------------------------------------ #
    "pat.len_mismatch": "2θ 与强度长度不一致",
    "pat.too_few": "数据点过少（<10），无法分析",
    "pat.no_data": "未找到连续的两列数值数据（至少需要 10 行）",
    "ana.no_peaks": "样品谱中未找到可用衍射峰，请检查数据或降低峰识别阈值。",
    "ana.window": "峰拟合失败：拟合窗口内数据点不足，请检查步长与数据范围。",

    # ------------------------------------------------------------------ #
    # CSV 导出
    # ------------------------------------------------------------------ #
    "csv.h_2th": "2θ(°)", "csv.h_d": "d(Å)", "csv.h_fwhm_obs": "FWHM_obs(°)",
    "csv.h_fwhm_inst": "FWHM_inst(°)", "csv.h_beta": "β(°)", "csv.h_D": "D(nm)",
    "csv.h_eta": "η", "csv.h_rwp": "Rwp(%)", "csv.h_status": "状态",
    "csv.h_quality": "质量标记",
    "csv.ok": "有效",
    "csv.mean_n": "数目平均(nm)", "csv.mean_i": "强度加权(nm)",
    "csv.mean_v": "体积加权(nm)", "csv.spread": "离散度(%)",
    "csv.wh_d": "W-H D(nm)", "csv.wh_strain": "W-H 微应变(%)", "csv.wh_r2": "W-H R²",
    "csv.instr_corr": "仪器校正", "csv.corrected": "已校正", "csv.uncorrected": "未校正",

    # ------------------------------------------------------------------ #
    # HTML 报告
    # ------------------------------------------------------------------ #
    "rep.title": "XRD 晶粒尺寸分析报告",
    "rep.doc_title": "{name} — 晶粒尺寸分析报告",
    "rep.unnamed": "未命名样品",
    "rep.sample": "样品",
    "rep.report_time": "报告时间",
    "rep.operator": "分析人",
    "rep.h1_cond": "一、测量与计算条件",
    "rep.h2_scherrer": "二、各峰晶粒尺寸（Scherrer 法）",
    "rep.h3_inst": "三、仪器宽化与线宽系数",
    "rep.h4_wh": "四、Williamson-Hall 法",
    "rep.h5_limits": "五、方法与局限",
    "rep.h_comment": "备注",

    "rep.card_dn": "平均晶粒尺寸 D<sub>n</sub>",
    "rep.card_nvalid": "有效峰数",
    "rep.card_wh": "W-H 晶粒尺寸",
    "rep.card_strain": "微应变 ε",

    "rep.c_sample": "样品",
    "rep.c_file": "数据文件",
    "rep.c_target": "靶材 / 波长",
    "rep.c_range": "扫描范围",
    "rep.c_points": "数据点数",
    "rep.c_model": "峰形模型",
    "rep.c_model_ka2": "，含 Kα₂ 分量",
    "rep.c_npeaks": "参与计算的峰数",
    "rep.c_npeaks_note": "（自动选强峰后可手动增删）",
    "rep.c_width": "宽度口径",
    "rep.c_std": "标样谱图",
    "rep.c_std_id": "标样识别",
    "rep.c_angcorr": "2θ 角度校正",
    "rep.c_std_none": "未导入",
    "rep.c_std_unknown": "未识别",
    "rep.c_range_val": "{lo:.2f}° – {hi:.2f}°，步长 {st:.4f}°",
    "rep.c_target_val": "{anode} Kα₁，λ = {wl:.7f} Å",
    "rep.width_fwhm": "FWHM",
    "rep.width_int": "积分宽度 β_int",

    "rep.t1_cap": "表 1　各衍射峰的峰宽与 Scherrer 晶粒尺寸（{mode} 口径；宽度单位 °，R<sub>wp</sub> 单位 %）",
    "rep.th_2th": "2θ (°)",
    "rep.th_d": "d (Å)",
    "rep.th_status": "状态",

    "rep.t2_cap": "表 2　平均晶粒尺寸的三种统计口径",
    "rep.t2_th1": "统计方式",
    "rep.t2_th2": "数值 (nm)",
    "rep.t2_th3": "说明",
    "rep.avg_dn": "数目平均 D<sub>n</sub>",
    "rep.avg_dn_note": "各峰等权算术平均，最常用",
    "rep.avg_di": "强度加权 D<sub>I</sub>",
    "rep.avg_di_note": "按峰净高加权，强峰主导",
    "rep.avg_dv": "体积加权 D<sub>v</sub>",
    "rep.avg_dv_note": "Σ(I·D⁴)/Σ(I·D³)，与比表面积对应",
    "rep.avg_spread": "离散度",
    "rep.avg_spread_note": "各峰 D 的标准差/均值，反映各向异性",

    "rep.note_scherrer": "Scherrer 方程 D = K·λ/(β·cosθ)。β 为扣除仪器宽化后的纯物理宽化：本报告按{how}处理"
                         "（{formula}）。D 为垂直于该衍射面方向的相干散射柱长，不等于颗粒直径；对球形颗粒，"
                         "D 通常约为直径的下限估计。",
    "rep.how_fwhm": "FWHM 平方差",
    "rep.how_int": "积分宽度直接相减",
    "rep.f_fwhm": "β = √(FWHM_obs² − FWHM_inst²)",
    "rep.f_int": "β = β_obs − β_inst",

    "rep.i_phase": "标样物相",
    "rep.i_unknown_phase": "未识别物相",
    "rep.i_func": "分辨函数",
    "rep.i_func_caglioti": "Caglioti 多项式 FWHM² = U·tan²θ + V·tanθ + W",
    "rep.i_func_pchip": "实测点 PCHIP 插值",
    "rep.i_uvw_deg": "U / V / W（度²）",
    "rep.i_uvw_rad": "U / V / W（rad²）",
    "rep.i_r2": "R² = {r2:.3f}，RMS = {rms:.4f}°",
    "rep.i_coverage": "标样峰覆盖",
    "rep.i_note": "备注",
    "rep.t3_cap": "表 3　标样各峰的实测峰宽与分辨函数值",
    "rep.t3_corr": "2θ<sub>校正后</sub>",
    "rep.t3_obs": "2θ<sub>实测</sub>",
    "rep.t3_fobs": "FWHM<sub>实测</sub> (°)",
    "rep.t3_fmodel": "FWHM<sub>模型</sub> (°)",
    "rep.t3_res": "残差 (°)",
    "rep.i_note_txt": "U/V/W 为 Cu 靶、上述狭缝与扫描速度下的实测分辨函数，仅对本次同条件测量有效；"
                      "更换狭缝、靶材、计数时间后须重测标样。表格中“2θ 校正后”指经角度校正（零位偏移与"
                      "cosθ 项）后的峰位。",

    "rep.w_fit": "拟合式",
    "rep.w_fit_val": "β·cosθ = K·λ/D + 4·ε·sinθ，β 取积分宽度，K = {K:.2f}",
    "rep.w_d": "晶粒尺寸 D",
    "rep.w_strain": "微应变 ε",
    "rep.w_goodness": "拟合优度",
    "rep.w_goodness_val": "R² = {r2}，有效点 {n} 个",
    "rep.w_ref": "对照",
    "rep.w_ref_val": "各峰按积分宽度单独算得平均 {mean} nm",
    "rep.w_ref_note": "（K = 1，与 W-H 同一口径；W-H 分离应变后通常大于该值。注意此值"
                      "与第二节谢乐法的 FWHM/K = 0.89 口径不同，两者不可直接对比）",
    "rep.t4_cap": "表 4　W-H 图数据点",
    "rep.w_not_reg": "未参与回归",
    "rep.w_note": "W-H 法要求峰宽随 2θ 单调变化。若峰宽出现非单调（各向异性宽化、层错、"
                  "择优取向），单一直线模型不成立，R² 会显著降低，此时应改用各向异性模型或按晶向分别分析。"
                  "有效点少于 4 个时结果仅供参考。",

    "rep.fig1": "图 1　样品衍射谱与参与计算峰（红色为拟合曲线，阴影为拟合区间）",
    "rep.fig2": "图 2　Williamson-Hall 图：纵轴截距给出晶粒尺寸，斜率给出微应变",
    "rep.wp_points": "参与拟合的峰",
    "rep.wp_fit": "线性拟合",

    "rep.st_unreliable": "拟合欠佳",
    "rep.st_insexceed": "宽化不可解",
    "rep.st_nostd": "未校正",

    "rep.lim1_h": "1. 取值口径",
    "rep.lim1": "Scherrer 法用 FWHM 与 K = 0.89（球形晶体）；W-H 法用积分宽度与 K = 1，因为"
                "W-H 关系由积分宽度推导，且积分宽度在卷积下可加和（Stokes, 1948），而 FWHM 不可加和。"
                "两者混用会引入 5%–20% 的系统偏差。",
    "rep.lim2_h": "2. 可靠量程",
    "rep.lim2": "峰宽法对 2–100 nm 敏感；当晶粒大于约 100–200 nm 时，β 由两个相近的宽度相减得到，"
                "相对不确定度急剧放大，结果失去意义（本报告会在出现此类峰时标注）。小于 2 nm 时"
                "需考虑原子层数效应与 Debye  Waller 因子，Scherrer 方程不再严格成立。",
    "rep.lim3_h": "3. 未纳入的因素",
    "rep.lim3": "本报告未分离层错、孪晶、位错引起的宽化，也未做择优取向与各向异性宽化建模；"
                "W-H 法假设宽化各向同性、应变均匀。若样品存在明显各向异性（如片状、针状晶），"
                "W-H 图会偏离直线，此时应改用各向异性模型（如 Warren-Averbach 或按晶向分组）。",

    "rep.foot_note": "本报告由上述软件生成。软件按双许可发布：学术许可仅限非商业学术研究与教学，"
                     "商业使用须另行取得书面授权（详见随附 LICENSE / LICENSE-CN）。引用本报告的算法时应注明"
                     "Scherrer 方程与 Williamson-Hall 法的原始文献。",
}
