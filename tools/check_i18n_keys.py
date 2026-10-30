"""不依赖 pytest/numpy 的三语键集与占位符一致性校验。"""

import ast
import string
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "crysize" / "i18n" / "translations"
LANGS = ["zh_CN", "en_US", "ja_JP"]


def load(lang: str) -> dict[str, str]:
    src = (BASE / f"{lang}.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            out = {}
            for k, v in zip(node.value.keys, node.value.values):
                key = ast.literal_eval(k)
                if isinstance(v, ast.Constant):
                    out[key] = v.value
                elif isinstance(v, ast.BinOp):  # 隐式拼接
                    out[key] = ast.literal_eval(v)
            return out
    raise SystemExit(f"no dict in {lang}")


def fields(s: str) -> list[str]:
    return [f for _, f, _, _ in string.Formatter().parse(s) if f]


def main() -> int:
    data = {lang: load(lang) for lang in LANGS}
    keys = {lang: set(d) for lang, d in data.items()}
    ref = keys["zh_CN"]
    bad = 0
    for lang in LANGS:
        missing = ref - keys[lang]
        extra = keys[lang] - ref
        if missing:
            print(f"[MISSING] {lang}: {sorted(missing)}")
            bad += 1
        if extra:
            print(f"[EXTRA]   {lang}: {sorted(extra)}")
            bad += 1
    for key in sorted(ref):
        fs = {lang: tuple(sorted(fields(data[lang][key]))) for lang in LANGS}
        if len(set(fs.values())) > 1:
            print(f"[FORMAT]  {key}: {fs}")
            bad += 1
    print(f"keys={len(ref)} langs={LANGS} problems={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
