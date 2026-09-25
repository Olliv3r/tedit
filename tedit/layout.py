from __future__ import annotations

from pathlib import Path

from .config import APP_DIR, ensure_dirs

LAYOUTS = ("auto", "compact", "desktop", "native")
DEFAULT_LAYOUT = "auto"


def normalize_layout(value: str | None) -> str:
    mode = (value or DEFAULT_LAYOUT).lower()
    if mode not in LAYOUTS:
        raise ValueError(f"Layout desconhecido: {value}. Use: {', '.join(LAYOUTS)}")
    return mode


def runtime_script_path() -> Path:
    ensure_dirs()
    target = APP_DIR / "runtime" / "nvim_layout.lua"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_runtime_lua(), encoding="utf-8")
    return target


def render_runtime_lua() -> str:
    # This shim deliberately avoids changing plugin configuration files. It only
    # adjusts the running Neovim instance and reacts to resizes/filetype events.
    return r'''-- TEdit responsive layout shim. Loaded only for this Neovim process.
local requested = (vim.env.TEDIT_NVIM_LAYOUT or "auto"):lower()
if requested == "native" then
  return
end

local function mode()
  if requested ~= "auto" then
    return requested
  end
  if vim.o.columns < 100 then
    return "compact"
  end
  return "desktop"
end

local sidebar_filetypes = {
  ["neo-tree"] = true,
  ["NvimTree"] = true,
  ["aerial"] = true,
  ["Outline"] = true,
  ["snacks_picker_list"] = true,
  ["snacks_layout_box"] = true,
}

local function sidebar_width()
  if mode() == "compact" then
    return math.max(18, math.min(24, math.floor(vim.o.columns * 0.30)))
  end
  return math.max(26, math.min(36, math.floor(vim.o.columns * 0.25)))
end

local function apply_globals()
  vim.opt.winminwidth = 1
  vim.opt.winwidth = mode() == "compact" and 8 or 20
  vim.opt.equalalways = false

  if mode() == "compact" then
    vim.opt.showtabline = 1
  end
end

local function apply_window(win)
  if not win or not vim.api.nvim_win_is_valid(win) then
    return
  end
  local buf = vim.api.nvim_win_get_buf(win)
  local ok_ft, ft = pcall(function() return vim.bo[buf].filetype end)
  local ok_bt, bt = pcall(function() return vim.bo[buf].buftype end)
  if ok_ft and sidebar_filetypes[ft] then
    pcall(vim.api.nvim_win_set_width, win, sidebar_width())
    return
  end

  -- On narrow terminals reclaim the gutter columns normally reserved for
  -- signs/folds.  Signs still work: `signcolumn=number` draws them in the
  -- number column instead of consuming a separate column.
  if mode() == "compact" and ok_bt and bt == "" then
    pcall(function() vim.wo[win].numberwidth = 2 end)
    pcall(function() vim.wo[win].signcolumn = "number" end)
    pcall(function() vim.wo[win].foldcolumn = "0" end)
    pcall(function() vim.wo[win].statuscolumn = "" end)
  end
end

local function apply_all()
  apply_globals()
  for _, win in ipairs(vim.api.nvim_list_wins()) do
    apply_window(win)
  end
end

local group = vim.api.nvim_create_augroup("TEditResponsiveLayout", { clear = true })
vim.api.nvim_create_autocmd({ "VimEnter", "UIEnter", "VimResized", "WinEnter", "FileType" }, {
  group = group,
  callback = function()
    vim.schedule(apply_all)
  end,
})

apply_all()
'''
