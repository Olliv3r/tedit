import argparse
import json
from . import __version__
from .config import ensure_dirs, APP_DIR
from .detector import detect
from .backup import create_backup, list_backups, restore, reset_configs
from .theme import list_themes, apply_theme, current_theme
from .theme_preview import preview_terminal, browse_terminal, preview_nvim
from .profile import list_profiles, show, apply
from .tui import run as tui
from .diagnostics import report as debug_report
from .modern import FEATURES, LANGUAGES, load_state, set_feature, set_language, sync as modern_sync
from .nvim_manager import (
    list_presets as nvim_list, install as nvim_install, use as nvim_use,
    remove as nvim_remove, current_preset as nvim_current,
    appname as nvim_appname, config_dir as nvim_config_dir,
    run as nvim_run, doctor as nvim_doctor, update as nvim_update,
)


def parser():
    p = argparse.ArgumentParser(prog="tedit")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--version", action="version", version=f"TEdit {__version__}")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("version")
    sub.add_parser("status")
    sub.add_parser("doctor")
    dbg = sub.add_parser("debug")
    dbg.add_argument("--report", action="store_true")
    sub.add_parser("backup")
    sub.add_parser("backups")
    r = sub.add_parser("restore"); r.add_argument("id")
    sub.add_parser("reset")

    theme = sub.add_parser("theme")
    ts = theme.add_subparsers(dest="sub")
    ts.add_parser("list")
    ts.add_parser("current")
    tp = ts.add_parser("preview"); tp.add_argument("name")
    ts.add_parser("browse")
    s = ts.add_parser("set"); s.add_argument("name"); s.add_argument("--editor", action="append", dest="editors")

    nvim = sub.add_parser("nvim", help="Gerencia ambientes isolados do Neovim")
    ns = nvim.add_subparsers(dest="sub")
    ns.add_parser("list")
    ns.add_parser("current")
    ni = ns.add_parser("install"); ni.add_argument("preset"); ni.add_argument("--keep-git", action="store_true")
    nu = ns.add_parser("use"); nu.add_argument("preset")
    nr = ns.add_parser("remove"); nr.add_argument("preset")
    np = ns.add_parser("path"); np.add_argument("preset")
    ne = ns.add_parser("env"); ne.add_argument("preset", nargs="?")
    nrun = ns.add_parser("run"); nrun.add_argument("--preset"); nrun.add_argument("args", nargs=argparse.REMAINDER)
    ns.add_parser("doctor")
    nup = ns.add_parser("update"); nup.add_argument("preset", nargs="?"); nup.add_argument("--replace", action="store_true")

    nt = ns.add_parser("theme")
    nts = nt.add_subparsers(dest="theme_sub")
    ntp = nts.add_parser("preview"); ntp.add_argument("name")

    modern = ns.add_parser("modern", help="Configura o preset tedit-modern")
    ms = modern.add_subparsers(dest="modern_sub")
    ms.add_parser("status")
    ms.add_parser("sync")
    feat = ms.add_parser("feature")
    fs = feat.add_subparsers(dest="feature_sub")
    fs.add_parser("list")
    fen = fs.add_parser("enable"); fen.add_argument("name")
    fdis = fs.add_parser("disable"); fdis.add_argument("name")
    lang = ms.add_parser("lang")
    ls = lang.add_subparsers(dest="lang_sub")
    ls.add_parser("list")
    lenable = ls.add_parser("enable"); lenable.add_argument("name")
    ldisable = ls.add_parser("disable"); ldisable.add_argument("name")

    profile = sub.add_parser("profile")
    ps = profile.add_subparsers(dest="sub")
    ps.add_parser("list")
    s = ps.add_parser("show"); s.add_argument("name")
    s = ps.add_parser("apply"); s.add_argument("name")
    return p


def _require_modern():
    path = nvim_config_dir("tedit-modern")
    if not path.is_dir():
        raise ValueError("tedit-modern não está instalado. Use: tedit nvim install tedit-modern")
    return path


def main():
    ensure_dirs()
    p = parser()
    a = p.parse_args()

    try:
        if not a.cmd:
            tui(); return 0
        if a.cmd == "version":
            print(__version__)
        elif a.cmd == "status":
            for n, x in detect().items():
                print(("✓" if x["installed"] else "✗"), f"{n:8}", x["config"])
        elif a.cmd == "doctor":
            d = nvim_doctor()
            print("TEDIT DOCTOR\n")
            for n, x in detect().items():
                print(f"{n:8} {'OK' if x['installed'] else 'missing':8} {x['config']}")
            print("\nNeovim:", d["nvim"] or "missing")
            print("Git:", d["git"] or "missing")
            print("Data:", APP_DIR)
            print("Theme:", current_theme() or "none")
            print("Preset:", d["current"] or "none")
            if d["issues"]:
                print("\nIssues:")
                for issue in d["issues"]: print(" -", issue)
            else:
                print("\n✓ Nenhum problema estrutural detectado")
        elif a.cmd == "debug":
            print(debug_report())
        elif a.cmd == "backup":
            print("Backup:", create_backup())
        elif a.cmd == "backups":
            for x in list_backups(): print(x)
        elif a.cmd == "restore":
            restore(a.id); print("Restaurado:", a.id)
        elif a.cmd == "reset":
            b = create_backup("before-reset"); reset_configs(); print("Backup:", b); print("Configurações resetadas.")
        elif a.cmd == "theme":
            if a.sub == "list":
                for x in list_themes(): print(x)
            elif a.sub == "current": print(current_theme() or "none")
            elif a.sub == "preview": preview_terminal(a.name)
            elif a.sub == "browse":
                selected = browse_terminal()
                if selected: print("Selecionado:", selected); print(f"Para aplicar: tedit theme set {selected}")
            elif a.sub == "set":
                b, editors = apply_theme(a.name, a.dry_run, a.editors)
                print("DRY RUN" if a.dry_run else f"Backup: {b}")
                print("Editores:", ", ".join(editors) if editors else "nenhum")
        elif a.cmd == "nvim":
            if a.sub == "list":
                for row in nvim_list():
                    flags = ("●" if row["current"] else " ") + ("✓" if row["installed"] else "-")
                    suffix = f" @ {row['commit']}" if row.get("commit") else ""
                    print(f"{flags} {row['id']:12} {row['name']:13} {row['config']}{suffix}")
            elif a.sub == "current": print(nvim_current() or "none")
            elif a.sub == "install":
                result = nvim_install(a.preset, a.dry_run, a.keep_git)
                print("DRY RUN" if a.dry_run else "Instalado:", result["name"])
                print("Config:", result["target"]); print("NVIM_APPNAME:", result["appname"])
                if not a.dry_run: print(f"Execute: tedit nvim run --preset {result['preset']}")
            elif a.sub == "use": print("NVIM_APPNAME:", nvim_use(a.preset))
            elif a.sub == "remove": print("DRY RUN removeria:" if a.dry_run else "Removido:", nvim_remove(a.preset, a.dry_run))
            elif a.sub == "path": print(nvim_config_dir(a.preset))
            elif a.sub == "env":
                preset = a.preset or nvim_current()
                if not preset: raise ValueError("Nenhum preset ativo")
                print(f"NVIM_APPNAME={nvim_appname(preset)}")
            elif a.sub == "run": return nvim_run(a.preset, a.args)
            elif a.sub == "doctor":
                d = nvim_doctor(); print("nvim:", d["nvim"] or "missing"); print("git:", d["git"] or "missing"); print("current:", d["current"] or "none")
                for row in d["presets"]: print(("✓" if row["installed"] else "-"), row["id"], row["config"])
                for issue in d["issues"]: print("!", issue)
            elif a.sub == "update":
                for row in nvim_update(a.preset, a.dry_run, a.replace):
                    print(f"{row['preset']}: {row['action']} -> {row['target']}")
                if not a.replace: print("Nota: presets instalados sem .git são preservados; use --replace para substituí-los.")
            elif a.sub == "theme":
                if a.theme_sub == "preview": return preview_nvim(a.name)
                p.parse_args(["nvim", "theme", "-h"])
            elif a.sub == "modern":
                path = _require_modern()
                if a.modern_sub == "status": print(json.dumps(load_state(path), indent=2, ensure_ascii=False))
                elif a.modern_sub == "sync": modern_sync(path); print("tedit-modern sincronizado:", path)
                elif a.modern_sub == "feature":
                    if a.feature_sub == "list":
                        state = load_state(path); enabled = set(state["features"])
                        for key, desc in FEATURES.items(): print(("✓" if key in enabled else "-"), f"{key:12}", desc)
                    elif a.feature_sub == "enable": set_feature(path, a.name, True); print("Feature ativada:", a.name)
                    elif a.feature_sub == "disable": set_feature(path, a.name, False); print("Feature desativada:", a.name)
                elif a.modern_sub == "lang":
                    if a.lang_sub == "list":
                        state = load_state(path); enabled = set(state["languages"])
                        for key, meta in LANGUAGES.items(): print(("✓" if key in enabled else "-"), f"{key:12}", meta["lsp"])
                    elif a.lang_sub == "enable": set_language(path, a.name, True); print("Linguagem ativada:", a.name)
                    elif a.lang_sub == "disable": set_language(path, a.name, False); print("Linguagem desativada:", a.name)
            else: p.parse_args(["nvim", "-h"])
        elif a.cmd == "profile":
            if a.sub == "list":
                for x in list_profiles(): print(x)
            elif a.sub == "show": print(json.dumps(show(a.name), indent=2, ensure_ascii=False))
            elif a.sub == "apply":
                result, profile = apply(a.name, a.dry_run); b, editors = result
                print("Perfil:", a.name); print("Tema:", profile.get("theme")); print("DRY RUN" if a.dry_run else f"Backup: {b}"); print("Editores:", ", ".join(editors) if editors else "nenhum")
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        p.exit(2, f"tedit: erro: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
