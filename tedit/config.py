from pathlib import Path
import os

APP_DIR = Path(os.environ.get("TEDIT_DATA_DIR", Path.home() / ".local/share/tedit"))
BACKUP_DIR = APP_DIR / "backups"
STATE_FILE = APP_DIR / "state.json"


def ensure_dirs():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def config_paths():
    home = Path.home()
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return {
        "nvim": xdg / "nvim",
        "micro": xdg / "micro",
        "helix": xdg / "helix",
        "vim": home / ".vim",
        "vscode": xdg / "Code" / "User",
        "vscodium": xdg / "VSCodium" / "User",
        "atom": home / ".atom",
        "pulsar": home / ".pulsar",
    }
