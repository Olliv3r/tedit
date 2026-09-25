from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import APP_DIR
from .nvim_manager import current_preset, current_layout, list_presets, config_dir


def _version(cmd: list[str]) -> str | None:
    if not shutil.which(cmd[0]):
        return None
    try:
        out = subprocess.run(cmd, text=True, capture_output=True, timeout=4, check=False)
        text = (out.stdout or out.stderr).strip().splitlines()
        return text[0] if text else None
    except (OSError, subprocess.SubprocessError):
        return None


def report() -> str:
    current = current_preset()
    lines = [
        f"TEdit: {__version__}",
        f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {platform.python_version()}",
        f"Neovim: {_version(['nvim', '--version']) or 'missing'}",
        f"Git: {_version(['git', '--version']) or 'missing'}",
        f"Current preset: {current or 'none'}",
        f"Layout: {current_layout()}",
        f"TEdit data: {APP_DIR}",
        f"XDG_CONFIG_HOME: {os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))}",
        "",
        "Presets:",
    ]
    for row in list_presets():
        marker = "OK" if row["installed"] else "--"
        lines.append(f"  {marker} {row['id']}: {row['config']}")
    if current:
        lines.extend(["", f"Active config: {config_dir(current)}", f"NVIM_APPNAME: tedit-nvim-{current}"])
    return "\n".join(lines)
