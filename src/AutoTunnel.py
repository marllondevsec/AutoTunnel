#!/usr/bin/env python3
"""
AutoTunnel - Minimal, numeric menus, colored (rich), auto-install cloudflared,
and default to the user's current working directory (pwd).
"""
import os, sys, json, shutil, subprocess, threading, time, re, importlib.util
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ---------------- Paths / config ----------------
HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "autotunnel"
CONFIG_PATH = CONFIG_DIR / "config.json"
DATA_DIR = HOME / ".local" / "share" / "autotunnel"
LOG_DIR = DATA_DIR / "logs"
PID_DIR = DATA_DIR / "pids"
PLUGIN_DIR = Path(__file__).parent / "tunnels"
LANG_DIR = Path(__file__).parent / "lang"
LOCAL_BIN = DATA_DIR / "bin"

for d in (CONFIG_DIR, DATA_DIR, LOG_DIR, PID_DIR, LOCAL_BIN):
    d.mkdir(parents=True, exist_ok=True)

# Default config: note default_dir uses current working directory (pwd)
DEFAULT_CONFIG = {
    "language": "pt",
    "default_port": 1337,
    "default_dir": str(Path.cwd()),
    "installed_tunnels": {}
}

# ---------------- Helpful: ensure rich ----------------
def ensure_rich():
    try:
        import rich
        return rich
    except Exception:
        print("Instalando dependência 'rich' para menu colorido...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "rich"], check=False)
        try:
            import rich
            return rich
        except Exception:
            return None

rich = ensure_rich()
if rich:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
else:
    console = None

# ---------------- Config / i18n ----------------
def load_config():
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # ensure default_dir is at least current cwd if missing
            if "default_dir" not in cfg or not cfg["default_dir"]:
                cfg["default_dir"] = str(Path.cwd())
            return cfg
        except Exception:
            pass
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG.copy()

cfg = load_config()
LANG = cfg.get("language", "pt")

def load_lang(lang):
    f = LANG_DIR / f"{lang}.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))

I18N = load_lang(LANG)
def tr(key, *args):
    s = I18N.get(key, key)
    for i,a in enumerate(args, start=1):
        s = s.replace("{" + str(i) + "}", str(a))
    return s

# ---------------- HttpServer minimal ----------------
class HttpServer:
    def __init__(self):
        self.httpd = None
        self.thread = None
        self.port = None
        self.directory = None

    def start(self, port:int, directory:str):
        if self.httpd:
            return False
        directory = str(Path(directory).expanduser().resolve())
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=directory, **kwargs)
        # ThreadingHTTPServer so server runs in same process but background thread
        self.httpd = ThreadingHTTPServer(("", int(port)), handler)
        self.port = port
        self.directory = directory
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        (PID_DIR / "http_server.json").write_text(json.dumps({"pid": os.getpid(), "port": port, "dir": directory}))
        return True

    def stop(self):
        if not self.httpd:
            return False
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd = None
        try:
            (PID_DIR / "http_server.json").unlink()
        except:
            pass
        return True

http_server = HttpServer()

# ---------------- Plugin loader ----------------
PLUGINS = {}  # index(int) -> (name, instance)
def load_plugins():
    PLUGINS.clear()
    if not PLUGIN_DIR.exists():
        return
    idx = 1
    for p in sorted(PLUGIN_DIR.glob("*.py")):
        name = p.stem
        spec = importlib.util.spec_from_file_location(f"autotunnel.plugins.{name}", p)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print("Erro carregando plugin", name, e)
            continue
        if hasattr(mod, "TunnelPlugin"):
            try:
                inst = mod.TunnelPlugin()
                PLUGINS[idx] = (inst.name(), inst)
                idx += 1
            except Exception as e:
                print("Erro inicializando plugin", name, e)

# ---------------- Utils UI ----------------
def cprint(text, style=None):
    if console:
        console.print(text, style=style)
    else:
        print(text)

def print_header():
    if console:
        console.print(Panel("[bold cyan]AutoTunnel[/bold cyan]\n[green]Servidor rápido + túnel (cloudflared)[/green]"), justify="center")
    else:
        print("\n=== AutoTunnel ===\nServidor rápido + túnel (cloudflared)\n")

def numeric_choice(prompt_text, options):
    """
    options: list of strings
    prints numbered options, returns selected index (1-based) or None
    """
    if console:
        table = Table.grid(padding=(0,1))
        for i,opt in enumerate(options, start=1):
            table.add_row(f"[bold yellow]{i})[/bold yellow] {opt}")
        console.print(table)
        choice = console.input(f"[bold cyan]{prompt_text}[/bold cyan] ")
    else:
        for i,opt in enumerate(options, start=1):
            print(f"{i}) {opt}")
        choice = input(prompt_text + " ")
    try:
        n = int(choice.strip())
        if 1 <= n <= len(options):
            return n
    except:
        pass
    return None

# ---------------- Directory selection (numeric) ----------------
def choose_dir_numeric():
    cwd = str(Path.cwd())
    default_dir = cfg.get("default_dir", cwd)
    opts = [
        tr("dir_option1", cwd),  # current working directory
        tr("dir_option2", default_dir),
        tr("dir_option3", tr("dir_option3_title"))  # custom
    ]
    sel = numeric_choice(tr("prompt.choose_dir_numeric"), opts)
    if sel == 1:
        return cwd
    if sel == 2:
        return default_dir
    if sel == 3:
        p = input(tr("prompt.enter_dir") + " ").strip()
        if not p:
            return default_dir
        return str(Path(p).expanduser().resolve())
    return None

# ---------------- Cloudflared installer helper ----------------
def install_cloudflared_auto():
    # downloads latest linux-amd64 release and tries to install to /usr/local/bin (sudo) else local bin
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    tmp = Path("/tmp/cloudflared-autotunnel")
    try:
        import urllib.request
        cprint(tr("installing_cf"), "yellow")
        urllib.request.urlretrieve(url, str(tmp))
        tmp.chmod(0o755)
        target = Path("/usr/local/bin/cloudflared")
        # try move with sudo
        try:
            subprocess.run(["sudo", "mv", str(tmp), str(target)], check=True)
            subprocess.run(["sudo", "chmod", "+x", str(target)], check=False)
            cprint(tr("installed_system", str(target)), "green")
            cfg.setdefault("installed_tunnels", {})["cloudflared"] = str(target)
            save_config()
            return True
        except Exception:
            # fallback to local bin
            dst = LOCAL_BIN / "cloudflared"
            tmp.replace(dst)
            dst.chmod(0o755)
            cprint(tr("installed_local", str(dst)), "green")
            cfg.setdefault("installed_tunnels", {})["cloudflared"] = str(dst)
            save_config()
            return True
    except Exception as e:
        print("Erro install cloudflared:", e)
        return False

# ---------------- Save config helper ----------------
def save_config():
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# ---------------- Orquestração túnel ----------------
def start_tunnel_flow(only_tunnel=False):
    load_plugins()
    if not PLUGINS:
        cprint(tr("no_plugins"), "red"); return
    opts = [f"{name}" for _, (name,_) in PLUGINS.items()]
    sel = numeric_choice(tr("prompt.choose_plugin_numeric"), opts)
    if sel is None:
        cprint(tr("invalid_choice"), "red"); return
    name, plugin = PLUGINS[sel]
    if not plugin.installed():
        cprint(tr("plugin_not_installed", name), "yellow")
        # attempt automatic install
        ok = install_cloudflared_auto() if name == "cloudflared" else plugin.install()
        cprint(tr("install_result", ok), "green" if ok else "red")
        if not ok:
            return
    port = cfg.get("default_port", 1337)
    if not only_tunnel:
        p = input(tr("prompt.port", port) + " ").strip()
        if p: port = int(p)
        d = choose_dir_numeric()
        if not d:
            cprint(tr("aborted"), "red"); return
        started = http_server.start(port, d)
        cprint(tr("server_started", port) if started else tr("server_already"), "green")
    else:
        p = input(tr("prompt.port", port) + " ").strip()
        if p: port = int(p)
    cprint(tr("starting_tunnel", name), "cyan")
    plugin.start(port)
    # wait for url
    for i in range(40):
        url = getattr(plugin, "url", None)
        if url:
            cprint(tr("tunnel_url", url), "green")
            (DATA_DIR / "last_tunnel.url").write_text(url)
            return
        time.sleep(0.5)
    cprint(tr("tunnel_no_url"), "yellow")

def stop_tunnel_flow():
    load_plugins()
    if not PLUGINS:
        cprint(tr("no_plugins"), "red"); return
    opts = [f"{name}" for _, (name,_) in PLUGINS.items()]
    sel = numeric_choice(tr("prompt.choose_plugin_numeric"), opts)
    if sel is None:
        cprint(tr("invalid_choice"), "red"); return
    name, plugin = PLUGINS[sel]
    ok = plugin.stop()
    cprint(tr("stop_result", ok), "green" if ok else "red")

# ---------------- Main loop ----------------
def main():
    load_plugins()
    while True:
        print_header()
        menu_opts = [
            tr("menu.start_server"),
            tr("menu.start_tunnel"),
            tr("menu.start_tunnel_only"),
            tr("menu.stop_server"),
            tr("menu.stop_tunnel"),
            tr("menu.status"),
            tr("menu.change_lang"),
            tr("menu.exit")
        ]
        sel = numeric_choice(tr("prompt.choose_menu_numeric"), menu_opts)
        if sel == 1:
            port = cfg.get("default_port", 1337)
            p = input(tr("prompt.port", port) + " ").strip()
            if p: port = int(p)
            d = choose_dir_numeric()
            if not d:
                cprint(tr("aborted"), "red"); continue
            ok = http_server.start(port, d)
            cprint(tr("server_started", port) if ok else tr("server_already"), "green")
        elif sel == 2:
            start_tunnel_flow(only_tunnel=False)
        elif sel == 3:
            start_tunnel_flow(only_tunnel=True)
        elif sel == 4:
            if http_server.stop():
                cprint(tr("server_stopped"), "green")
            else:
                cprint(tr("server_not_running"), "yellow")
        elif sel == 5:
            stop_tunnel_flow()
        elif sel == 6:
            load_plugins()
            cprint(f"HTTP: port={http_server.port} dir={http_server.directory if http_server.httpd else 'stopped'}", "cyan")
            for _, (name, pl) in PLUGINS.items():
                cprint(f"Plugin {name}: installed={pl.installed()} pid={getattr(pl,'pid',None)} url={getattr(pl,'url',None)}", "cyan")
            input(tr("press_enter"))
        elif sel == 7:
            lang_opts = ["Português (pt)", "English (en)"]
            lsel = numeric_choice(tr("prompt.choose_lang_numeric"), lang_opts)
            if lsel == 1:
                cfg["language"]="pt"
            elif lsel == 2:
                cfg["language"]="en"
            save_config()
            global I18N
            I18N = load_lang(cfg["language"])
            cprint(tr("lang_saved"), "green")
        elif sel == 8:
            cprint("Saindo...", "cyan")
            try: http_server.stop()
            except: pass
            load_plugins()
            for _, (_, pl) in PLUGINS.items():
                try: pl.stop()
                except: pass
            break
        else:
            cprint(tr("invalid_choice"), "red")


if __name__ == "__main__":
    main()
