from datetime import datetime
from pathlib import Path
import json
import re
import shutil
from .config import BACKUP_DIR, APP_DIR, ensure_dirs, config_paths


def _copy(src: Path, dst: Path):
    if src.is_dir():
        shutil.copytree(src, dst)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def create_backup(reason="manual"):
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target = BACKUP_DIR / stamp
    target.mkdir()
    manifest = {"id": stamp, "reason": reason, "items": []}

    for name, path in config_paths().items():
        if path.exists():
            _copy(path, target / name)
            manifest["items"].append({"editor": name, "path": str(path)})

    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return stamp


def list_backups():
    ensure_dirs()
    return sorted((p.name for p in BACKUP_DIR.iterdir() if p.is_dir()), reverse=True)


def restore(backup_id):
    src = BACKUP_DIR / backup_id
    if not (src / "manifest.json").exists():
        raise ValueError(f"Backup inválido: {backup_id}")
    for name, path in config_paths().items():
        saved = src / name
        if not saved.exists():
            continue
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        _copy(saved, path)


def _strip_block(path: Path, start: str, end: str):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"\n?" + re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    updated = pattern.sub("\n", text).strip("\n")
    path.write_text((updated + "\n") if updated else "", encoding="utf-8")


def _reset_vscode(path: Path, palette: dict):
    settings_path = path / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    color_map = {
        "editor.background": palette.get("background", "#1e1e1e"),
        "editor.foreground": palette.get("foreground", "#d4d4d4"),
        "editorLineNumber.foreground": palette.get("muted", "#858585"),
        "editorCursor.foreground": palette.get("accent", "#aeafad"),
        "editor.selectionBackground": palette.get("selection", "#264f78"),
        "editor.lineHighlightBackground": palette.get("line", "#2a2d2e"),
        "editorWidget.background": palette.get("surface", "#252526"),
        "sideBar.background": palette.get("surface", "#252526"),
        "activityBar.background": palette.get("background", "#1e1e1e"),
        "statusBar.background": palette.get("surface", "#252526"),
    }
    colors = settings.get("workbench.colorCustomizations")
    if isinstance(colors, dict):
        for key, value in color_map.items():
            if colors.get(key) == value:
                colors.pop(key, None)
        if not colors:
            settings.pop("workbench.colorCustomizations", None)

    expected_tokens = {
        "comments": palette.get("comment", "#6a9955"),
        "strings": palette.get("string", "#ce9178"),
        "numbers": palette.get("number", "#b5cea8"),
        "keywords": palette.get("keyword", "#c586c0"),
        "functions": palette.get("function", "#dcdcaa"),
        "variables": palette.get("variable", "#9cdcfe"),
        "types": palette.get("type", "#4ec9b0"),
    }
    if settings.get("editor.tokenColorCustomizations") == expected_tokens:
        settings.pop("editor.tokenColorCustomizations", None)

    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def reset_configs():
    """Remove somente alterações gerenciadas pelo TEdit; não apaga configs do usuário."""
    state_file = APP_DIR / "state.json"
    if not state_file.exists():
        return
    state = json.loads(state_file.read_text(encoding="utf-8"))
    theme = state.get("theme")
    if not theme:
        return

    paths = config_paths()
    theme_dir = Path(__file__).resolve().parent / "themes" / theme
    palette_path = theme_dir / "palette.json"
    palette = json.loads(palette_path.read_text(encoding="utf-8")) if palette_path.exists() else {}

    (paths["nvim"] / "tedit_theme.lua").unlink(missing_ok=True)
    _strip_block(paths["nvim"] / "init.lua", "-- TEDIT:BEGIN THEME", "-- TEDIT:END THEME")

    (paths["micro"] / "colorschemes" / f"{theme}.micro").unlink(missing_ok=True)
    (paths["helix"] / "themes" / f"{theme}.toml").unlink(missing_ok=True)

    _reset_vscode(paths["vscode"], palette)
    _reset_vscode(paths["vscodium"], palette)
    _strip_block(paths["atom"] / "styles.less", "// TEDIT:BEGIN THEME", "// TEDIT:END THEME")
    _strip_block(paths["pulsar"] / "styles.less", "// TEDIT:BEGIN THEME", "// TEDIT:END THEME")

    state_file.unlink(missing_ok=True)
