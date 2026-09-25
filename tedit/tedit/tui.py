from . import __version__
from .detector import detect
from .theme import list_themes, current_theme, apply_theme
from .theme_preview import render_terminal_preview
from .backup import create_backup, list_backups, restore
from .nvim_manager import list_presets as nvim_list, current_preset as nvim_current, use as nvim_use


def clear(): print("\033[2J\033[H", end="")
def pause(): input("\nEnter...")


def run():
    while True:
        clear()
        print("╭────────────────────────────────────────────╮")
        print(f"│              TEDIT v{__version__:<20}│")
        print("╰────────────────────────────────────────────╯")
        print(f"Tema: {current_theme() or 'nenhum'}  │  Neovim: {nvim_current() or 'nenhum'}\n")
        print("[1] Status dos editores")
        print("[2] Temas / preview")
        print("[3] Aplicar tema")
        print("[4] Presets Neovim")
        print("[5] Backup")
        print("[6] Restaurar backup")
        print("[q] Sair")
        choice = input("\n> ").strip().lower()
        if choice == "q": return
        if choice == "1":
            clear()
            for n, x in detect().items(): print(("✓" if x["installed"] else "✗"), n, "-", x["config"])
            pause()
        elif choice == "2":
            themes = list_themes(); index = 0
            while True:
                clear(); print(render_terminal_preview(themes[index])); print(f"\n[{index+1}/{len(themes)}] n próximo · p anterior · q voltar")
                k = input("> ").strip().lower()
                if k == "q": break
                index = (index + (1 if k != "p" else -1)) % len(themes)
        elif choice == "3":
            clear(); themes = list_themes()
            for i, x in enumerate(themes, 1): print(f"[{i}] {x}")
            try:
                i = int(input("\nTema: ")) - 1; backup, editors = apply_theme(themes[i]); print("\nBackup:", backup); print("Aplicado:", ", ".join(editors) or "nenhum")
            except (ValueError, IndexError) as e: print("Erro:", e)
            pause()
        elif choice == "4":
            clear(); rows = nvim_list()
            for i, row in enumerate(rows, 1):
                flags = ("●" if row["current"] else " ") + ("✓" if row["installed"] else "-")
                print(f"[{i}] {flags} {row['id']:12} {row['name']}")
            print("\nDigite o número de um preset instalado para torná-lo ativo, ou Enter para voltar.")
            value = input("> ").strip()
            if value:
                try:
                    row = rows[int(value)-1]
                    if not row["installed"]: print("Preset não instalado. Use a CLI: tedit nvim install", row["id"])
                    else: nvim_use(row["id"]); print("Ativo:", row["id"])
                except (ValueError, IndexError) as e: print("Erro:", e)
                pause()
        elif choice == "5": print("\nBackup:", create_backup()); pause()
        elif choice == "6":
            clear(); bs = list_backups()
            for i, x in enumerate(bs, 1): print(f"[{i}] {x}")
            try: restore(bs[int(input("\nBackup: "))-1]); print("Restaurado.")
            except (ValueError, IndexError) as e: print("Erro:", e)
            pause()
