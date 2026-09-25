from pathlib import Path
import json
from .theme import apply_theme

PROFILES_DIR = Path(__file__).resolve().parent / "profiles"

def list_profiles():
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))

def load(name):
    p = PROFILES_DIR / f"{name}.json"
    if not p.exists():
        raise ValueError(f"Perfil não encontrado: {name}")
    return json.loads(p.read_text(encoding="utf-8"))

def show(name):
    return load(name)

def apply(name, dry_run=False):
    profile = load(name)
    theme = profile.get("theme")
    if not theme:
        raise ValueError("Perfil sem tema")
    return apply_theme(theme, dry_run=dry_run), profile
