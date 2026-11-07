"""Tests for scripts/build-color-schemes.py (run with: pytest scripts/)."""
import importlib.util
import pathlib
import textwrap

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_color_schemes", HERE / "build-color-schemes.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)

SCHEME = textwrap.dedent("""\
    system: "base24"
    name: "Test Dark"
    author: "someone"
    variant: "dark"
    description: "a test"
    palette:
      base00: "#101010"
      base01: "#111111"
      base02: "#121212"
      base03: "#131313"
      base04: "#141414"
      base05: "#f5f5f5"
      base06: "#161616"
      base07: "#171717"
      base08: "#ff0000"
      base09: "#ff8800"
      base0A: "#ffff00"
      base0B: "#00ff00"
      base0C: "#00ffff"
      base0D: "#0000ff"
      base0E: "#ff00ff"
      base0F: "#884400"
      base10: "#0a0a0a"
      base11: "#050505"
      base12: "#ff1111"
      base13: "#ffff11"
      base14: "#11ff11"
      base15: "#11ffff"
      base16: "#1111ff"
      base17: "#ff11ff"
""")


def make_package(tmp_path, template="{{ scheme_slug }} {{ base08_hex }} {{ roles.accent }} {{ roles.bg | hypr('cc') }}\n"):
    pkg = tmp_path / "color-schemes"
    (pkg / "schemes" / "test").mkdir(parents=True)
    (pkg / "schemes" / "test" / "dark.yaml").write_text(SCHEME)
    (pkg / "templates").mkdir()
    (pkg / "templates" / "demo.txt.j2").write_text(template)
    (pkg / "build.yaml").write_text('schemes:\n  test:\n    accent: base09\n')
    return pkg


def test_context_exposes_tinted_style_variables_and_roles(tmp_path):
    pkg = make_package(tmp_path)
    ctx = build.load_context(pkg, "test", "dark")
    assert ctx["base08_hex"] == "ff0000"
    assert ctx["base08_rgb_r"] == 255 and ctx["base08_rgb_g"] == 0
    assert ctx["scheme_is_dark_variant"] is True
    assert ctx["roles"]["accent"] == "#ff8800"
    assert ctx["roles"]["error"] == "#ff0000"
    assert ctx["ansi"][9] == "#ff1111"


def test_build_writes_ports_and_check_passes_then_fails_when_stale(tmp_path):
    pkg = make_package(tmp_path)
    assert build.main(["--package", str(pkg)]) == 0
    out = pkg / "ports" / "test" / "dark" / "demo.txt"
    assert out.read_text() == "test ff0000 #ff8800 rgba(101010cc)\n"
    assert build.main(["--package", str(pkg), "--check"]) == 0
    out.write_text("stale\n")
    assert build.main(["--package", str(pkg), "--check"]) == 1


def test_missing_slot_is_an_error(tmp_path):
    pkg = make_package(tmp_path)
    (pkg / "schemes" / "test" / "dark.yaml").write_text(SCHEME.replace('  base17: "#ff11ff"\n', ""))
    try:
        build.load_context(pkg, "test", "dark")
    except build.SchemeError as e:
        assert "base17" in str(e)
    else:
        raise AssertionError("expected SchemeError")


def context_with_nvim_block(tmp_path, block):
    pkg = make_package(tmp_path)
    path = pkg / "schemes" / "test" / "dark.yaml"
    path.write_text(path.read_text() + block)
    return build.load_context(pkg, "test", "dark")


def test_nvim_block_overrides_the_nvim_slots_only(tmp_path):
    ctx = context_with_nvim_block(
        tmp_path, 'nvim:\n  emphasis: true\n  palette:\n    base0E: "#ABCDEF"\n'
    )
    assert ctx["nvim_slots"]["base0E"] == "#abcdef"
    assert ctx["nvim_slots"]["base08"] == "#ff0000"
    assert ctx["nvim_emphasis"] is True
    assert ctx["slots"]["base0E"] == "#ff00ff"
    assert ctx["ansi"][5] == "#ff00ff"


def test_nvim_slots_default_to_the_palette(tmp_path):
    ctx = build.load_context(make_package(tmp_path), "test", "dark")
    assert ctx["nvim_slots"]["base0E"] == "#ff00ff"
    assert len(ctx["nvim_slots"]) == 16
    assert ctx["nvim_emphasis"] is False


def test_nvim_palette_rejects_slots_mini_base16_does_not_read(tmp_path):
    try:
        context_with_nvim_block(tmp_path, 'nvim:\n  palette:\n    base12: "#000000"\n')
    except build.SchemeError as e:
        assert "base12" in str(e)
    else:
        raise AssertionError("expected SchemeError")


def test_nvim_palette_rejects_bad_colours(tmp_path):
    try:
        context_with_nvim_block(tmp_path, 'nvim:\n  palette:\n    base0E: "nope"\n')
    except build.SchemeError as e:
        assert "nvim.palette.base0E" in str(e)
    else:
        raise AssertionError("expected SchemeError")
