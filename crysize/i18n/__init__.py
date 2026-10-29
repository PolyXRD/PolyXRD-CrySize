"""多语言支持（zh_CN / en_US / ja_JP）—— 与家族 PolyXRD-RutAna 同一接口。

对外暴露 tr / set_language / current_language / available_languages /
load_language / save_language。
"""
from crysize.i18n.i18n_manager import (
    TABLE,
    available_languages,
    current_language,
    load_language,
    save_language,
    set_language,
    tr,
)

__all__ = [
    "tr",
    "TABLE",
    "set_language",
    "current_language",
    "available_languages",
    "load_language",
    "save_language",
]
