#!/usr/bin/env python3
"""
CME Bank Design System — build script.

Produces two things in dist/:

  dist/index.html   A single self-contained HTML file with all CSS inlined.
                    Use this when you need to hand the docs to someone as one
                    file, or publish somewhere that can't serve assets.

  dist/tokens.json  DTCG-format tokens, regenerated from tokens.css so the
                    CSS stays the single source of truth. Feed this to Style
                    Dictionary to emit iOS, Android, or JS token files.

Usage:  python build.py

No dependencies. Python 3.8+.
"""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"


def build_single_file() -> None:
    """Inline tokens.css, components.css and site.css into one HTML file."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    bundle = []
    for name in ("tokens.css", "components.css", "site.css"):
        css = (ROOT / name).read_text(encoding="utf-8")
        bundle.append(f"/* ===== {name} ===== */\n{css}")

    # replace the three <link> tags with one inline <style>
    html = re.sub(
        r'\s*<link rel="stylesheet" href="(tokens|components|site)\.css">',
        "",
        html,
    )
    html = html.replace(
        "</head>",
        "<style>\n" + "\n\n".join(bundle) + "\n</style>\n</head>",
    )

    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(html, encoding="utf-8")
    print(f"  dist/index.html      {len(html):>8,} bytes")


def build_tokens_json() -> None:
    """Regenerate DTCG tokens from tokens.css."""
    css = (ROOT / "tokens.css").read_text(encoding="utf-8")

    primitive_block = css.split("TIER 2")[0]
    primitives = dict(
        re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6}|\d+px|999px|0);", primitive_block)
    )

    def classify(name):
        m = re.match(r"(green|blue|red|amber|teal|neutral)-(\d+)$", name)
        if m:
            return "color", m.group(1), m.group(2)
        m = re.match(r"(space|radius|border|control|icon)-(.+)$", name)
        if m:
            return "dimension", m.group(1), m.group(2)
        return None

    out = {"$schema": "https://tr.designtokens.org/format/", "cme": {}}
    for key, value in primitives.items():
        info = classify(key)
        if not info:
            continue
        token_type, family, step = info
        out["cme"].setdefault(family, {})[step] = {"$value": value, "$type": token_type}

    light = css.split("TIER 2 — SEMANTIC (light mode)")[1].split(
        "TIER 2 — SEMANTIC (dark mode)"
    )[0]
    out["cme"]["semantic"] = {}
    for name, ref in re.findall(r"--([\w-]+):\s*var\(--([\w-]+)\);", light):
        if re.match(r".+-\d+$", ref):
            pointer = "{{cme.{}.{}}}".format(*ref.rsplit("-", 1))
        else:
            pointer = "{cme.%s}" % ref
        out["cme"]["semantic"][name] = {"$value": pointer, "$type": "color"}

    DIST.mkdir(exist_ok=True)
    text = json.dumps(out, indent=2)
    (DIST / "tokens.json").write_text(text, encoding="utf-8")
    (ROOT / "tokens.json").write_text(text, encoding="utf-8")

    n_prim = sum(len(v) for k, v in out["cme"].items() if k != "semantic")
    print(f"  dist/tokens.json     {n_prim} primitives, {len(out['cme']['semantic'])} semantic")


def copy_sources() -> None:
    """Copy the raw stylesheets so dist/ can also be served as-is."""
    DIST.mkdir(exist_ok=True)
    for name in ("tokens.css", "components.css", "site.css"):
        shutil.copy(ROOT / name, DIST / name)
    print("  dist/*.css           copied")


if __name__ == "__main__":
    print("Building CME Bank Design System…")
    build_tokens_json()
    copy_sources()
    build_single_file()
    print("Done. Serve dist/ or open dist/index.html directly.")
