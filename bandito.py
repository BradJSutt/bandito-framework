# bandito.py
import os
import importlib

from utils import printbanner, colored, cmatrixloading, printcolored, ok, info, warn, fail

MODULES = {}

def loadmodules():
    global MODULES
    MODULES = {}
    toolsdir = "tools"
    info("Scanning tools directory...")

    if not os.path.isdir(toolsdir):
        fail("tools directory not found!")
        return

    for toolname in os.listdir(toolsdir):
        toolpath = os.path.join(toolsdir, toolname)
        if not os.path.isdir(toolpath):
            continue
        if toolname.startswith("__"):
            continue

        mainfile = os.path.join(toolpath, "main.py")
        if not os.path.isfile(mainfile):
            continue

        try:
            module = importlib.import_module(f"tools.{toolname}.main")
            if hasattr(module, "Tool"):
                MODULES[toolname] = module.Tool()
                ok(f"Loaded tool {toolname}")
            else:
                warn(f"{toolname}/main.py has no Tool class")
        except Exception as e:
            fail(f"Failed to load tool {toolname}: {e}")

def main():
    cmatrixloading()
    printbanner()
    printcolored("Bandito Framework v1.0 - Educational Exploitation Tool", "darkred")
    printcolored("Type help for commands", "yellow")
    loadmodules()

    currenttool = None

    while True:
        try:
            prompt = colored(f"bandito({currenttool.name if currenttool else 'no tool'}) > ", "red")
            cmd = input(prompt).strip()
            if not cmd:
                continue

            low = cmd.lower()

            # Global "back" always works
            if low in ("back",):
                if currenttool:
                    info("Returning to main Bandito menu...")
                currenttool = None
                continue

            # If a tool is selected, give it first shot (except exit/help/show/use)
            if currenttool and not (low in ("help", "show tools") or low.startswith("use ")):
                # Let tool decide what "exit/quit" means in its context
                currenttool.handlecommand(cmd)
                continue

            if low in ("exit", "quit"):
                info("Goodbye!")
                break

            if low == "help":
                printcolored("Commands:", "yellow")
                print("  use <tool>      - Select a tool (e.g. use WebRCE)")
                print("  show tools      - List available tools")
                print("  back            - Return to main menu / unload tool")
                print("  exit | quit     - Exit framework")
                continue

            if low == "show tools":
                printcolored("Available tools:", "yellow")
                for t in MODULES.keys():
                    printcolored(f" - {t}", "orange")
                continue

            if low.startswith("use "):
                toolname = cmd.split(maxsplit=1)[1].strip()
                # case-insensitive match
                chosen = None
                for key in MODULES:
                    if key.lower() == toolname.lower():
                        chosen = key
                        break
                if not chosen:
                    fail(f"Tool '{toolname}' not found")
                    continue
                currenttool = MODULES[chosen]
                ok(f"Tool loaded: {chosen}")
                # optional: show module help on load
                if hasattr(currenttool, "showhelp"):
                    currenttool.showhelp()
                continue

            warn("No tool selected. Use 'use <tool>' first.")

        except KeyboardInterrupt:
            print()
            warn("Interrupted (Ctrl+C). Type 'exit' to quit.")
        except Exception as e:
            fail(f"Error: {e}")

if __name__ == "__main__":
    main()
