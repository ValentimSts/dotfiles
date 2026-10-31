#!/usr/bin/env python3
"""Render every colour scheme port from the Base24 palettes.

Usage: scripts/build-color-schemes.py [--package DIR] [--check]

Reads <package>/build.yaml, loads <package>/schemes/<scheme>/<mode>.yaml
(Base24, spec 0.11) and renders each <package>/templates/<app>.<ext>.j2 into
<package>/ports/<scheme>/<mode>/<app>.<ext>. With --check nothing is written;
the exit status is 1 when a rendered port differs from the committed file.

Template variables follow the tinted-theming builder names with underscores
(base00_hex, base00_rgb_r, scheme_is_dark_variant, ...) plus a `roles` table
of semantic colours, a `slots` table (base00..base17 -> '#rrggbb') and an
`ansi` list of the 16 terminal colours.
"""
import argparse
import pathlib
import sys

import jinja2
import yaml

SLOTS = ["base%02X" % i for i in range(0x18)]
MODES = ("dark", "light")

# Base24 slot roles (tinted-theming styling guide); the accent slot comes from build.yaml.
ROLES = {
    "bg": "base00", "bg_alt": "base01", "selection": "base02", "muted": "base03",
    "subtle": "base04", "text": "base05", "text_bright": "base06", "text_brightest": "base07",
    "error": "base08", "orange": "base09", "warning": "base0A", "success": "base0B",
    "info": "base0C", "link": "base0D", "keyword": "base0E", "deprecated": "base0F",
    "pane_dark": "base10", "pane_darkest": "base11",
}
# ANSI 0..15 -> slot, per the Base24 styling guide.
ANSI = ["base00", "base08", "base0B", "base0A", "base0D", "base0E", "base0C", "base05",
        "base03", "base12", "base14", "base13", "base16", "base17", "base15", "base07"]


class SchemeError(Exception):
    pass


def hypr(hex_color, alpha="ff"):
    """'#rrggbb' -> 'rgba(rrggbbaa)' (hyprlang colour syntax)."""
    return "rgba(%s%s)" % (hex_color.lstrip("#").lower(), alpha)


def rgb(hex_color):
    """'#rrggbb' -> 'r, g, b'."""
    h = hex_color.lstrip("#")
    return ", ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def load_context(package, scheme, mode):
    path = package / "schemes" / scheme / f"{mode}.yaml"
    data = yaml.safe_load(path.read_text())
    manifest = yaml.safe_load((package / "build.yaml").read_text())
    accent_slot = manifest["schemes"][scheme].get("accent", "base0D")
    palette = data.get("palette") or {}
    missing = [s for s in SLOTS if s not in palette]
    if missing:
        raise SchemeError(f"{path}: missing slots {', '.join(missing)}")
    if data.get("system") != "base24":
        raise SchemeError(f"{path}: system must be base24")

    ctx = {
        "scheme_system": "base24",
        "scheme_name": data["name"],
        "scheme_slug": scheme,
        "scheme_author": data.get("author", ""),
        "scheme_description": data.get("description", ""),
        "scheme_variant": mode,
        "scheme_is_dark_variant": mode == "dark",
        "scheme_is_light_variant": mode == "light",
    }
    hexes = {}
    for slot in SLOTS:
        value = str(palette[slot]).lstrip("#").lower()
        if len(value) != 6 or any(c not in "0123456789abcdef" for c in value):
            raise SchemeError(f"{path}: {slot} is not a #rrggbb colour: {palette[slot]}")
        hexes[slot] = "#" + value
        ctx[f"{slot}_hex"] = value
        for name, i in (("r", 0), ("g", 2), ("b", 4)):
            ctx[f"{slot}_hex_{name}"] = value[i:i + 2]
            ctx[f"{slot}_rgb_{name}"] = int(value[i:i + 2], 16)
            ctx[f"{slot}_dec_{name}"] = round(int(value[i:i + 2], 16) / 255, 4)
    ctx["slots"] = dict(hexes)
    ctx["roles"] = {role: hexes[slot] for role, slot in ROLES.items()}
    ctx["roles"]["accent"] = hexes[accent_slot]
    ctx["ansi"] = [hexes[slot] for slot in ANSI]
    return ctx


def render_all(package):
    """Yield (output path, rendered text) for every scheme, mode and template."""
    manifest = yaml.safe_load((package / "build.yaml").read_text())
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(package / "templates")),
        keep_trailing_newline=True, undefined=jinja2.StrictUndefined,
        trim_blocks=True, lstrip_blocks=True,
    )
    env.filters["hypr"] = hypr
    env.filters["rgb"] = rgb
    templates = sorted(p.name for p in (package / "templates").glob("*.j2"))
    for scheme in manifest["schemes"]:
        for mode in MODES:
            if not (package / "schemes" / scheme / f"{mode}.yaml").exists():
                continue
            ctx = load_context(package, scheme, mode)
            for name in templates:
                out = package / "ports" / scheme / mode / name[:-3]
                yield out, env.get_template(name).render(ctx)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parent.parent / "color-schemes" / ".config" / "color-schemes")
    parser.add_argument("--check", action="store_true", help="report stale ports instead of writing")
    args = parser.parse_args(argv)
    stale = 0
    try:
        for out, text in render_all(args.package):
            if args.check:
                if not out.exists() or out.read_text() != text:
                    print(f"stale: {out}")
                    stale += 1
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text)
                print(f"wrote {out.relative_to(args.package)}")
    except SchemeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.check:
        print("all ports up to date" if not stale else f"{stale} stale port(s); run scripts/build-color-schemes.py")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
