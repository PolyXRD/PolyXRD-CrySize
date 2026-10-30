# PolyXRD CrySize

XRD 粉末衍射谱的**晶粒尺寸**与**微应变**分析工具。导入样品谱图与同条件测试的
线宽标样（Si / LaB₆）谱图，程序自动识别衍射峰、做峰形拟合、扣除仪器宽化，
再用 **Scherrer 方程**与 **Williamson-Hall 法**给出晶粒尺寸。

两个标签页对应两种方法：

| 标签 | 方法 | 输出 |
|---|---|---|
| ① 谢乐法 | D = K·λ/(β·cosθ)，逐峰计算 | 各峰 D、平均 D（三种统计口径） |
| ② Williamson-Hall | UDM / USDM / UDEDM 三变体可切换 | 截距→D、斜率→ε/σ/√u、R² |
| ③ 标样与仪器线宽 | Caglioti 分辨函数 | U/V/W、仪器线宽曲线、2θ 角度校正 |
| ④ 方法对比 | 5 组 7 种方法横向对比 | 各方法 D、次级量、R²、状态与选型说明 |

## 运行

```bash
python run.py                                  # 空界面，手动导入
python run.py 样品.txt 标样.txt                 # 直接带文件启动
python -m crysize.gui
```

依赖：Python ≥ 3.10、numpy、scipy、matplotlib、PySide6（版本锁定见 `requirements.txt`）。

界面与报告支持**三语**（简体中文 / English / 日本語），菜单「语言」运行时热切换，
选择持久化到 `%USERPROFILE%/.crysize/config.json`。漏译键以 `⟪key⟫` 直接上界面，
`tests/test_i18n.py` 在上线前拦截三语 key 集与格式占位符的不一致。

## 计算方法：5 组 7 种

侧栏「计算方法」下拉可切换主方法，标签页「方法对比」给出 7 种方法在同一组
峰拟合结果上的横向对比。完整选型说明见 [`docs/METHODS.md`](docs/METHODS.md)。

| 组 | 细分方法（7 种） | 主输出 | 次级量 | 额外输入 |
|---|---|---|---|---|
| ① 谢乐法 | FWHM 口径（K=0.89）／积分宽度口径（K=1.0） | 数目平均 D | — | 标样（可选） |
| ② W-H UDM | 均匀形变模型 | D | ε (%) | 标样（推荐） |
| ③ W-H USDM | 均匀应力模型 | D | σ (MPa) | 标样 + a、c₁₁/c₁₂/c₄₄ |
| ④ W-H UDEDM | 形变能密度模型 | D | u (MJ·m⁻³) | 同 ③ |
| ⑤ Warren-Averbach | 单峰 Voigt 近似／多级反射傅里叶法 | D（体积加权） | ⟨ε²⟩^½ | 标样；傅里叶法还要 ≥3 峰且 d 值 ≥2 种 |

「按晶向分组」是 ②③④ 共用的增强开关（按 Γ 分组后组内回归），需先填晶格
参数完成指标化；若谱里没有同族高级次，程序自动退回不分组并注明。

三条使用边界：

1. **无弹性常数时 ②③④ 退化为同一条拟合线**（σ = εE、u = ε²E/2 只是重参数
   化），界面标注「降级」。
2. **口径不可混用**：谢乐两种口径 K 不同；单峰 W-A 与傅里叶 W-A 物理含义
   不同；跨方法比数值大小没有意义。
3. **无标样时**仪器宽化被计入尺寸，结果只作相对参考。

## 两个版次

| 版次 | 产物 | 打包命令 | 版次标识 |
|---|---|---|---|
| 内部评估版 | `dist/PolyXRD-CrySize-vX.Y.Z.exe`（单文件免安装） | `build_exe.bat` | 状态栏 + 关于框标「内部评估版本」（`installer/rthook_internal.py` 运行时覆写） |
| 注册版 | `dist/PolyXRD-CrySize/PolyXRD-CrySize.exe`（onedir）+ `dist/PolyXRD-CrySize-vX.Y.Z-Setup.exe`（Inno Setup 安装包） | `build_setup.bat` | 无标识（`crysize/edition.py` 默认 `registered`） |

版次只影响标识显示，不影响任何计算功能。两个 spec 共用同一份源码与
`resources/`，差异仅在 onefile/onedir 与是否加 runtime hook。

## 使用流程

1. **导入样品谱图**：两列文本（2θ, 强度），支持 `.txt .xy .dat .csv .asc .prn .raw` 等。
   岛津/Rigaku/Bruker 的 ASCII 导出可直接读，程序会跳过表头并提取靶材、步长、扫描范围。
2. **导入标样谱图**：与样品**同一天、同一狭缝、同一扫描速度**测的 Si 或 LaB₆。
   这是仪器宽化校正的前提 —— 换狭缝、换靶、改计数时间后必须重测。
3. 程序自动选强峰、拟合、计算。左侧峰表可勾选/取消峰，取消后自动重算。
4. **导出报告**（自包含 HTML，浏览器打开可打印为 PDF）或 **CSV**。

## 关键约定（影响数值，务必了解）

**1. 宽度口径与 K 值**

- Scherrer 用 **FWHM**，K = 0.89（球形晶体）
- W-H 用 **积分宽度 β_int**，K = 1.0

依据：W-H 关系由积分宽度推导；且积分宽度在卷积下可加和（Stokes, Proc. Phys.
Soc. A 61 (1948) 382），而 FWHM 不可加和。两者混用会引入 5%–20% 系统偏差。
界面里切换口径会同步 K 的默认值，也可手动改。

**2. 仪器宽化扣除**

- FWHM 口径：β = √(FWHM_obs² − FWHM_inst²)
- 积分宽度口径：β = β_obs − β_inst

仪器分辨函数用 Caglioti 形式 FWHM² = U·tan²θ + V·tanθ + W（Caglioti et al.,
Nucl. Instr. 3 (1958) 223），由标样峰拟合得到；峰数不足或拟合质量差时自动退回
实测点 PCHIP 插值，并在界面上注明实际用的是哪一种。

**3. 2θ 角度校正**

由标样实测峰位与 Si/LaB₆ 理论峰位（a_Si = 5.431194 Å，a_LaB₆ = 4.156826 Å）
比较，自动校正零位偏移；偏差随 2θ 变化时追加 cosθ 项。校正后 Si 峰位残差通常
在 0.005° 以内，d 值可直接与 PDF 卡片比对。

**4. 选峰原则**

选 **3–6 个孤立、无重叠、2θ 分布尽量宽**的强峰，而不是简单取最强峰：

- 重叠峰的 FWHM 会被邻峰污染（本程序在窗口内做多峰联合拟合来缓解，但重叠严重时
  仍会给出不可靠宽度，此时该峰会被标记并从统计中剔除）
- W-H 需要尽量多、角度跨度大的峰（建议 ≥5 个、跨度 ≥60°），否则拟合自由度不足

**5. 没有标样时**

程序照常计算，但结果会标注"未做仪器宽化校正"：这些 D 是**含仪器展宽的表观值，
系统性偏小**，只能用于同仪器、同条件的样品之间相对比较。报告中以醒目警告条提示。

## 可靠量程

| 晶粒尺寸 | 可靠性 |
|---|---|
| 2–100 nm | 主要适用区 |
| 100–200 nm | 边缘，β 由两个相近宽度相减，不确定度急剧放大 |
| > 200 nm | 失效（仪器宽化 ≥ 观测宽化，程序会标记并从平均中排除） |

W-H 法还假设宽化各向同性、应变均匀。若样品各向异性明显（片状/针状晶、层错），
W-H 图会偏离直线，R² 显著下降，程序会给出提示。

## 输出

- **HTML 报告**：结论卡片、测量条件、各峰峰宽与 D、三种平均口径、仪器线宽系数
  U/V/W（度² 与 rad² 两种单位）、W-H 图与数据点、方法与局限说明
- **CSV**：峰表 + 汇总值，便于批量汇总

## 测试

```bash
python -m pytest tests -q                       # 12 项核心算法测试
python tools/smoke_gui.py 样品.txt 标样.txt      # GUI 冒烟：3 个标签页 + 两个对话框截图 + 出报告
python tools/shot_report.py _smoke/report.html   # 把 HTML 报告整页渲染成 PNG，复核版式
```

测试用**正演-反演闭环**验证数学正确性：按谢乐方程生成已知晶粒尺寸的合成谱，
再让程序反演，检查能否还原真值（20 nm、50 nm、无应变与含应变算例）。这条路径
曾抓出两处真实缺陷：W-H 微应变被多除了一个 4（横轴已取 4sinθ）、以及"无标样时
D 偏大"的方向写反 —— 说明闭环测试不是形式，是唯一的正确性判据。

> GUI 冒烟与报告截图需要图形会话（`QT_QPA_PLATFORM=windows`）；纯离屏模式
> 渲染不出中文字形，会得到一排"豆腐块"。

## 家族约定（PolyXRD）

本工具是 PolyXRD 家族的一员（项目根 `D:\Project\XRD`），视觉与工程约定与家族
其它工具一致，改任何一处都要与兄弟项目对齐：

| 项目 | 约定 |
|---|---|
| 视觉标识 | 白色正六边形 + 工具专属图形（此处为逐渐变宽的衍射峰与 FWHM 标注），品牌深色 `#0F172A` → 品牌蓝 `#0284C7` 斜向渐变，子工具强调色青 `#22D3EE` |
| 启动画面 | `resources/splash-screen.png`（480×270），打包态由 PyInstaller `Splash` 在解包阶段先显示，主窗口 `show()` 后 `pyi_splash.close()` 交接；关闭定时器**必须**在 `show()` 之后挂，否则冷启动会闪退 |
| 图标 | 窗口用 PNG（Qt6 内建解码，不加载 `qico.dll` 插件），`.ico` 只给 exe 资源与安装器 |
| 风格 | Fusion 样式 + 局部内联样式 + `gui/theme.py` 统一配色，不用全局 QSS |
| 字体 | Microsoft YaHei 9 pt |
| i18n | `crysize/i18n/`（manager + 三语翻译表），接口与 RutAna 完全一致（`tr()` 缺键返回 `⟪key⟫` 不回退）；core 层警告/质量标记也经 `tr()` 生成，语言切换后主窗口自动重算刷新 |
| 版次 | `crysize/edition.py`：`registered`（安装包）或 `internal`（单文件 exe，状态栏标"内部评估版本"，由 `installer/rthook_internal.py` 覆写） |
| 打包 | `build_exe.bat` → 单文件内部评估版；`build_setup.bat` → onedir + Inno Setup 注册版安装包 |
| 许可 | 双许可：学术（非商业研究与教学）免费；商业用途须取得书面授权。条款见 `LICENSE` / `LICENSE-CN` |
| 联系 | sshztx@outlook.com · https://github.com/PolyXRD |

品牌图片由 `tools/build_artwork.py`（Pillow）生成，改配色或图形只需改这一个文件
再跑一次，避免图标、启动图、logo、报告三处色差。

## 目录

```
crysize/
  version.py      版本与产品标识（家族统一字段）
  edition.py      版次标识（registered / internal）
  i18n/           三语基础设施（manager + translations/zh_CN,en_US,ja_JP）
  core/
    pattern.py     谱图读取（表头跳过、元数据提取、降序翻转）
    elasticity.py  立方晶系 hkl 指标化与方向杨氏模量 E(hkl)（USDM/UDEDM 用）
    wh_models.py   W-H 三变体 UDM / USDM / UDEDM + 按 Γ 分组
    warren.py      Warren-Averbach：单峰 Voigt 近似 + 多级反射傅里叶法
    methods.py     5 组 7 种方法的注册表、统一结果与选型说明入口
    peaks.py       峰搜索与自动选峰
    profile.py     pseudo-Voigt 拟合（局部多峰、Kα₂ 剥离、质量标记）
    instrument.py  仪器分辨函数（Caglioti / PCHIP）
    standards.py   Si / LaB₆ 参考数据与角度校正
    size.py        Scherrer 与 W-H 计算
    analysis.py    编排层
  gui/
    __main__.py    入口（启动图 → 主窗口 → 关闭启动图）
    main_window.py 主窗口、参数面板、峰表、语言菜单
    canvas.py      谱图/W-H/线宽曲线画布
    report.py      HTML 报告（语言跟随界面）
    dialogs.py     关于 / 版权与许可
    theme.py       家族配色与字体常量
    resources.py   资源定位（开发态 / sys._MEIPASS）
resources/         品牌资产（build_artwork.py 生成）
installer/         Inno Setup 脚本、中文语言文件、内部版 runtime hook
tools/             build_artwork.py、smoke_gui.py、shot_report.py
tests/             test_core.py（算法闭环）+ test_i18n.py（三语一致性）
                   + test_methods.py（弹性/指标化、三变体、Warren-Averbach）
docs/              METHODS.md（5 组 7 种方法的选择场景与文献依据）
pyproject.toml     打包元数据（双许可 LicenseRef、版本单一来源、pytest/ruff 配置）
PolyXRD-CrySize.spec / PolyXRD-CrySize-Setup.spec   PyInstaller 内部版 / 注册版
build_exe.bat / build_setup.bat                    一键打包脚本
```

> `pip install -e .` 需要 setuptools ≥ 77（PEP 639 的 `license` / `license-files`
> 字段），与家族主程序 `PolyXRD/pyproject.toml` 同一写法；日常开发直接
> `python run.py` 不需要安装。

## 参考

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

## 许可与联系

© 2026 PolyXRD Team · 版权所有

本软件按**双许可**发布：

- **学术许可**：仅限非商业学术研究与教学，免费；可自由使用、复制、修改、分发，
  不允许任何商业用途。
- **商业许可**：商用前须联系版权持有人取得书面授权。

完整条款见 `LICENSE`（英文）与 `LICENSE-CN`（中文）。商业授权与技术支持：
sshztx@outlook.com。
