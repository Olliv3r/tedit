from pathlib import Path
import json
from .config import APP_DIR, ensure_dirs
from .backup import create_backup
from .detector import detect
from .editors import ADAPTERS, supports_theme

THEMES_DIR = Path(__file__).resolve().parent / "themes"


def list_themes():
    return sorted(p.name for p in THEMES_DIR.iterdir() if p.is_dir())


def apply_theme(name, dry_run=False, editors=None):
    theme_dir = THEMES_DIR / name
    if not theme_dir.is_dir():
        raise ValueError(f"Tema não encontrado: {name}")

    detected = detect()
    selected = set(editors or detected.keys())
    unknown = selected.difference(detected)
    if unknown:
        raise ValueError("Editor(es) desconhecido(s): " + ", ".join(sorted(unknown)))

    planned = [
        editor for editor, info in detected.items()
        if editor in selected and info["installed"] and editor in ADAPTERS and supports_theme(editor, theme_dir)
    ]

    if dry_run:
        return None, planned

    backup_id = create_backup(f"apply-theme:{name}")
    applied = []
    for editor in planned:
        adapter = ADAPTERS[editor]
        if adapter(theme_dir, detected[editor]["config"]):
            applied.append(editor)

    ensure_dirs()
    state = {"theme": name, "backup_before_apply": backup_id, "editors": applied}
    (APP_DIR / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return backup_id, applied


def current_theme():
    p = APP_DIR / "state.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("theme")
