# Changelog

## 1.1.1

- Corrige o gutter largo em telas estreitas/Termux.
- No modo compacto, sinais de diagnóstico/Git compartilham a coluna dos números (`signcolumn=number`).
- Remove a coluna de folds (`foldcolumn=0`) e reduz `numberwidth` para 2.
- Limpa `statuscolumn` customizada no modo compacto para recuperar largura útil.
- Aplica o ajuste ao TEdit Modern, previews e ao shim temporário de NvChad, LazyVim e AstroNvim.

## 1.1.0

- Adiciona layout responsivo `auto`, `compact`, `desktop` e `native`.
- TEdit Modern passa a ajustar Neo-tree e Telescope para telas estreitas.
- `tedit nvim run --layout <modo>` permite override por execução.
- `tedit nvim layout <modo>` define o modo padrão para todos os presets.
- NvChad, LazyVim e AstroNvim recebem um shim de layout temporário, sem alteração de seus arquivos de configuração.
- Sidebars Neo-tree/NvimTree/Aerial/Outline e componentes compatíveis são redimensionados durante a execução.
- Adiciona testes para responsividade e para garantir que presets externos não sejam modificados pelo shim.

## 1.0.2 - 2026-09-25

### Added

- galeria com previews separados para todos os sete temas incluídos;
- links no README para os projetos/origens visuais de Tokyo Night, Catppuccin, VS Code Dark Modern, GitHub Dark, Gruvbox, Nord e Atom One Dark;
- explicação mais detalhada da arquitetura e do isolamento do `tedit-modern`.

### Documentation

- deixa explícito que os previews do README são ilustrativos e que o preview real deve ser feito pelos comandos do TEdit.

## 1.0.1 - 2026-09-25

### Fixed

- corrige o mapeamento `Ctrl+\` do ToggleTerm no preset `tedit-modern`;
- evita `E5112: invalid escape sequence` no `init.lua` gerado;
- o atalho agora é emitido como long string Lua (`[[<C-\>]]`), sem escape ambíguo.

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
