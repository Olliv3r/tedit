from __future__ import annotations

import json
from pathlib import Path

FEATURES = {
    "completion": "Autocomplete com blink.cmp",
    "explorer": "File explorer com neo-tree",
    "telescope": "Busca de arquivos/texto com Telescope",
    "statusline": "Statusline com lualine",
    "git": "Indicadores Git com gitsigns",
    "terminal": "Terminal integrado com toggleterm",
    "treesitter": "Parsers e highlighting com nvim-treesitter",
}

LANGUAGES = {
    "python": {"lsp": "pyright", "parser": "python", "tools": ["pyright"]},
    "javascript": {"lsp": "ts_ls", "parser": "javascript", "tools": ["typescript-language-server"]},
    "typescript": {"lsp": "ts_ls", "parser": "typescript", "tools": ["typescript-language-server"]},
    "lua": {"lsp": "lua_ls", "parser": "lua", "tools": ["lua-language-server"]},
    "rust": {"lsp": "rust_analyzer", "parser": "rust", "tools": ["rust-analyzer"]},
    "go": {"lsp": "gopls", "parser": "go", "tools": ["gopls"]},
    "bash": {"lsp": "bashls", "parser": "bash", "tools": ["bash-language-server"]},
    "json": {"lsp": "jsonls", "parser": "json", "tools": ["vscode-json-language-server"]},
    "html": {"lsp": "html", "parser": "html", "tools": ["vscode-html-language-server"]},
    "css": {"lsp": "cssls", "parser": "css", "tools": ["vscode-css-language-server"]},
}

DEFAULT_FEATURES = list(FEATURES)
DEFAULT_LANGUAGES = ["python", "javascript", "typescript", "lua", "json", "html", "css"]
STATE_NAME = ".tedit-modern.json"


def default_state() -> dict:
    return {"features": DEFAULT_FEATURES.copy(), "languages": DEFAULT_LANGUAGES.copy(), "theme": "tokyo-night"}


def state_path(config_dir: Path) -> Path:
    return config_dir / STATE_NAME


def load_state(config_dir: Path) -> dict:
    p = state_path(config_dir)
    if not p.exists():
        return default_state()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_state()
    state = default_state()
    state.update({k: v for k, v in data.items() if k in state})
    state["features"] = [x for x in state.get("features", []) if x in FEATURES]
    state["languages"] = [x for x in state.get("languages", []) if x in LANGUAGES]
    return state


def save_state(config_dir: Path, state: dict) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    state_path(config_dir).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _lua_list(values: list[str]) -> str:
    return "{ " + ", ".join(json.dumps(v) for v in values) + " }"


def render_init(state: dict) -> str:
    features = set(state.get("features", []))
    langs = [LANGUAGES[x] for x in state.get("languages", []) if x in LANGUAGES]
    lsps = sorted({x["lsp"] for x in langs})
    parsers = sorted({x["parser"] for x in langs})

    specs: list[str] = [
        '''{ "folke/tokyonight.nvim", lazy = false, priority = 1000, config = function() vim.cmd.colorscheme("tokyonight-night") end }''',
        '''{ "nvim-lua/plenary.nvim", lazy = true }''',
        '''{ "neovim/nvim-lspconfig", lazy = false }''',
    ]
    if "completion" in features:
        specs.append('''{ "saghen/blink.cmp", version = "1.*", dependencies = { "rafamadriz/friendly-snippets" }, opts = { keymap = { preset = "super-tab" }, completion = { documentation = { auto_show = true } }, sources = { default = { "lsp", "path", "snippets", "buffer" } }, fuzzy = { implementation = "lua" } } }''')
    if "explorer" in features:
        specs.append('''{ "nvim-neo-tree/neo-tree.nvim", branch = "v3.x", dependencies = { "nvim-lua/plenary.nvim", "MunifTanjim/nui.nvim", "nvim-tree/nvim-web-devicons" }, keys = { { "<leader>e", "<cmd>Neotree toggle<cr>", desc = "Explorer" } }, opts = { filesystem = { follow_current_file = { enabled = true } } } }''')
    if "telescope" in features:
        specs.append('''{ "nvim-telescope/telescope.nvim", dependencies = { "nvim-lua/plenary.nvim" }, keys = { { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" }, { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live grep" }, { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" } }, opts = {} }''')
    if "statusline" in features:
        specs.append('''{ "nvim-lualine/lualine.nvim", dependencies = { "nvim-tree/nvim-web-devicons" }, opts = { options = { theme = "tokyonight", globalstatus = true } } }''')
    if "git" in features:
        specs.append('''{ "lewis6991/gitsigns.nvim", opts = {} }''')
    if "terminal" in features:
        specs.append('''{ "akinsho/toggleterm.nvim", version = "*", keys = { { "<C-\\>", "<cmd>ToggleTerm<cr>", desc = "Terminal" } }, opts = { direction = "float" } }''')
    if "treesitter" in features:
        specs.append('''{ "nvim-treesitter/nvim-treesitter", lazy = false, build = ":TSUpdate", config = function() local ts = require("nvim-treesitter"); ts.setup({}); local parsers = %s; if #parsers > 0 then ts.install(parsers) end end }''' % _lua_list(parsers))

    spec_text = ",\n  ".join(specs)
    lsp_text = "\n".join(f'pcall(vim.lsp.enable, {json.dumps(name)})' for name in lsps)

    return f'''-- Generated by TEdit. Re-run `tedit nvim modern sync` after changing features/languages.\nvim.g.mapleader = " "\nvim.g.maplocalleader = "\\\\"\n\nvim.opt.number = true\nvim.opt.relativenumber = true\nvim.opt.termguicolors = true\nvim.opt.signcolumn = "yes"\nvim.opt.cursorline = true\nvim.opt.updatetime = 250\nvim.opt.splitright = true\nvim.opt.splitbelow = true\nvim.opt.ignorecase = true\nvim.opt.smartcase = true\nvim.opt.clipboard = "unnamedplus"\n\nlocal lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"\nif not (vim.uv or vim.loop).fs_stat(lazypath) then\n  local repo = "https://github.com/folke/lazy.nvim.git"\n  local out = vim.fn.system({{ "git", "clone", "--filter=blob:none", "--branch=stable", repo, lazypath }})\n  if vim.v.shell_error ~= 0 then\n    vim.api.nvim_echo({{{{ "Failed to clone lazy.nvim:\\n", "ErrorMsg" }}, {{ out, "WarningMsg" }}}}, true, {{}})\n    return\n  end\nend\nvim.opt.rtp:prepend(lazypath)\n\nrequire("lazy").setup({{\n  spec = {{\n  {spec_text}\n  }},\n  install = {{ colorscheme = {{ "tokyonight", "habamax" }} }},\n  checker = {{ enabled = true, notify = false }},\n  change_detection = {{ notify = false }},\n}})\n\n{lsp_text}\n\nvim.keymap.set("n", "<leader>w", "<cmd>w<cr>", {{ desc = "Save" }})\nvim.keymap.set("n", "<leader>q", "<cmd>q<cr>", {{ desc = "Quit" }})\nvim.keymap.set("n", "gd", vim.lsp.buf.definition, {{ desc = "Go to definition" }})\nvim.keymap.set("n", "gr", vim.lsp.buf.references, {{ desc = "References" }})\nvim.keymap.set("n", "K", vim.lsp.buf.hover, {{ desc = "Hover" }})\nvim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, {{ desc = "Rename" }})\nvim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, {{ desc = "Code action" }})\n'''


def sync(config_dir: Path) -> dict:
    state = load_state(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    save_state(config_dir, state)
    (config_dir / "init.lua").write_text(render_init(state), encoding="utf-8")
    return state


def create(config_dir: Path) -> dict:
    if config_dir.exists() and any(config_dir.iterdir()):
        raise ValueError(f"Diretório não vazio: {config_dir}")
    config_dir.mkdir(parents=True, exist_ok=True)
    state = default_state()
    save_state(config_dir, state)
    (config_dir / "init.lua").write_text(render_init(state), encoding="utf-8")
    return state


def set_feature(config_dir: Path, feature: str, enabled: bool) -> dict:
    if feature not in FEATURES:
        raise ValueError(f"Feature desconhecida: {feature}")
    state = load_state(config_dir)
    values = set(state["features"])
    (values.add if enabled else values.discard)(feature)
    state["features"] = [x for x in FEATURES if x in values]
    save_state(config_dir, state)
    return sync(config_dir)


def set_language(config_dir: Path, language: str, enabled: bool) -> dict:
    if language not in LANGUAGES:
        raise ValueError(f"Linguagem desconhecida: {language}")
    state = load_state(config_dir)
    values = set(state["languages"])
    (values.add if enabled else values.discard)(language)
    state["languages"] = [x for x in LANGUAGES if x in values]
    save_state(config_dir, state)
    return sync(config_dir)
