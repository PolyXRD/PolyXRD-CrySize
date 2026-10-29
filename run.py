"""启动入口：``python run.py [样品谱图] [标样谱图]``。"""

from __future__ import annotations

import sys

from crysize.gui.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
