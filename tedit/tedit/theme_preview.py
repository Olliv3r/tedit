from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .theme import THEMES_DIR, list_themes

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
CLEAR = "\x1b[2J\x1b[H"


def _palette(name: str) -> dict[str, str]:
    path = THEMES_DIR / name / "palette.json"
    if not path.is_file():
        raise ValueError(f"Tema sem palette.json para preview: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Cor inválida: {hex_color}")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def _fg(color: str) -> str:
    r, g, b = _rgb(color)
    return f"\x1b[38;2;{r};{g};{b}m"


def _bg(color: str) -> str:
    r, g, b = _rgb(color)
    return f"\x1b[48;2;{r};{g};{b}m"


def _span(text: str, color: str, background: str | None = None, bold: bool = False) -> str:
    prefix = (_bg(background) if background else "") + (_fg(color) if color else "") + (BOLD if bold else "")
    return f"{prefix}{text}{RESET}"


def render_terminal_preview(name: str) -> str:
    p = _palette(name)
    bg = p["background"]
    fg = p["foreground"]
    lines = [
        _span(f"  TEdit theme preview — {name}  ", fg, p.get("surface", bg), True),
        "",
        _span("  1  ", p["muted"], bg) + _span("class ", p["keyword"], bg) + _span("ThemePreview", p["type"], bg) + _span(":", fg, bg),
        _span("  2  ", p["muted"], bg) + _span("    def ", p["keyword"], bg) + _span("render", p["function"], bg) + _span("(self, name: ", fg, bg) + _span("str", p["type"], bg) + _span(") -> ", fg, bg) + _span("bool", p["type"], bg) + _span(":", fg, bg),
        _span("  3  ", p["muted"], bg) + _span("        # preview sem alterar sua configuração", p["comment"], bg),
        _span("  4  ", p["muted"], bg) + _span("        colors", p["variable"], bg) + _span(" = [", fg, bg) + _span('"blue"', p["string"], bg) + _span(", ", fg, bg) + _span('"green"', p["string"], bg) + _span("]", fg, bg),
        _span("  5  ", p["muted"], bg) + _span("        retries", p["variable"], bg) + _span(" = ", fg, bg) + _span("3", p["number"], bg),
        _span("  6  ", p["muted"], bg) + _span("        return ", p["keyword"], bg) + _span("True", p["constant"], bg),
        "",
        _span("  NORMAL  ", bg, p["accent"], True) + " " + _span(" main.py  Ln 6, Col 20 ", fg, p.get("surface", bg)),
    ]
    return "\n".join(lines) + RESET


def preview_terminal(name: str) -> None:
    if name not in list_themes():
        raise ValueError(f"Tema não encontrado: {name}")
    print(render_terminal_preview(name))


def _read_key() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().strip().lower()
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch += sys.stdin.read(2)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except (ImportError, OSError):
        return input("> ").strip().lower()


def browse_terminal() -> str | None:
    themes = list_themes()
    if not themes:
        return None
    if not os.isatty(0) or not os.isatty(1):
        for name in themes:
            print(render_terminal_preview(name))
            print()
        return None

    index = 0
    while True:
        name = themes[index]
        print(CLEAR, end="")
        print(render_terminal_preview(name))
        print(f"\n[{index + 1}/{len(themes)}]  ←/→ ou j/k muda · Enter seleciona · q sai")
        key = _read_key()
        if key in {"q", "Q", "\x03"}:
            print()
            return None
        if key in {"\r", "\n", ""}:
            print()
            return name
        if key in {"j", "l", "n", "\x1b[C", "\x1b[B"}:
            index = (index + 1) % len(themes)
        elif key in {"k", "h", "p", "\x1b[D", "\x1b[A"}:
            index = (index - 1) % len(themes)


def _lua_quote(value: str) -> str:
    return json.dumps(value)


def _write_nvim_preview(root: Path, name: str) -> tuple[Path, Path]:
    p = _palette(name)
    app = "tedit-preview"
    config = root / "config" / app
    config.mkdir(parents=True, exist_ok=True)
    demo = root / "theme_preview.py"
    demo.write_text(
        '''class ThemePreview:\n    """Preview real do tema no Neovim."""\n\n    def render(self, name: str) -> bool:\n        # Feche o Neovim para descartar este ambiente temporário.\n        colors = ["blue", "green", "purple"]\n        retries = 3\n        return True\n\npreview = ThemePreview()\nprint(preview.render("tedit"))\n''',
        encoding="utf-8",
    )

    groups = {
        "Normal": ("foreground", "background"),
        "NormalFloat": ("foreground", "surface"),
        "Comment": ("comment", None),
        "String": ("string", None),
        "Number": ("number", None),
        "Boolean": ("constant", None),
        "Constant": ("constant", None),
        "Keyword": ("keyword", None),
        "Function": ("function", None),
        "Type": ("type", None),
        "Identifier": ("variable", None),
        "LineNr": ("muted", "background"),
        "CursorLineNr": ("accent", "background"),
        "Visual": (None, "selection"),
        "StatusLine": ("background", "accent"),
        "StatusLineNC": ("muted", "surface"),
        "Pmenu": ("foreground", "surface"),
        "PmenuSel": ("background", "accent"),
    }
    lua = [
        "vim.opt.termguicolors = true",
        "vim.opt.number = true",
        "vim.opt.cursorline = true",
        "vim.opt.signcolumn = 'yes'",
        "vim.opt.statusline = ' TEdit Preview │ %f %= %l:%c '",
        f"vim.g.colors_name = {_lua_quote('tedit-preview-' + name)}",
    ]
    for group, (fg_key, bg_key) in groups.items():
        parts = []
        if fg_key:
            parts.append(f"fg = {_lua_quote(p[fg_key])}")
        if bg_key:
            parts.append(f"bg = {_lua_quote(p[bg_key])}")
        if group == "CursorLineNr":
            parts.append("bold = true")
        lua.append(f"vim.api.nvim_set_hl(0, {_lua_quote(group)}, {{ {', '.join(parts)} }})")
    lua += [
        "vim.api.nvim_create_autocmd('BufReadPost', { callback = function() vim.cmd('syntax enable') end })",
        f"vim.api.nvim_echo({{{{{_lua_quote('TEdit preview: ' + name)}, 'Title'}}}}, false, {{}})",
    ]
    (config / "init.lua").write_text("\n".join(lua) + "\n", encoding="utf-8")
    return config, demo


def preview_nvim(name: str) -> int:
    if name not in list_themes():
        raise ValueError(f"Tema não encontrado: {name}")
    if not shutil.which("nvim"):
        raise RuntimeError("nvim não encontrado no PATH")

    with tempfile.TemporaryDirectory(prefix="tedit-preview-") as temp:
        root = Path(temp)
        _, demo = _write_nvim_preview(root, name)
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = str(root / "config")
        env["XDG_DATA_HOME"] = str(root / "data")
        env["XDG_STATE_HOME"] = str(root / "state")
        env["XDG_CACHE_HOME"] = str(root / "cache")
        env["NVIM_APPNAME"] = "tedit-preview"
        return subprocess.call(["nvim", str(demo)], env=env)
