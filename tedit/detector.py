import shutil
from .config import config_paths

EDITOR_BINARIES = {
    "nvim": ("nvim",),
    "micro": ("micro",),
    "helix": ("hx",),
    "vim": ("vim",),
    "vscode": ("code",),
    "vscodium": ("codium",),
    "atom": ("atom",),
    "pulsar": ("pulsar",),
}


def detect():
    paths = config_paths()
    result = {}
    for name, binaries in EDITOR_BINARIES.items():
        binary = next((b for b in binaries if shutil.which(b)), binaries[0])
        result[name] = {
            "binary": binary,
            "installed": any(shutil.which(b) for b in binaries),
            "config": paths[name],
        }
    return result
