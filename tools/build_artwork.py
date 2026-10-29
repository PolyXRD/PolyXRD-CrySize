"""PolyXRD CrySize 品牌资产生成器
=================================
参照 PolyXRD 家族的视觉血统（Pillow 纯代码绘制，可复现、颜色精确）。

设计血统（与家族严格一致）
--------------------------
- 品牌深色 #0F172A (slate-950) → 品牌蓝 #0284C7 (sky-600) 对角线渐变
- 家族符号 = 「白色正六边形」
- 子工具强调色 = 青色 #22D3EE

本工具的 motif
--------------
六边形内画**一条衍射谱线 + 三个宽度递增的峰**，并在左峰上标出 FWHM 的双箭头。
家族里 RutAna 画两个四方晶胞、LFP 画正交晶胞 + 三强线，都是从工具本身的分析
对象里取符号；CrySize 分析的正是"峰有多宽"，所以直接画峰宽本身：
三个峰由窄到宽，箭头量出半高宽 —— 图标即说明了"峰宽 → 晶粒尺寸"这件事。

产出（写入 <root>/resources/）
------------------------------
- app-icon.png        256×256   运行时窗口图标
- app-icon@2x.png     512×512   高分屏备份
- app-icon.ico        多分辨率  给 exe 资源使用
- crystal-mark.png    256×256   透明底深色 mark（浅色背景用）
- logo-horizontal.png 512×160   横向 logo：mark + 「PolyXRD CrySize」
- splash-screen.png   480×270   启动图（深色底 + logo + 版本 + tagline）
- hero-banner.png     1600×600  About 页头图

使用：
    python tools/build_artwork.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crysize.version import APP_TAGLINE, __version__  # noqa: E402

RES_DIR = ROOT / "resources"

# --------------------------------------------------------------------------- #
# 品牌常量（家族色，严格一致）
# --------------------------------------------------------------------------- #
BRAND_DARK = (15, 23, 42)        # #0F172A  slate-950
BRAND_BLUE = (2, 132, 199)       # #0284C7  sky-600
WHITE = (255, 255, 255)
SOFT = (226, 232, 240)           # #E2E8F0  slate-200
SLATE = (100, 116, 139)          # #64748B  slate-500
CYAN = (34, 211, 238)            # #22D3EE  子工具强调色
CYAN_LIGHT = (125, 211, 252)     # #7DD3FC
CYAN_DARK = (8, 145, 178)        # #0891B2  浅色背景上的青色词标

# 启动图 / 横幅的深空背景（与家族 splash 的墨青基调一致）
BG_INNER = (12, 48, 70)
BG_OUTER = (5, 12, 24)

FONT_BOLD = r"C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = r"C:/Windows/Fonts/seguisb.ttf"
FONT_CN = r"C:/Windows/Fonts/msyh.ttc"

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]

#: 三个峰的相对位置 / 高度 / 半高宽（以谱线区宽度为归一化单位）
#: 由窄到宽，直接表达"峰宽"这一分析对象；半高宽刻意取大一些，
#: 保证 32×32 的小图标上 FWHM 箭头仍然可辨
PEAKS = (
    (0.320, 0.300, 0.072),
    (0.500, 0.205, 0.105),
    (0.680, 0.132, 0.150),
)


# --------------------------------------------------------------------------- #
# 基础几何 / 绘制工具
# --------------------------------------------------------------------------- #
def hex_points(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """尖顶正六边形顶点（顶点在正上/正下）。"""
    return [
        (cx + r * math.cos(math.radians(-90 + 60 * k)),
         cy + r * math.sin(math.radians(-90 + 60 * k)))
        for k in range(6)
    ]


def draw_profile(draw: ImageDraw.ImageDraw, x0: float, x1: float, y_base: float,
                 amp_unit: float, color, lw: int,
                 arrow: bool = True, arrow_color=None) -> None:
    """画衍射谱线：基线 + 三个高斯峰；最左峰上标 FWHM 双箭头。"""
    width = x1 - x0
    n = 220
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        g = 0.0
        for xc, h, fw in PEAKS:
            sigma = fw / 2.3548          # FWHM → 高斯 σ
            g += h * math.exp(-((t - xc) ** 2) / (2 * sigma ** 2))
        pts.append((x0 + t * width, y_base - amp_unit * g))
    draw.line(pts, fill=color, width=lw, joint="curve")

    if not arrow:
        return
    xc, h, fw = PEAKS[0]
    y_half = y_base - amp_unit * h * 0.5
    xa = x0 + (xc - fw / 2) * width
    xb = x0 + (xc + fw / 2) * width
    ac = arrow_color or color
    lw_a = max(1, int(round(lw * 0.8)))
    draw.line([(xa, y_half), (xb, y_half)], fill=ac, width=lw_a)
    cap = max(2, int(round(lw * 1.5)))
    for x in (xa, xb):
        draw.line([(x, y_half - cap), (x, y_half + cap)], fill=ac, width=lw_a)


def make_mark(size: int, hex_color, line_color, arrow_color,
              hex_w_ratio: float = 0.070, glow: bool = False) -> Image.Image:
    """生成 CrySize 家族符号：六边形 + 峰宽谱线（透明底 RGBA）。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = size / 2.0
    r = size * 0.44
    hex_w = max(2, int(round(size * hex_w_ratio)))
    line_lw = max(2, int(size * 0.022))
    pts = hex_points(cx, cy, r)

    # 谱线区域：占符号内部宽度的 ~60%，基线略低于中心，最高峰顶接近中心偏上
    x0 = cx - size * 0.290
    x1 = cx + size * 0.290
    y_base = cy + size * 0.155
    amp = size * 1.20

    def motif(d: ImageDraw.ImageDraw) -> None:
        draw_profile(d, x0, x1, y_base, amp, line_color, line_lw,
                     arrow=True, arrow_color=arrow_color)

    if glow:
        gl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gd.line(pts + [pts[0]], fill=hex_color, width=hex_w, joint="curve")
        motif(gd)
        gl = gl.filter(ImageFilter.GaussianBlur(max(2, size * 0.02)))
        im.alpha_composite(gl)

    d = ImageDraw.Draw(im)
    d.line(pts + [pts[0]], fill=hex_color, width=hex_w, joint="curve")
    motif(d)
    return im


def diagonal_gradient(size: int, c1, c2) -> Image.Image:
    """左上 → 右下 对角线渐变（低分辨率生成再放大，保证平滑）。"""
    small = Image.new("RGB", (96, 96))
    px = small.load()
    for y in range(96):
        for x in range(96):
            t = (x + y) / (2 * 95.0)
            px[x, y] = (round(c1[0] + (c2[0] - c1[0]) * t),
                        round(c1[1] + (c2[1] - c1[1]) * t),
                        round(c1[2] + (c2[2] - c1[2]) * t))
    return small.resize((size, size), Image.BICUBIC)


def radial_gradient(w: int, h: int, inner, outer) -> Image.Image:
    """径向渐变背景（中心亮 → 四周暗）。"""
    small = Image.new("RGB", (120, 68))
    px = small.load()
    cx, cy = 59.5, 33.0
    maxd = math.hypot(cx, cy)
    for y in range(68):
        for x in range(120):
            d = min(1.0, math.hypot(x - cx, y - cy) / maxd) ** 0.85
            px[x, y] = (round(inner[0] + (outer[0] - inner[0]) * d),
                        round(inner[1] + (outer[1] - inner[1]) * d),
                        round(inner[2] + (outer[2] - inner[2]) * d))
    return small.resize((w, h), Image.BICUBIC)


def rounded_mask(size: int, ratio: float = 0.22) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=int(size * ratio), fill=255)
    return m


def load_font(paths: list[str], size: int):
    """按顺序尝试加载字体，全部失败时退回默认位图字体。"""
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_wordmark(draw: ImageDraw.ImageDraw, x: float, y_top: float,
                  segments: list[tuple[str, tuple[int, int, int]]],
                  font) -> float:
    """按 segment 着色绘制词标，返回结束 x。"""
    for text, color in segments:
        draw.text((x, y_top), text, font=font, fill=color)
        x += draw.textlength(text, font=font)
    return x


def wordmark_width(draw: ImageDraw.ImageDraw, segments, font) -> float:
    return sum(draw.textlength(t, font=font) for t, _c in segments)


# --------------------------------------------------------------------------- #
# 各类资产构建
# --------------------------------------------------------------------------- #
def build_icon() -> None:
    """应用图标：对角渐变底 + 发光 mark，256 / @2x / 多分辨率 ico。"""
    size = 512
    base = diagonal_gradient(size, BRAND_DARK, BRAND_BLUE).convert("RGBA")
    mark = make_mark(size, WHITE, CYAN_LIGHT, CYAN,
                     hex_w_ratio=0.075, glow=True)
    base.alpha_composite(mark)
    base.putalpha(rounded_mask(size, 0.22))

    RES_DIR.mkdir(parents=True, exist_ok=True)
    base.resize((512, 512), Image.LANCZOS).save(
        RES_DIR / "app-icon@2x.png", format="PNG", optimize=True)
    base.resize((256, 256), Image.LANCZOS).save(
        RES_DIR / "app-icon.png", format="PNG", optimize=True)
    base.save(RES_DIR / "app-icon.ico", format="ICO",
              sizes=[(s, s) for s in ICON_SIZES])
    print("[icon] app-icon.png / app-icon@2x.png / app-icon.ico")


def build_crystal_mark() -> None:
    """透明底、深色线条版家族符号（浅色背景 About / 文档用）。"""
    mark = make_mark(256, BRAND_DARK, BRAND_BLUE, CYAN_DARK,
                     hex_w_ratio=0.055)
    mark.save(RES_DIR / "crystal-mark.png", format="PNG", optimize=True)
    print("[mark] crystal-mark.png")


def build_logo_horizontal() -> None:
    """横向 logo 512×160：mark + 「PolyXRD CrySize」+ 功能副标。"""
    SS = 4
    W, H = 512 * SS, 160 * SS
    mark_size = int(H * 0.72)
    sub = "Scherrer · Williamson-Hall"

    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = make_mark(mark_size, BRAND_DARK, BRAND_BLUE, CYAN_DARK,
                     hex_w_ratio=0.055)
    pad_x = int(H * 0.10)
    im.alpha_composite(mark, (pad_x, (H - mark_size) // 2))

    d = ImageDraw.Draw(im)
    font_size = int(H * 0.30)
    segs = [("PolyXRD ", BRAND_DARK), ("CrySize", CYAN_DARK)]
    font_big = load_font([FONT_BOLD], font_size)
    x_text = pad_x + mark_size + int(H * 0.12)
    while x_text + wordmark_width(d, segs, font_big) > W - int(H * 0.08) and font_size > 24:
        font_size = int(font_size * 0.95)
        font_big = load_font([FONT_BOLD], font_size)
    y_big = int(H * 0.20)
    draw_wordmark(d, x_text, y_big, segs, font_big)
    font_sub = load_font([FONT_SEMI, FONT_CN], int(H * 0.115))
    d.text((x_text, y_big + int(H * 0.40)), sub, font=font_sub, fill=SLATE)

    im.resize((W // SS, H // SS), Image.LANCZOS).save(
        RES_DIR / "logo-horizontal.png", format="PNG", optimize=True)
    print("[logo] logo-horizontal.png (512x160)")


def _title_segments() -> list[tuple[str, tuple[int, int, int]]]:
    return [("PolyXRD ", SOFT), ("CrySize", CYAN_LIGHT)]


def build_splash() -> None:
    """启动图 480×270：深色底 + mark + 标题 + 版本 + tagline。"""
    W, H = 480, 270
    SS = 2
    w, h = W * SS, H * SS
    bg = radial_gradient(w, h, BG_INNER, BG_OUTER).convert("RGBA")

    mark = make_mark(int(h * 0.42), WHITE, CYAN_LIGHT, CYAN,
                     hex_w_ratio=0.070, glow=True)
    bg.alpha_composite(mark, ((w - mark.size[0]) // 2, int(h * 0.015)))

    d = ImageDraw.Draw(bg)
    segs = _title_segments()
    font_t = load_font([FONT_BOLD], int(h * 0.105))
    tw = wordmark_width(d, segs, font_t)
    draw_wordmark(d, (w - tw) / 2, int(h * 0.525), segs, font_t)

    font_v = load_font([FONT_SEMI], int(h * 0.055))
    ver = f"v{__version__}"
    d.text(((w - d.textlength(ver, font=font_v)) / 2, int(h * 0.655)),
           ver, font=font_v, fill=CYAN)

    font_c = load_font([FONT_CN, FONT_SEMI], int(h * 0.052))
    tw = d.textlength(APP_TAGLINE, font=font_c)
    d.text(((w - tw) / 2, int(h * 0.755)), APP_TAGLINE, font=font_c,
           fill=(130, 176, 205))

    bg.convert("RGB").resize((W, H), Image.LANCZOS).save(
        RES_DIR / "splash-screen.png", format="PNG", optimize=True)
    print("[splash] splash-screen.png (480x270)")


def build_hero() -> None:
    """About 页头图 1600×600：深空底 + 大 mark + 标题 + tagline。"""
    W, H = 1600, 600
    bg = radial_gradient(W, H, BG_INNER, BG_OUTER).convert("RGBA")

    mark = make_mark(int(H * 0.40), WHITE, CYAN_LIGHT, CYAN,
                     hex_w_ratio=0.070, glow=True)
    bg.alpha_composite(mark, ((W - mark.size[0]) // 2, int(H * 0.03)))

    d = ImageDraw.Draw(bg)
    segs = _title_segments()
    font_t = load_font([FONT_BOLD], int(H * 0.135))
    tw = wordmark_width(d, segs, font_t)
    draw_wordmark(d, (W - tw) / 2, int(H * 0.50), segs, font_t)

    font_c = load_font([FONT_CN, FONT_SEMI], int(H * 0.052))
    tw = d.textlength(APP_TAGLINE, font=font_c)
    d.text(((W - tw) / 2, int(H * 0.72)), APP_TAGLINE, font=font_c,
           fill=(130, 176, 205))

    font_s = load_font([FONT_SEMI], int(H * 0.042))
    sub = ("Scherrer Equation  ·  Williamson-Hall Plot  ·  "
           "Instrumental Broadening  ·  Caglioti U/V/W")
    tw = d.textlength(sub, font=font_s)
    d.text(((W - tw) / 2, int(H * 0.83)), sub, font=font_s, fill=CYAN)

    bg.convert("RGB").save(RES_DIR / "hero-banner.png", format="PNG", optimize=True)
    print("[hero] hero-banner.png (1600x600)")


def build_all() -> None:
    RES_DIR.mkdir(parents=True, exist_ok=True)
    build_icon()
    build_crystal_mark()
    build_logo_horizontal()
    build_splash()
    build_hero()
    files = sorted(p.name for p in RES_DIR.iterdir() if p.is_file())
    print(f"\n[done] 共 {len(files)} 个资产: {files}")


if __name__ == "__main__":
    build_all()
