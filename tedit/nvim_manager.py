from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from .config import APP_DIR, ensure_dirs
from .layout import DEFAULT_LAYOUT, LAYOUTS, normalize_layout, runtime_script_path

PRESETS = {
    "nvchad": {
        "name": "NvChad",
        "repo": "https://github.com/NvChad/starter.git",
        "description": "UI moderna, temas, file tree, Telescope e base para LSP/autocomplete.",
        "kind": "git",
    },
    "lazyvim": {
        "name": "LazyVim",
        "repo": "https://github.com/LazyVim/starter.git",
        "description": "Distribuição IDE baseada em lazy.nvim, LSP, completion e extras.",
        "kind": "git",
    },
    "astronvim": {
        "name": "AstroNvim",
        "repo": "https://github.com/AstroNvim/template.git",
        "description": "Configuração extensível com UI, LSP, completion e ferramentas de IDE.",
        "kind": "git",
    },
    "tedit-modern": {
        "name": "TEdit Modern",
        "repo": None,
        "description": "Preset próprio do TEdit com lazy.nvim, LSP, completion, explorer, Telescope e UI moderna.",
        "kind": "generated",
    },
}

STATE_FILE = APP_DIR / "nvim.json"
APP_PREFIX = "tedit-nvim-"


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def appname(preset: str) -> str:
    _get_preset(preset)
    return APP_PREFIX + preset


def config_dir(preset: str) -> Path:
    return _xdg_config_home() / appname(preset)


def _get_preset(preset: str) -> dict:
    key = preset.lower()
    if key not in PRESETS:
        raise ValueError(f"Preset desconhecido: {preset}")
    return PRESETS[key]


def _read_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_state(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _git_commit(target: Path) -> str | None:
    if not (target / ".git").exists() or not shutil.which("git"):
        return None
    try:
        out = subprocess.run(["git", "-C", str(target), "rev-parse", "--short", "HEAD"], text=True, capture_output=True, check=False, timeout=4)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def list_presets() -> list[dict]:
    current = current_preset()
    rows = []
    for key, meta in PRESETS.items():
        target = config_dir(key)
        rows.append({
            "id": key,
            "name": meta["name"],
            "description": meta["description"],
            "installed": target.is_dir(),
            "current": key == current,
            "appname": appname(key),
            "config": str(target),
            "kind": meta["kind"],
            "commit": _git_commit(target),
        })
    return rows


def current_preset() -> str | None:
    value = _read_state().get("current")
    return value if value in PRESETS else None




def current_layout() -> str:
    value = _read_state().get("layout", DEFAULT_LAYOUT)
    return value if value in LAYOUTS else DEFAULT_LAYOUT


def set_layout(mode: str) -> str:
    mode = normalize_layout(mode)
    state = _read_state()
    state["layout"] = mode
    _write_state(state)
    return mode

def use(preset: str) -> str:
    preset = preset.lower()
    _get_preset(preset)
    if not config_dir(preset).is_dir():
        raise ValueError(f"Preset não instalado: {preset}. Use: tedit nvim install {preset}")
    state = _read_state()
    state["current"] = preset
    _write_state(state)
    return appname(preset)


def install(preset: str, dry_run: bool = False, keep_git: bool = False) -> dict:
    preset = preset.lower()
    meta = _get_preset(preset)
    target = config_dir(preset)
    if target.exists():
        raise ValueError(f"O preset {preset} já está instalado em {target}")

    result = {
        "preset": preset,
        "name": meta["name"],
        "repo": meta["repo"],
        "target": str(target),
        "appname": appname(preset),
        "dry_run": dry_run,
    }
    if dry_run:
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    if meta["kind"] == "generated":
        from .modern import create
        create(target)
    else:
        if not shutil.which("git"):
            raise RuntimeError("git não encontrado no PATH")
        cmd = ["git", "clone", "--depth", "1", meta["repo"], str(target)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            raise RuntimeError(f"Falha ao clonar {meta['name']} (git exit {exc.returncode})") from exc
        if not keep_git:
            shutil.rmtree(target / ".git", ignore_errors=True)

    state = _read_state()
    installed = state.setdefault("installed", {})
    installed[preset] = {"appname": appname(preset), "config": str(target), "source": meta["repo"] or "generated"}
    if not state.get("current"):
        state["current"] = preset
    _write_state(state)
    return result


def update(preset: str | None = None, dry_run: bool = False, replace: bool = False) -> list[dict]:
    chosen = [preset.lower()] if preset else [r["id"] for r in list_presets() if r["installed"]]
    results = []
    for key in chosen:
        meta = _get_preset(key)
        target = config_dir(key)
        if not target.is_dir():
            raise ValueError(f"Preset não instalado: {key}")
        if meta["kind"] == "generated":
            results.append({"preset": key, "action": "regenerate", "target": str(target), "dry_run": dry_run})
            if not dry_run:
                from .modern import sync
                sync(target)
            continue

        if (target / ".git").is_dir():
            results.append({"preset": key, "action": "git-pull", "target": str(target), "dry_run": dry_run})
            if not dry_run:
                subprocess.run(["git", "-C", str(target), "pull", "--ff-only"], check=True)
            continue

        if not replace:
            results.append({"preset": key, "action": "skipped-no-git", "target": str(target), "dry_run": dry_run})
            continue
        if not shutil.which("git"):
            raise RuntimeError("git não encontrado no PATH")
        results.append({"preset": key, "action": "replace", "target": str(target), "dry_run": dry_run})
        if dry_run:
            continue
        with tempfile.TemporaryDirectory(prefix="tedit-update-") as temp:
            fresh = Path(temp) / key
            subprocess.run(["git", "clone", "--depth", "1", meta["repo"], str(fresh)], check=True)
            shutil.rmtree(fresh / ".git", ignore_errors=True)
            backup = target.with_name(target.name + ".pre-update")
            if backup.exists():
                shutil.rmtree(backup)
            target.rename(backup)
            try:
                shutil.copytree(fresh, target)
            except Exception:
                if target.exists():
                    shutil.rmtree(target, ignore_errors=True)
                backup.rename(target)
                raise
            shutil.rmtree(backup, ignore_errors=True)
    return results


def remove(preset: str, dry_run: bool = False) -> Path:
    preset = preset.lower()
    _get_preset(preset)
    target = config_dir(preset)
    if target.name != appname(preset) or not target.name.startswith(APP_PREFIX):
        raise RuntimeError("Recusando remover diretório fora do namespace do TEdit")
    if not target.exists():
        raise ValueError(f"Preset não instalado: {preset}")
    if dry_run:
        return target

    shutil.rmtree(target)
    state = _read_state()
    state.get("installed", {}).pop(preset, None)
    if state.get("current") == preset:
        state["current"] = next((row["id"] for row in list_presets() if row["installed"] and row["id"] != preset), None)
    _write_state(state)
    return target


def environment(preset: str | None = None) -> dict[str, str]:
    chosen = (preset or current_preset() or "").lower()
    if not chosen:
        raise ValueError("Nenhum preset ativo. Use: tedit nvim use <preset>")
    _get_preset(chosen)
    if not config_dir(chosen).is_dir():
        raise ValueError(f"Preset não instalado: {chosen}")
    env = os.environ.copy()
    env["NVIM_APPNAME"] = appname(chosen)
    return env


def run(preset: str | None = None, args: Iterable[str] = (), layout: str | None = None) -> int:
    if not shutil.which("nvim"):
        raise RuntimeError("nvim não encontrado no PATH")
    env = environment(preset)
    mode = normalize_layout(layout or current_layout())
    env["TEDIT_NVIM_LAYOUT"] = mode

    cmd = ["nvim"]
    if mode != "native":
        script = runtime_script_path()
        env["TEDIT_LAYOUT_SCRIPT"] = str(script)
        cmd.extend(["--cmd", "lua dofile(vim.env.TEDIT_LAYOUT_SCRIPT)"])
    cmd.extend(args)
    return subprocess.call(cmd, env=env)


def doctor() -> dict:
    nvim = shutil.which("nvim")
    git = shutil.which("git")
    current = current_preset()
    issues = []
    if not nvim:
        issues.append("Neovim não encontrado")
    if not git:
        issues.append("Git não encontrado")
    if current and not config_dir(current).is_dir():
        issues.append(f"Preset ativo ausente: {current}")
    for row in list_presets():
        if row["installed"] and not (Path(row["config"]) / "init.lua").exists():
            issues.append(f"{row['id']}: init.lua ausente")
    return {"nvim": nvim, "git": git, "current": current, "layout": current_layout(), "presets": list_presets(), "issues": issues}
