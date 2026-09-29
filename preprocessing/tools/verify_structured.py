#!/usr/bin/env python3
"""守恒自查：structured/ 的每个 md 是否完整保留了 raw/ 中「应保留」的物理行。

判定：对每个单元覆盖的 raw 页，取所有**未被清洗规则剔除**的行，去掉空白与标点后，
检查其字符序列是否为该单元 md（去空白标点后）的子串。缺一即报（静默吞内容的硬指标）。

清洗规则与 normalize_structured.py 一致（数字页眉 / 分隔线 / 印刷书名页眉）。

用法：``python preprocessing/tools/verify_structured.py``（退出码非 0 = 有缺失）
"""

from __future__ import annotations

import re
import sys

from normalize_structured import (
    STRUCT,
    UNIT_MAP,
    _is_digital_header,
    _is_print_header,
    _is_separator,
    _load_page,
)

_STRIP = re.compile(r"[\s\W_]+", re.UNICODE)


def _norm(s: str) -> str:
    return _STRIP.sub("", s)


def main() -> int:
    total = missing = 0
    for unit in UNIT_MAP:
        rel = "cover.md" if unit["region"] == "cover" else f"{unit['region']}/{unit['id']}.md"
        md = (STRUCT / rel).read_text(encoding="utf-8")
        md_norm = _norm(md)
        for pno in range(unit["pages"][0], unit["pages"][1] + 1):
            page = _load_page(pno)
            for block in page.get("blocks", []):
                if block.get("type") != "text" or _is_digital_header(block):
                    continue
                for line in (block.get("text") or "").split("\n"):
                    if not line.strip() or _is_separator(line) or _is_print_header(line):
                        continue
                    total += 1
                    key = _norm(line)
                    if key and key not in md_norm:
                        missing += 1
                        if missing <= 20:
                            print(f"  MISS {rel} p{pno}: {line.strip()[:70]}")
    print(f"checked lines={total} missing={missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
