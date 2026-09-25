# Changelog

## 1.0.0 - 2026-09-25

### Added
- preset próprio `tedit-modern`;
- geração local de configuração baseada em `lazy.nvim`;
- autocomplete com `blink.cmp` estável 1.x;
- Neo-tree, Telescope, lualine, gitsigns, toggleterm e nvim-treesitter;
- configuração LSP via `vim.lsp.enable`;
- `tedit nvim modern feature ...`;
- `tedit nvim modern lang ...`;
- `tedit nvim update` com modo conservador e `--replace` explícito;
- `tedit debug --report`;
- versão CLI com `tedit version` e `--version`;
- TUI atualizada;
- testes para TEdit Modern e segurança de remoção.

### Changed
- versão do projeto elevada para 1.0.0;
- README refeito como documentação principal da v1.0;
- `nvim list` pode mostrar commit quando o preset mantém `.git`;
- `doctor` passa a reportar problemas estruturais dos presets.

### Safety
- updates não substituem presets externos sem `.git` a menos que `--replace` seja informado;
- `tedit-modern` é sempre instalado sob `tedit-nvim-tedit-modern`;
- remoção continua limitada ao namespace `tedit-nvim-*`;
- previews continuam separados de operações persistentes.

## 0.5.0
- preview ANSI truecolor;
- navegador interativo de temas;
- preview real descartável em Neovim;
- testes garantindo que preview não aplique tema.

## 0.4.0
- gerenciamento isolado de NvChad, LazyVim e AstroNvim via `NVIM_APPNAME`.
