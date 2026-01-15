#!/usr/bin/env python3
"""
AutoTunnel - Minimal, numeric menus, colored (rich), auto-install cloudflared/ngrok.
Completely portable - no fixed hostnames or absolute paths.
"""
import os, sys, json, shutil, subprocess, threading, time, re, importlib.util
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import datetime

# ---------------- ASCII Arts Separadas ----------------
ASCII_ART_1 = """._____. ._____.
| ._. | | ._. |
| !_| |_|_|_! |
!___| |_______!
.___|_|_| |___.
| ._____| |_. |
| !_! | | !_! |
!_____! !_____!"""

ASCII_ART_2 = """  /$$$$$$              /$$            /$$$$$$$$                                      /$$
 /$$__  $$            | $$           |__  $$__/                                     | $$
| $$  \ $$ /$$   /$$ /$$$$$$    /$$$$$$ | $$ /$$   /$$ /$$$$$$$  /$$$$$$$   /$$$$$$ | $$
| $$$$$$$$| $$  | $$|_  $$_/   /$$__  $$| $$| $$  | $$| $$__  $$| $$__  $$ /$$__  $$| $$
| $$__  $$| $$  | $$  | $$    | $$  \ $$| $$| $$  | $$| $$  \ $$| $$  \ $$| $$$$$$$$| $$
| $$  | $$| $$  | $$  | $$ /$$| $$  | $$| $$| $$  | $$| $$  | $$| $$  | $$| $$_____/| $$
| $$  | $$|  $$$$$$/  |  $$$$/|  $$$$$$/| $$|  $$$$$$/| $$  | $$| $$  | $$|  $$$$$$$| $$
|__/  |__/ \______/    \___/   \______/ |__/ \______/ |__/  |__/|__/  |__/ \_______/|__/"""

# ---------------- Portable Paths / config ----------------
def get_user_data_dir():
    """Get portable user data directory"""
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    if xdg_data_home:
        return Path(xdg_data_home) / "autotunnel"
    return Path.home() / ".local" / "share" / "autotunnel"

def get_user_config_dir():
    """Get portable user config directory"""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        return Path(xdg_config_home) / "autotunnel"
    return Path.home() / ".config" / "autotunnel"

def to_portable_path(path_str):
    """
    Convert absolute path to portable format.
    If path is in home directory, convert to ~/ format.
    Otherwise, return as relative path if possible.
    """
    if not path_str:
        return ""
    
    try:
        path = Path(path_str).expanduser().resolve()
        home = Path.home()
        
        # Try to make path relative to home
        try:
            if path.is_relative_to(home):
                return "~/" + str(path.relative_to(home))
        except ValueError:
            pass
        
        # Try to make path relative to current directory
        try:
            cwd = Path.cwd()
            if path.is_relative_to(cwd):
                rel_path = path.relative_to(cwd)
                return "./" + str(rel_path) if str(rel_path) != "." else "."
        except ValueError:
            pass
        
        # Return absolute path as last resort
        return str(path)
    except Exception:
        return path_str

def from_portable_path(portable_path_str):
    """
    Convert portable path to absolute path.
    Handles ~/, ./, and absolute paths.
    """
    if not portable_path_str:
        return Path.cwd()
    
    try:
        path_str = str(portable_path_str)
        
        # Expand ~ to home directory
        if path_str.startswith("~"):
            return Path(path_str).expanduser().resolve()
        
        # Handle relative paths starting with .
        if path_str.startswith(".") or not Path(path_str).is_absolute():
            # Check if it's relative to current directory
            abs_path = (Path.cwd() / path_str).resolve()
            if abs_path.exists():
                return abs_path
            # If not, try to expand user (in case it's something like "Documents")
            return Path(path_str).expanduser().resolve()
        
        # Already absolute
        return Path(path_str).expanduser().resolve()
    except Exception:
        # Fallback to current directory
        return Path.cwd()

# Define all paths using portable functions
CONFIG_DIR = get_user_config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
DATA_DIR = get_user_data_dir()
LOG_DIR = DATA_DIR / "logs"
PID_DIR = DATA_DIR / "pids"
SCRIPT_DIR = Path(__file__).parent
PLUGIN_DIR = SCRIPT_DIR / "tunnels"
LANG_DIR = SCRIPT_DIR / "lang"
LOCAL_BIN = DATA_DIR / "bin"

for d in (CONFIG_DIR, DATA_DIR, LOG_DIR, PID_DIR, LOCAL_BIN):
    d.mkdir(parents=True, exist_ok=True)

# Default config - uses portable paths
DEFAULT_CONFIG = {
    "language": "pt",
    "default_port": 1337,
    "default_dir": "",  # Empty by default - will be set with portable path
    "installed_tunnels": {},
    "ngrok_auth_token": ""
}

# ---------------- Helpful: ensure rich ----------------
def ensure_rich():
    try:
        import rich
        return rich
    except Exception:
        print("Installing 'rich' dependency for colored menu...")
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
    from rich.text import Text
    from rich.box import ROUNDED
    console = Console()
else:
    console = None

# ---------------- Config / i18n ----------------
def load_config():
    """Load configuration, ensuring portability and fixing invalid paths"""
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            
            # Convert any absolute paths in default_dir to portable format
            if "default_dir" in cfg and cfg["default_dir"]:
                cfg["default_dir"] = to_portable_path(cfg["default_dir"])
            
            # Ensure default_dir exists - if not, reset to current directory
            if cfg.get("default_dir"):
                abs_path = from_portable_path(cfg["default_dir"])
                if not abs_path.exists():
                    # Path doesn't exist, reset to current directory
                    cfg["default_dir"] = to_portable_path(str(Path.cwd()))
            
            # If default_dir is empty after validation, set to current directory
            if not cfg.get("default_dir"):
                cfg["default_dir"] = to_portable_path(str(Path.cwd()))
                
            return cfg
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Corrupted config, create new
            pass
    
    # Create config with current directory as portable path
    current_portable = to_portable_path(str(Path.cwd()))
    DEFAULT_CONFIG["default_dir"] = current_portable
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG.copy()

cfg = load_config()
LANG = cfg.get("language", "pt")

def load_lang(lang):
    f = LANG_DIR / f"{lang}.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except:
        return {}

I18N = load_lang(LANG)
def tr(key, *args):
    s = I18N.get(key, key)
    for i,a in enumerate(args, start=1):
        s = s.replace("{" + str(i) + "}", str(a))
    return s

# ---------------- Custom HTTP Handler ----------------
class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        log_entry = "%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args
        )
        log_path = LOG_DIR / "http_server.log"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

# ---------------- HttpServer ----------------
class HttpServer:
    def __init__(self):
        self.httpd = None
        self.thread = None
        self.port = None
        self.directory = None
        self.log_path = LOG_DIR / "http_server.log"

    def start(self, port:int, directory:str):
        if self.httpd:
            return False
        
        # Convert portable path to absolute
        try:
            dir_path = from_portable_path(directory)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Create default index.html
                    index_file = dir_path / "index.html"
                    if not index_file.exists():
                        index_file.write_text(f'''<!DOCTYPE html>
<html>
<head><title>AutoTunnel Server</title></head>
<body>
    <h1>AutoTunnel HTTP Server</h1>
    <p>{tr("server_started", port)}</p>
    <p>{tr("current_dir", dir_path)}</p>
    <p>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>''')
                except Exception as e:
                    cprint(tr("error_creating_dir", dir_path, e), "red")
                    return False
        except Exception as e:
            cprint(tr("error_path", e), "red")
            return False
        
        if self.log_path.exists():
            self.log_path.unlink()
        
        handler = lambda *args, **kwargs: QuietHTTPRequestHandler(*args, directory=str(dir_path), **kwargs)
        self.httpd = ThreadingHTTPServer(("", int(port)), handler)
        self.port = port
        self.directory = str(dir_path)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        
        (PID_DIR / "http_server.json").write_text(json.dumps({
            "pid": os.getpid(),
            "port": port,
            "dir": to_portable_path(str(dir_path)),
            "start_time": datetime.datetime.now().isoformat()
        }))
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] HTTP Server started on port {port}, directory: {dir_path}\n")
        
        return True

    def stop(self):
        if not self.httpd:
            return False
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] HTTP Server stopped\n")
        
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd = None
        try:
            (PID_DIR / "http_server.json").unlink()
        except:
            pass
        return True
    
    def get_logs(self, lines=20):
        if not self.log_path.exists():
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        return all_lines[-lines:]

http_server = HttpServer()

# ---------------- Plugin loader ----------------
PLUGINS = {}
def load_plugins():
    PLUGINS.clear()
    if not PLUGIN_DIR.exists():
        return
    
    # Load Cloudflared
    try:
        spec = importlib.util.spec_from_file_location(
            "autotunnel.plugins.cloudflared",
            PLUGIN_DIR / "Cloudflared.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        inst = mod.TunnelPlugin()
        PLUGINS[1] = (inst.name(), inst)
    except Exception as e:
        cprint(f"Error loading Cloudflared plugin: {e}", "yellow")
    
    # Load Ngrok if exists
    ngrok_path = PLUGIN_DIR / "Ngrok.py"
    if ngrok_path.exists():
        try:
            spec = importlib.util.spec_from_file_location(
                "autotunnel.plugins.ngrok",
                ngrok_path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            inst = mod.TunnelPlugin()
            PLUGINS[2] = (inst.name(), inst)
        except Exception as e:
            cprint(f"Error loading Ngrok plugin: {e}", "yellow")
    
    # Load other plugins
    idx = 3
    for p in sorted(PLUGIN_DIR.glob("*.py")):
        if p.name in ["Cloudflared.py", "Ngrok.py"]:
            continue
        
        name = p.stem
        spec = importlib.util.spec_from_file_location(f"autotunnel.plugins.{name}", p)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            continue
        
        if hasattr(mod, "TunnelPlugin"):
            try:
                inst = mod.TunnelPlugin()
                PLUGINS[idx] = (inst.name(), inst)
                idx += 1
            except Exception:
                continue

# ---------------- Utils UI ----------------
def cprint(text, style=None, end="\n"):
    if console:
        console.print(text, style=style, end=end)
    else:
        print(text, end=end)

def clear_screen():
    if console:
        console.clear()
    else:
        os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    clear_screen()
    if console:
        # Center ASCII arts manually by splitting lines and centering each
        ascii1_lines = ASCII_ART_1.split('\n')
        ascii2_lines = ASCII_ART_2.split('\n')
        
        # Find maximum width of both ASCII arts
        max_width = max(
            max(len(line) for line in ascii1_lines) if ascii1_lines else 0,
            max(len(line) for line in ascii2_lines) if ascii2_lines else 0
        )
        
        # Create centered text
        centered_text = ""
        
        # Center ASCII art 1
        for line in ascii1_lines:
            padding = (max_width - len(line)) // 2
            centered_text += " " * padding + line + "\n"
        
        centered_text += "\n"
        
        # Center ASCII art 2
        for line in ascii2_lines:
            padding = (max_width - len(line)) // 2
            centered_text += " " * padding + line + "\n"
        
        # Create the panel content
        panel_content = f"[bold cyan]{centered_text}[/bold cyan]\n[bold cyan]AutoTunnel[/bold cyan]\n[green]Fast server + tunnel (cloudflared/ngrok)[/green]\n[dim]Portable • Settings saved in universal format[/dim]"
        
        console.print(Panel(panel_content, 
                          border_style="cyan",
                          box=ROUNDED,
                          padding=(1, 2)))
    else:
        # Fallback without rich
        print(ASCII_ART_1)
        print("\n" + ASCII_ART_2)
        print("\n" + "="*60)
        print("AutoTunnel")
        print("Fast server + tunnel (cloudflared/ngrok)")
        print("Portable • Settings saved in universal format")
        print("="*60 + "\n")

def numeric_choice(prompt_text, options):
    if console:
        table = Table.grid(padding=(0,1))
        for i,opt in enumerate(options, start=1):
            # Remove any rich formatting for counting
            clean_opt = re.sub(r'\[.*?\]', '', opt)
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

# ---------------- Directory selection (PORTABLE) ----------------
def choose_dir():
    """Portable directory selection with validation"""
    current_dir = Path.cwd()
    current_portable = to_portable_path(str(current_dir))
    
    # Get default directory (already in portable format)
    default_dir_portable = cfg.get("default_dir", current_portable)
    default_dir_absolute = from_portable_path(default_dir_portable)
    
    # Check if default exists
    default_exists = default_dir_absolute.exists() and default_dir_absolute.is_dir()
    
    # If default doesn't exist, reset to current directory
    if not default_exists:
        default_dir_portable = current_portable
        default_dir_absolute = current_dir
        cfg["default_dir"] = current_portable
        save_config()
    
    while True:
        print_header()
        cprint(f"📁 {tr('current_dir', current_portable)}", "white")
        
        if default_dir_portable != current_portable:
            cprint(f"⭐ {tr('default_dir', default_dir_portable)}", "white")
        
        opts = []
        opts.append(f"📂 {tr('dir_option_current')}")
        
        if default_dir_portable != current_portable:
            opts.append(f"📂 {tr('dir_option_default')}")
        
        opts.append(f"🔍 {tr('dir_option_custom')}")
        opts.append(f"🆕 {tr('dir_option_create')}")
        opts.append(f"⬅️ {tr('back')}")
        
        sel = numeric_choice(tr("prompt.choose_dir"), opts)
        
        if sel == 1:
            return str(current_dir)
        
        elif sel == 2 and default_dir_portable != current_portable:
            return str(default_dir_absolute)
        
        elif (sel == 2 and default_dir_portable == current_portable) or (sel == 3 and default_dir_portable != current_portable):
            # Choose custom directory
            cprint("💡 Tip: Use ~/ for home directory or ./ for current directory", "dim")
            path = input(tr("prompt.enter_dir") + " ").strip()
            if not path:
                continue
            
            try:
                abs_path = from_portable_path(path)
                if abs_path.exists() and abs_path.is_dir():
                    # Update default directory to this new choice
                    new_portable = to_portable_path(str(abs_path))
                    if new_portable != current_portable:
                        cfg["default_dir"] = new_portable
                        save_config()
                        cprint(tr("dir_saved"), "green")
                    return str(abs_path)
                else:
                    cprint(tr("dir_not_exist", path), "yellow")
                    create = input(tr("prompt.create_dir") + " ").strip().lower()
                    if create in ['s', 'y', 'sim', 'yes']:
                        abs_path.mkdir(parents=True, exist_ok=True)
                        # Update default to new directory
                        new_portable = to_portable_path(str(abs_path))
                        cfg["default_dir"] = new_portable
                        save_config()
                        cprint(tr("dir_created", new_portable), "green")
                        return str(abs_path)
            except Exception as e:
                cprint(tr("error_path", e), "red")
                time.sleep(2)
        
        elif (sel == 3 and default_dir_portable == current_portable) or (sel == 4 and default_dir_portable != current_portable):
            # Create new directory
            path = input(tr("prompt.enter_new_dir") + " ").strip()
            if path:
                try:
                    abs_path = from_portable_path(path)
                    abs_path.mkdir(parents=True, exist_ok=True)
                    portable_path = to_portable_path(str(abs_path))
                    
                    cprint(tr("dir_created", portable_path), "green")
                    
                    # Ask to set as default
                    set_default = input("⭐ Set as default directory? (y/n): ").strip().lower()
                    if set_default in ['s', 'y', 'sim', 'yes']:
                        cfg["default_dir"] = portable_path
                        save_config()
                        cprint(tr("dir_saved"), "green")
                    
                    time.sleep(1)
                    return str(abs_path)
                except Exception as e:
                    cprint(tr("error_creating_dir", path, e), "red")
                    time.sleep(2)
        
        elif sel == (5 if default_dir_portable != current_portable else 4) or sel is None:
            return None

# ---------------- Save config ----------------
def save_config():
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# ---------------- Installers ----------------
def install_cloudflared_auto():
    """Install cloudflared - portable version"""
    import platform
    arch = platform.machine()
    
    if arch in ["x86_64", "amd64"]:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif arch in ["aarch64", "arm64"]:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    elif "arm" in arch:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
    else:
        cprint(f"❌ Unsupported architecture: {arch}", "red")
        cprint(tr("installing_cf"), "yellow")
        return False
    
    tmp = Path("/tmp/cloudflared-autotunnel")
    
    try:
        import urllib.request
        cprint(tr("installing_cf"), "yellow")
        urllib.request.urlretrieve(url, str(tmp))
        tmp.chmod(0o755)
        
        dst = LOCAL_BIN / "cloudflared"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(tmp), str(dst))
        dst.chmod(0o755)
        tmp.unlink(missing_ok=True)
        
        cprint(tr("installed_local", dst), "green")
        cfg.setdefault("installed_tunnels", {})["cloudflared"] = str(dst)
        save_config()
        return True
    except Exception as e:
        cprint(f"❌ Error installing cloudflared: {e}", "red")
        return False

def install_ngrok_auto():
    """Install ngrok - portable version"""
    import platform, tarfile, warnings
    arch = platform.machine()
    
    if arch in ["x86_64", "amd64"]:
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
    elif arch in ["aarch64", "arm64"]:
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz"
    elif "arm" in arch:
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz"
    else:
        cprint(f"❌ Unsupported architecture: {arch}", "red")
        cprint("📦 Install manually: https://ngrok.com/download", "yellow")
        return False
    
    tmp_tar = Path("/tmp/ngrok.tgz")
    
    try:
        import urllib.request
        cprint(tr("installing_ngrok"), "yellow")
        urllib.request.urlretrieve(url, str(tmp_tar))
        
        with tarfile.open(tmp_tar, 'r:gz') as tar:
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            tar.extract('ngrok', path="/tmp")
        
        tmp_ngrok = Path("/tmp/ngrok")
        if not tmp_ngrok.exists():
            cprint("❌ Error extracting ngrok", "red")
            return False
        
        dst = LOCAL_BIN / "ngrok"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(tmp_ngrok), str(dst))
        dst.chmod(0o755)
        
        tmp_tar.unlink(missing_ok=True)
        tmp_ngrok.unlink(missing_ok=True)
        
        # Configure token if needed
        if not cfg.get("ngrok_auth_token"):
            cprint(f"\n🔑 {tr('ngrok_token_required')}", "yellow")
            cprint(tr("ngrok_get_token"), "dim")
            token = input(tr("prompt.ngrok_token") + " ").strip()
            if token:
                cfg["ngrok_auth_token"] = token
                save_config()
                subprocess.run([str(dst), "config", "add-authtoken", token],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cprint(tr("ngrok_token_saved"), "green")
        
        cfg.setdefault("installed_tunnels", {})["ngrok"] = str(dst)
        save_config()
        cprint(tr("installed_ngrok", dst), "green")
        return True
        
    except Exception as e:
        cprint(f"❌ Error installing ngrok: {e}", "red")
        return False

# ---------------- Tunnel functions ----------------
def start_tunnel_flow(only_tunnel=False):
    load_plugins()
    if not PLUGINS:
        cprint(tr("no_plugins"), "red")
        input(tr("press_enter"))
        return
    
    opts = [f"{name}" for _, (name,_) in PLUGINS.items()]
    sel = numeric_choice(tr("prompt.choose_plugin_numeric"), opts)
    
    if sel is None:
        cprint(tr("invalid_choice"), "red")
        input(tr("press_enter"))
        return
    
    name, plugin = PLUGINS[sel]
    
    if not plugin.installed():
        cprint(tr("plugin_not_installed", name), "yellow")
        install_now = input(tr("prompt.install_now") + " ").strip().lower()
        
        if install_now in ['s', 'y', 'sim', 'yes']:
            if name == "cloudflared":
                ok = install_cloudflared_auto()
            elif name == "ngrok":
                ok = install_ngrok_auto()
            else:
                ok = plugin.install()
            
            if not ok:
                cprint(tr("install_failed"), "red")
                input(tr("press_enter"))
                return
            else:
                cprint(tr("install_result", "success"), "green")
        else:
            cprint(tr("install_skipped"), "yellow")
            input(tr("press_enter"))
            return
    
    port = cfg.get("default_port", 1337)
    if not only_tunnel:
        p = input(tr("prompt.port", port) + " ").strip()
        if p:
            try:
                port = int(p)
            except:
                cprint(tr("invalid_port"), "red")
                port = cfg.get("default_port", 1337)
        
        d = choose_dir()
        if not d:
            cprint(tr("aborted"), "red")
            input(tr("press_enter"))
            return
        
        started = http_server.start(port, d)
        if started:
            cprint(tr("server_started", port), "green")
        else:
            cprint(tr("server_already"), "yellow")
    else:
        p = input(tr("prompt.tunnel_port", port) + " ").strip()
        if p:
            try:
                port = int(p)
            except:
                cprint(tr("invalid_port"), "red")
                port = cfg.get("default_port", 1337)
    
    cprint(tr("starting_tunnel", name), "cyan")
    
    if name == "ngrok" and not cfg.get("ngrok_auth_token"):
        cprint(tr("ngrok_token_missing"), "yellow")
        cprint(tr("ngrok_get_token"), "dim")
        token = input(tr("prompt.ngrok_token") + " ").strip()
        if token:
            cfg["ngrok_auth_token"] = token
            save_config()
            ngrok_path = cfg.get("installed_tunnels", {}).get("ngrok", "ngrok")
            subprocess.run([ngrok_path, "config", "add-authtoken", token],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cprint(tr("ngrok_token_saved"), "green")
    
    plugin.start(port)
    
    cprint(tr("waiting_for_url"), "cyan")
    for i in range(40):
        url = getattr(plugin, "url", None)
        if url:
            cprint(f"✅ {tr('tunnel_url', url)}", "white")
            (DATA_DIR / "last_tunnel.url").write_text(url)
            
            try:
                import pyperclip
                pyperclip.copy(url)
                cprint(tr("url_copied"), "green")
            except:
                pass
            
            input(tr("press_enter"))
            return
        time.sleep(0.5)
    
    cprint(tr("tunnel_no_url"), "yellow")
    cprint(tr("check_logs"), "dim")
    input(tr("press_enter"))

def stop_tunnel_flow():
    load_plugins()
    if not PLUGINS:
        cprint(tr("no_plugins"), "red")
        input(tr("press_enter"))
        return
    
    running = []
    for idx, (name, plugin) in PLUGINS.items():
        if hasattr(plugin, 'proc') and plugin.proc:
            running.append((idx, name, plugin))
    
    if not running:
        cprint(tr("no_tunnels_running"), "yellow")
        input(tr("press_enter"))
        return
    
    if len(running) == 1:
        idx, name, plugin = running[0]
        ok = plugin.stop()
        cprint(tr("stop_result", name, "stopped" if ok else "error"), "green" if ok else "red")
        input(tr("press_enter"))
        return
    
    opts = [f"{name}" for _, name, _ in running]
    sel = numeric_choice(tr("prompt.choose_tunnel_stop"), opts)
    
    if sel is None:
        cprint(tr("invalid_choice"), "red")
        input(tr("press_enter"))
        return
    
    for i, (_, name, plugin) in enumerate(running, 1):
        if i == sel:
            ok = plugin.stop()
            cprint(tr("stop_result", name, "stopped" if ok else "error"), "green" if ok else "red")
            input(tr("press_enter"))
            return

# ---------------- Log viewer ----------------
def view_logs():
    while True:
        print_header()
        cprint(f"[bold]{tr('menu.view_logs')}[/bold]", "cyan")
        
        logs_available = []
        if http_server.log_path.exists():
            logs_available.append((f"🌐 {tr('menu.start_server')}", http_server.log_path))
        
        load_plugins()
        for idx, (name, plugin) in PLUGINS.items():
            if hasattr(plugin, 'log_path') and plugin.log_path and Path(plugin.log_path).exists():
                logs_available.append((f"🚇 {name}", plugin.log_path))
        
        if not logs_available:
            cprint(tr("no_logs_available"), "yellow")
            input(tr("press_enter"))
            return
        
        opts = [f"{name}" for name, _ in logs_available]
        opts.append(f"⬅️ {tr('back')}")
        
        sel = numeric_choice(tr("prompt.choose_log"), opts)
        
        if sel is None or sel > len(logs_available):
            return
        
        if sel <= len(logs_available):
            name, log_path = logs_available[sel - 1]
            show_log_file(name, log_path)

def show_log_file(name, log_path):
    while True:
        print_header()
        cprint(f"[bold]📄 {name}[/bold]", "cyan")
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                cprint(tr("log_empty"), "yellow")
            else:
                start = max(0, len(lines) - 30)
                for line in lines[start:]:
                    line = line.rstrip()
                    if "ERROR" in line or "error" in line.lower():
                        cprint(f"❌ {line}", "red")
                    elif "WARN" in line or "warning" in line.lower():
                        cprint(f"⚠️ {line}", "yellow")
                    elif "https://" in line:
                        parts = line.split("https://")
                        if len(parts) > 1:
                            cprint(parts[0], "white", end="")
                            cprint("https://" + parts[1], "green")
                        else:
                            cprint(line, "white")
                    else:
                        cprint(f"📝 {line}", "white")
            
            print("\n" + "="*60)
            opts = [
                f"🔄 {tr('log_refresh')}",
                f"🧹 {tr('log_clear')}",
                f"👀 {tr('log_tail')}",
                f"⬅️ {tr('back')}"
            ]
            
            sel = numeric_choice(tr("prompt.log_action"), opts)
            
            if sel == 1:
                continue
            elif sel == 2:
                confirm = input(tr("prompt.confirm_clear_log") + " ").strip().lower()
                if confirm in ['s', 'y', 'sim', 'yes']:
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write(f"[{datetime.datetime.now().isoformat()}] {tr('log_cleared')}\n")
                    cprint(tr("log_cleared"), "green")
                    time.sleep(1)
            elif sel == 3:
                tail_log(name, log_path)
            else:
                break
                
        except Exception as e:
            cprint(f"❌ Error: {e}", "red")
            input(tr("press_enter"))
            break

def tail_log(name, log_path):
    print_header()
    cprint(f"[bold]👀 {name}[/bold]", "cyan")
    cprint("[dim]Ctrl+C to go back[/dim]", "white")
    print("-" * 60)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    line = line.rstrip()
                    if "ERROR" in line or "error" in line.lower():
                        cprint(f"❌ {line}", "red")
                    elif "WARN" in line or "warning" in line.lower():
                        cprint(f"⚠️ {line}", "yellow")
                    elif "https://" in line:
                        parts = line.split("https://")
                        if len(parts) > 1:
                            cprint(parts[0], "white", end="")
                            cprint("https://" + parts[1], "green")
                        else:
                            cprint(line, "white")
                    else:
                        cprint(f"📝 {line}", "white")
                else:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        cprint(f"❌ Error: {e}", "red")

# ---------------- Status ----------------
def show_status():
    print_header()
    
    if http_server.httpd:
        cprint(f"✅ {tr('menu.start_server')}: port {http_server.port}", "bold")
        cprint(f"   {tr('current_dir', to_portable_path(http_server.directory))}", "dim")
        
        logs = http_server.get_logs(3)
        if logs:
            cprint("\n   Last requests:", "cyan")
            for log in logs[-3:]:
                cprint(f"   {log.strip()}", "white")
    else:
        cprint(f"❌ {tr('menu.start_server')}: {tr('server_not_running')}", "bold")
    
    print()
    
    load_plugins()
    running = 0
    
    for idx, (name, plugin) in PLUGINS.items():
        installed = plugin.installed()
        is_running = hasattr(plugin, 'proc') and plugin.proc and plugin.proc.poll() is None
        
        if is_running:
            running += 1
            status = "✅"
        elif installed:
            status = "⚠️ "
        else:
            status = "❌"
        
        cprint(f"{status} {name}: {'running' if is_running else 'installed' if installed else 'not installed'}", "bold")
        
        if is_running:
            url = getattr(plugin, 'url', None)
            pid = getattr(plugin, 'pid', None)
            if url:
                cprint(f"   URL: {url}", "green")
            if pid:
                cprint(f"   PID: {pid}", "dim")
    
    print("\n" + "="*60)
    cprint(f"📊 Summary: {running} active tunnel(s)", "green" if running > 0 else "yellow")
    input(tr("press_enter"))

# ---------------- Settings ----------------
def show_settings():
    global I18N, LANG
    
    while True:
        print_header()
        cprint(f"[bold]{tr('menu.settings')}[/bold]", "cyan")
        
        cprint(f"\n🌐 Language: {LANG}", "white")
        cprint(f"🔢 {tr('settings_change_port')}: {cfg.get('default_port', 1337)}", "white")
        cprint(f"📁 {tr('settings_change_dir')}: {cfg.get('default_dir', '~')}", "white")
        
        if cfg.get('ngrok_auth_token'):
            cprint(f"🔑 {tr('settings_ngrok_token')}: {'*' * 20}", "white")
        else:
            cprint(f"🔑 {tr('settings_ngrok_token')}: {tr('ngrok_token_missing')}", "yellow")
        
        print()
        opts = [
            f"🌐 {tr('settings_change_lang')}",
            f"🔢 {tr('settings_change_port')}",
            f"📁 {tr('settings_change_dir')}",
            f"🔑 {tr('settings_ngrok_token')}",
            f"⬅️ {tr('back')}"
        ]
        
        sel = numeric_choice(tr("prompt.choose_setting"), opts)
        
        if sel == 1:
            lang_opts = ["Português (pt)", "English (en)"]
            lsel = numeric_choice(tr("prompt.choose_lang_numeric"), lang_opts)
            if lsel == 1:
                cfg["language"] = "pt"
            elif lsel == 2:
                cfg["language"] = "en"
            save_config()
            # Reload translations
            LANG = cfg["language"]
            I18N = load_lang(LANG)
            cprint(tr("lang_saved"), "green")
            time.sleep(2)
            # Return to main menu to show updated language
            return True  # Signal to refresh
        elif sel == 2:
            new_port = input(tr("prompt.new_default_port") + " ").strip()
            if new_port:
                try:
                    port = int(new_port)
                    if 1 <= port <= 65535:
                        cfg["default_port"] = port
                        save_config()
                        cprint(tr("port_saved"), "green")
                        time.sleep(1)
                    else:
                        cprint(tr("invalid_port"), "red")
                        time.sleep(2)
                except:
                    cprint(tr("invalid_port"), "red")
                    time.sleep(2)
        elif sel == 3:
            new_dir = choose_dir()
            if new_dir:
                cfg["default_dir"] = to_portable_path(new_dir)
                save_config()
                cprint(tr("dir_saved"), "green")
                time.sleep(1)
        elif sel == 4:
            token = input(tr("prompt.ngrok_token") + " ").strip()
            if token:
                cfg["ngrok_auth_token"] = token
                save_config()
                cprint(tr("ngrok_token_saved"), "green")
                time.sleep(1)
        else:
            break
    
    return False

# ---------------- Main loop ----------------
def main():
    load_plugins()
    
    while True:
        print_header()
        
        menu_opts = [
            f"🌐 {tr('menu.start_server')}",
            f"🚇 {tr('menu.start_tunnel')}",
            f"🔌 {tr('menu.start_tunnel_only')}",
            f"🛑 {tr('menu.stop_server')}",
            f"✋ {tr('menu.stop_tunnel')}",
            f"📊 {tr('menu.status')}",
            f"📄 {tr('menu.view_logs')}",
            f"⚙️ {tr('menu.settings')}",
            f"🚪 {tr('menu.exit')}"
        ]
        
        sel = numeric_choice(tr("prompt.choose_menu_numeric"), menu_opts)
        
        if sel == 1:
            port = cfg.get("default_port", 1337)
            p = input(tr("prompt.port", port) + " ").strip()
            if p:
                try:
                    port = int(p)
                except:
                    cprint(tr("invalid_port"), "red")
                    continue
            
            d = choose_dir()
            if not d:
                cprint(tr("aborted"), "red")
                time.sleep(1)
                continue
            
            ok = http_server.start(port, d)
            if ok:
                cprint(tr("server_started", port), "green")
            else:
                cprint(tr("server_already"), "yellow")
            input(tr("press_enter"))
            
        elif sel == 2:
            start_tunnel_flow(only_tunnel=False)
            
        elif sel == 3:
            start_tunnel_flow(only_tunnel=True)
            
        elif sel == 4:
            if http_server.stop():
                cprint(tr("server_stopped"), "green")
            else:
                cprint(tr("server_not_running"), "yellow")
            input(tr("press_enter"))
            
        elif sel == 5:
            stop_tunnel_flow()
            
        elif sel == 6:
            show_status()
            
        elif sel == 7:
            view_logs()
            
        elif sel == 8:
            refresh = show_settings()
            if refresh:
                continue  # Refresh the interface with new language
            
        elif sel == 9:
            cprint("👋 Exiting...", "cyan")
            try:
                http_server.stop()
            except:
                pass
            
            load_plugins()
            for _, (_, plugin) in PLUGINS.items():
                try:
                    if hasattr(plugin, 'proc') and plugin.proc:
                        plugin.stop()
                except:
                    pass
            
            break
        else:
            cprint(tr("invalid_choice"), "red")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cprint(f"\n👋 {tr('aborted')}", "yellow")
    except Exception as e:
        cprint(f"\n💀 Error: {e}", "red")
