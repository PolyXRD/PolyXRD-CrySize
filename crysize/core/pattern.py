"""谱图数据模型与文件读取。

设计原则
--------
1. **只定位数值列，不改写数据**：不做平滑/重采样/裁切；2θ 若为降序则翻转为升序。
2. **宽容但不猜测**：跳过表头/注释/仪器信息行；进入数值区后遇到非数值行即结束，
   多段数值取最长连续段（多扫描拼接的文件不静默拼接）。
3. **元数据提取**：靶材/波长/步长/扫描范围尽量从文件头读出（岛津、Rigaku、
   Bruker 的 ASCII 导出均有明文），读不到则用 Cu Kα1 默认值并标记来源。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from crysize.i18n import tr

#: 支持的文件扩展名
SUPPORTED_EXTS = (".txt", ".xy", ".xye", ".dat", ".csv", ".asc", ".prn", ".raw", ".uxd", ".ras")

#: 常用靶材 Kα1 波长（Å），ITU/ICDD 表值
KA1 = {
    "Cu": 1.5405980,
    "Co": 1.7889650,
    "Cr": 2.2897000,
    "Fe": 1.9360420,
    "Mo": 0.7093000,
    "Ag": 0.5594075,
}

#: 常用靶材 Kα2 波长（Å）
KA2 = {
    "Cu": 1.5444260,
    "Co": 1.7928500,
    "Cr": 2.2936630,
    "Fe": 1.9399730,
    "Mo": 0.7135900,
    "Ag": 0.5637980,
}

_TARGET_RE = (
    re.compile(r"target\s*[=:]\s*([A-Za-z]{1,2})", re.I),
    re.compile(r"anode\s*[=:]\s*([A-Za-z]{1,2})", re.I),
    re.compile(r"\b(Cu|Co|Cr|Fe|Mo|Ag)\s*K\s*[\u03b1a]", re.I),
    re.compile(r"\b(Cu|Co|Cr|Fe|Mo|Ag)\s*ka1", re.I),
)
_WAVE_RE = (
    re.compile(r"wavelength\s*[=:]\s*([0-9.]+)", re.I),
    re.compile(r"lambda\s*[=:]\s*([0-9.]+)", re.I),
    re.compile(r"k\s*alpha\s*1?\s*[=:]\s*([0-9.]+)", re.I),
)
_STEP_RE = (
    re.compile(r"sampling\s*pitch\s*[=:]\s*([0-9.]+)", re.I),
    re.compile(r"step\s*size\s*[=:]\s*([0-9.]+)", re.I),
    re.compile(r"2\s*theta\s*step\s*[=:]\s*([0-9.]+)", re.I),
    re.compile(r"\bstep\s*[=:]\s*([0-9.]+)", re.I),
)
_RANGE_RE = (
    re.compile(r"scan\s*range\s*[=:]\s*([0-9.]+)\s*[-~]\s*([0-9.]+)", re.I),
    re.compile(r"start\s*[=:]\s*([0-9.]+).*?stop\s*[=:]\s*([0-9.]+)", re.I),
)


class PatternFormatError(ValueError):
    """文件无法解析为两列谱图。"""


@dataclass
class Pattern:
    """单条粉末衍射谱。

    ``two_theta`` 升序、单位度；``intensity`` 为仪器原始计数（不归一化，
    因为计数统计决定拟合权重 —— 峰宽拟合需要 Poisson 权重的可信度）。
    """

    two_theta: np.ndarray
    intensity: np.ndarray
    label: str = ""
    path: str = ""
    anode: str = "Cu"
    wavelength: float = KA1["Cu"]
    step: float = 0.0
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.two_theta = np.asarray(self.two_theta, dtype=float)
        self.intensity = np.asarray(self.intensity, dtype=float)
        if self.two_theta.size != self.intensity.size:
            raise ValueError(tr("pat.len_mismatch"))
        if self.two_theta.size < 10:
            raise ValueError(tr("pat.too_few"))
        if self.two_theta[0] > self.two_theta[-1]:
            self.two_theta = self.two_theta[::-1].copy()
            self.intensity = self.intensity[::-1].copy()
        if not self.step:
            self.step = float(np.median(np.diff(self.two_theta)))

    # -- 便捷属性 ---------------------------------------------------------
    @property
    def n(self) -> int:
        return int(self.two_theta.size)

    @property
    def range(self) -> tuple[float, float]:
        return float(self.two_theta[0]), float(self.two_theta[-1])

    @property
    def max_intensity(self) -> float:
        return float(np.max(self.intensity)) if self.n else 0.0

    def mask(self, lo: float, hi: float) -> np.ndarray:
        return (self.two_theta >= lo) & (self.two_theta <= hi)

    def slice(self, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray]:
        m = self.mask(lo, hi)
        return self.two_theta[m], self.intensity[m]

    def estimate_background(self, window: float = 1.0) -> float:
        """用最低分位数估计本底水平（计数），用于信噪比与净峰高。"""
        if not self.n:
            return 0.0
        return float(np.percentile(self.intensity, 5))


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _numbers(line: str) -> list[float] | None:
    """把一行解析为浮点数列表；含非数值 token 时返回 None。"""
    s = line.strip()
    if not s or s[0] in "#!/*%":
        return None
    if "#" in s:
        s = s.split("#", 1)[0]
    if "//" in s:
        s = s.split("//", 1)[0]
    s = s.replace(",", " ").replace(";", " ").replace("\t", " ")
    out: list[float] = []
    for tok in s.split():
        try:
            out.append(float(tok))
        except ValueError:
            return None
    return out if len(out) >= 2 else None


def _numeric_block(text: str) -> np.ndarray:
    """提取最长连续数值段（N×2 数组）。"""
    best: list[list[float]] = []
    cur: list[list[float]] = []
    for line in text.splitlines():
        vals = _numbers(line)
        if vals is None:
            if len(cur) > len(best):
                best = cur
            cur = []
            continue
        cur.append(vals[:2])
    if len(cur) > len(best):
        best = cur
    if len(best) < 10:
        raise PatternFormatError(tr("pat.no_data"))
    return np.asarray(best, dtype=float)


def _first(regexes, text: str) -> str | None:
    for rx in regexes:
        m = rx.search(text)
        if m:
            return m.group(1)
    return None


def read_pattern(path: str | Path, label: str = "") -> Pattern:
    """读取两列文本谱图（2θ, I）。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    text = _read_text(p)
    arr = _numeric_block(text)

    anode = "Cu"
    tgt = _first(_TARGET_RE, text)
    if tgt:
        t = tgt.strip().capitalize()
        if t in KA1:
            anode = t

    wave = KA1[anode]
    wsrc = f"默认 {anode} Kα1 表值"
    w = _first(_WAVE_RE, text)
    if w:
        try:
            val = float(w)
            if 0.3 < val < 3.0:
                wave = val
                wsrc = "文件头读取"
        except ValueError:
            pass

    meta = {"wavelength_source": wsrc}
    st = _first(_STEP_RE, text)
    if st:
        try:
            meta["header_step"] = float(st)
        except ValueError:
            pass
    rng = None
    for rx in _RANGE_RE:
        m = rx.search(text)
        if m:
            rng = (float(m.group(1)), float(m.group(2)))
            break
    if rng:
        meta["header_range"] = rng

    return Pattern(
        two_theta=arr[:, 0],
        intensity=arr[:, 1],
        label=label or p.stem,
        path=str(p),
        anode=anode,
        wavelength=wave,
        meta=meta,
    )
