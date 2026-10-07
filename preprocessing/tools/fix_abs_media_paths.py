#!/usr/bin/env python3
"""把译文/源文里指向 `…/structured/<相对路径>` 的**绝对路径**改回相对路径。

## 缺陷

源抽取把图片引用写成绝对路径，且**根目录与实际工作区不符**：本项目在
`/home/hermes/work/translate`，而 pentagon-papers 的源侧写的是
`/home/agent/work/translate/workspaces/…/structured/raw/media/Images/bor.jpg`
——该路径在本机**根本不存在**。构建器只按 `structured/` 下的相对路径打包媒体，
绝对路径一律无法解析，于是成品**静默丢图**：
`E_MEDIA_EPUB_LOST 成品缺失译文引用的图片`（实测 8 张）。

## 处置

按「`structured/` 之后的部分」重写，与本机实际根目录无关，也不硬编码 slug：
`(/.*?)/structured/(raw/…)` → `\2`。

**只改图片/链接的 href，不动链接文字、不动其他内容**；不改 `…/structured/` 之外的
绝对路径（那些可能是有意为之的外部资源）。

用法：
    python fix_abs_media_paths.py <目录...>            # dry-run
    python fix_abs_media_paths.py --write <目录...>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# 形如 /任意根/structured/raw/... → raw/...
# 只在 markdown 链接/图片的 href 位置替换。
HREF = re.compile(r"(\]\()[^)]*?/structured/((?:raw|analysis|preprocessing)/[^)]*?)(\))")


def fix(text: str) -> tuple[str, int]:
    return HREF.subn(r"\1\2\3", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    total = 0
    files = 0
    for root in args.paths:
        for ext in ("*.md", "*.jsonl"):
            for p in sorted(Path(root).rglob(ext)):
                s = p.read_text(encoding="utf-8")
                if "/structured/" not in s:
                    continue
                out, n = fix(s)
                if n == 0:
                    continue
                total += n
                files += 1
                print(f"{'WRITE' if args.write else 'DRY'}  {p}  改写 {n} 处")
                if args.write:
                    tmp = Path(str(p) + ".tmp")
                    tmp.write_text(out, encoding="utf-8")
                    os.replace(tmp, p)
    print(f"\n合计改写 {total} 处，涉及 {files} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())