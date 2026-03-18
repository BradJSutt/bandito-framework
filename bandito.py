#!/usr/bin/env python3
"""
bandito.py  —  Bandito Framework v1.0
Metasploit-inspired modular exploitation framework for DVWA + BoF research.
"""

import atexit
import importlib.util
import os
import readline
import sys

from base_module import BaseModule
from utils import colored, cmatrix_loading, print_banner

# ---------------------------------------------------------------------------
# Add the framework root to sys.path so every module can do:
#   from dvwa_base import DVWABase
#   from base_module import BaseModule
#   from utils import colored
# regardless of which sub-folder the module file lives in.
# ---------------------------------------------------------------------------
FRAMEWORK_ROOT = os.path.dirname(os.path.abspath(__file__))
if FRAMEWORK_ROOT not in sys.path:
    sys.path.insert(0, FRAMEWORK_ROOT)

# ---------------------------------------------------------------------------
# Readline history
# ---------------------------------------------------------------------------
readline.parse_and_bind("tab: complete")
readline.set_history_length(1000)
_HISTORY_FILE = os.path.expanduser("~/.bandito_history")
if os.path.exists(_HISTORY_FILE):
    readline.read_history_file(_HISTORY_FILE)
atexit.register(readline.write_history_file, _HISTORY_FILE)
print(colored("[*] Readline enabled — up/down arrows work for history.", "green"))

# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------
MODULES:     dict[str, BaseModule] = {}
module_map:  dict[str, str]        = {}   # "01" → full module name
cat_map:     dict[str, str]        = {}   # "01" → category name


def _load_file(full_path: str, module_key: str) -> bool:
    """
    Import a single .py file, find any BaseModule subclass inside it,
    instantiate it, and register it under module_key.
    Returns True if at least one module was registered.
    """
    spec   = importlib.util.spec_from_file_location(module_key, full_path)
    module = importlib.util.module_from_spec(spec)

    # Ensure the file's own directory is importable (e.g. for relative helpers)
    file_dir = os.path.dirname(full_path)
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)

    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        print(colored(f"[-] Error loading {full_path}: {exc}", "red"))
        return False

    registered = False
    for attr in dir(module):
        obj = getattr(module, attr)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModule)
            and obj is not BaseModule
        ):
            instance = obj()
            MODULES[module_key] = instance
            print(colored(f"[+] Loaded: {module_key}", "green"))
            registered = True

    return registered


def load_modules(base_path: str = "modules"):
    """Walk the modules/ directory and load every non-dunder .py file."""
    MODULES.clear()

    if not os.path.isdir(base_path):
        print(colored(f"[-] Modules directory not found: {base_path}", "red"))
        return

    for root, _dirs, files in os.walk(base_path):
        for filename in sorted(files):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue
            full_path  = os.path.join(root, filename)
            # Build a dotted key:  "buffer_overflow.benjis_snack_vault_bo"
            rel_path   = os.path.relpath(full_path, base_path)
            module_key = rel_path.replace(os.sep, ".").removesuffix(".py")
            _load_file(full_path, module_key)


# ---------------------------------------------------------------------------
# Main REPL
# ---------------------------------------------------------------------------
def main():
    cmatrix_loading()
    print_banner()
    print(colored("[*] Bandito Framework v1.0  —  Educational Exploitation Tool", "dark_red"))
    print(colored("[*] Type 'help' for commands\n", "yellow"))

    load_modules()

    current_module: BaseModule | None = None

    while True:
        try:
            label  = current_module.name if current_module else "no module"
            prompt = colored(f"bandito ({label}) > ", "red")
            cmd    = input(prompt).strip()
            if not cmd:
                continue

            low = cmd.lower()

            # ---------------------------------------------------------------
            # Global commands (available regardless of selected module)
            # ---------------------------------------------------------------

            if low in ["exit", "quit"]:
                print(colored("[*] Goodbye!", "red"))
                break

            if low == "help":
                _print_help()
                continue

            if low == "show modules":
                _cmd_show_modules()
                continue

            if low == "browse":
                _cmd_browse()
                continue

            if low.startswith("browse "):
                _cmd_browse_category(cmd.split(maxsplit=1)[1].strip())
                continue

            if low.startswith("load "):
                _cmd_load(cmd.split(maxsplit=1)[1].strip())
                continue

            if low.startswith("use "):
                result = _cmd_use(cmd.split(maxsplit=1)[1].strip())
                if result is not None:
                    current_module = result
                continue

            if low == "back":
                current_module = None
                continue

            # ---------------------------------------------------------------
            # Delegate to the active module
            # ---------------------------------------------------------------
            if current_module:
                current_module.handle_command(cmd)
            else:
                print(colored("[-] No module selected. Try:", "red"))
                print(colored("    show modules  /  browse  /  use <name or number>", "yellow"))

        except KeyboardInterrupt:
            print()
        except Exception as exc:
            print(colored(f"[-] Error: {exc}", "red"))


# ---------------------------------------------------------------------------
# Command helpers
# ---------------------------------------------------------------------------

def _print_help():
    print(colored("\nCore Commands:", "yellow"))
    print("  use <name|number>   - Load a module  (e.g. 'use 01' or 'use buffer_overflow.benjis_snack_vault_bo')")
    print("  show modules        - List all loaded modules with index numbers")
    print("  browse              - List module categories")
    print("  browse <cat|number> - List modules inside a category")
    print("  load <path>         - Load a custom .py file or directory")
    print("  back                - Deselect current module")
    print("  exit / quit         - Exit the framework\n")


def _cmd_show_modules():
    if not MODULES:
        print(colored("  No modules loaded.", "red"))
        return

    module_map.clear()
    print(colored("\nAvailable modules:", "yellow"))
    for idx, name in enumerate(sorted(MODULES), start=1):
        key = f"{idx:02d}"
        module_map[key] = name
        print(colored(f"  {key}", "orange") + f" - {name}")
    print(colored("\nUse 'use <number>' or 'use <full.name>'", "yellow"))


def _cmd_browse():
    categories = sorted({name.split(".")[0] for name in MODULES if "." in name})
    if not categories:
        print(colored("  No categories found.", "red"))
        return

    cat_map.clear()
    print(colored("\nCategories:", "yellow"))
    for idx, cat in enumerate(categories, start=1):
        key = f"{idx:02d}"
        cat_map[key] = cat
        print(colored(f"  {key}", "orange") + f" - {cat}")
    print(colored("\nUse 'browse <number>' or 'browse <category>'", "yellow"))


def _cmd_browse_category(arg: str):
    if arg.isdigit():
        key = f"{int(arg):02d}"
        cat = cat_map.get(key)
        if not cat:
            print(colored(f"[-] No category with number {arg}. Run 'browse' first.", "red"))
            return
    else:
        cat = arg

    matching = [m for m in sorted(MODULES) if m.startswith(cat + ".")]
    if not matching:
        print(colored(f"  No modules in category '{cat}'.", "red"))
        return

    module_map.clear()
    print(colored(f"\nModules in {cat}:", "yellow"))
    for idx, name in enumerate(matching, start=1):
        key = f"{idx:02d}"
        module_map[key] = name
        print(colored(f"  {key}", "orange") + f" - {name}")
    print(colored("\nUse 'use <number>'", "yellow"))


def _cmd_load(path: str):
    if not os.path.exists(path):
        print(colored(f"[-] Path not found: {path}", "red"))
        return

    paths = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".py") and not f.startswith("__"):
                    paths.append(os.path.join(root, f))
    else:
        paths = [path]

    for fp in paths:
        stem = os.path.splitext(os.path.basename(fp))[0]
        key  = f"custom.{stem}"
        if not _load_file(fp, key):
            print(colored(f"[-] No BaseModule subclass found in {fp}", "red"))


def _cmd_use(arg: str) -> BaseModule | None:
    """Resolve arg to a module name, return the instance or None."""
    if arg.isdigit():
        key = f"{int(arg):02d}"
        name = module_map.get(key)
        if not name:
            print(colored(f"[-] No module with number {arg}. Run 'show modules' or 'browse' first.", "red"))
            return None
    else:
        name = arg

    instance = MODULES.get(name)
    if not instance:
        print(colored(f"[-] Module '{name}' not found.", "red"))
        print(colored("    Try 'show modules' or 'browse <category>'", "yellow"))
        return None

    print(colored(f"[+] Module loaded: {name}", "green"))
    if hasattr(instance, "show_help"):
        instance.show_help()
    return instance


if __name__ == "__main__":
    main()
