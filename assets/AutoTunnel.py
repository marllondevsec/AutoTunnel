#!/usr/bin/env python3
"""
AutoTunnel - Minimal, numeric menus, colored (rich), auto-install cloudflared/ngrok.
Completely portable - no fixed hostnames or absolute paths.
"""
import os, sys, json, shutil, subprocess, threading, time, re, importlib.util, socket, signal
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import datetime

# ---------------- ASCII Arts Separadas ----------------
ASCII_ART_1 = """
._____. ._____.
| ._. | | ._. |
| !_| |_|_|_! |
!___| |_______!
.___|_|_| |___.
| ._____| |_. |
| !_! | | !_! |
!_____! !_____!"""

ASCII_ART_2 = r""" 
  /$$$$$$              /$$            /$$$$$$$$                                      /$$
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

def get_local_ip():
    """
    Get the local IP address of the machine.
    Returns the network interface IP (not localhost).
    """
    try:
        # Create a socket to connect to an external server (doesn't send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        # Try to connect to any IP (doesn't need to be reachable)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback: get hostname and resolve to IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip.startswith('127.'):
                return None
            return ip
        except:
            return None

def show_server_urls(port):
    """
    Show URLs to access the HTTP server.
    """
    local_ip = get_local_ip()
    
    if console:
        from rich.table import Table
        from rich.panel import Panel
        
        # Create table
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("URL", style="green")
        
        if local_ip:
            local_url = f"http://{local_ip}:{port}"
            table.add_row(f"🌐 {tr('local_network')}", local_url)
        
        loopback_url = f"http://127.0.0.1:{port}"
        table.add_row("🔄 Loopback", loopback_url)
        
        console.print(table)
        
        if local_ip:
            console.print(f"\n[yellow]💡 {tr('share_local_url')}[/yellow]")
        
        # Copy to clipboard
        if local_ip:
            try:
                import pyperclip
                pyperclip.copy(local_url)
                console.print(f"[green]📋 {tr('copied_to_clipboard')}[/green]")
            except:
                pass
    
    else:
        # Fallback without Rich
        print("\n" + "="*60)
        print(tr("server_urls"))
        if local_ip:
            local_url = f"http://{local_ip}:{port}"
            print(f"🌐 {tr('local_network')}: {local_url}")
        print(f"🔄 Loopback: http://127.0.0.1:{port}")
        print("="*60)
        if local_ip:
            print(f"💡 {tr('share_local_url')}")
    
    # Save URL for future reference
    if local_ip:
        url_to_save = f"http://{local_ip}:{port}"
    else:
        url_to_save = f"http://127.0.0.1:{port}"
    
    (DATA_DIR / "last_server.url").write_text(url_to_save)
    return url_to_save

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

# Fallback English translations for new keys
FALLBACK_EN = {
    "server_local_url": "Local server URL: {1}",
    "server_loopback_url": "Loopback URL: {1}",
    "local_network": "Local Network",
    "copied_to_clipboard": "Copied to clipboard!",
    "share_local_url": "Share this URL with other devices on the same network",
    "ip_not_detected": "Could not detect local network IP. Only accessible from this machine.",
    "saved_urls": "Saved URLs",
    "last_server_url": "Last Server",
    "last_tunnel_url": "Last Tunnel",
    "copy_url": "Copy",
    "url_copied_success": "URL copied to clipboard!",
    "no_saved_urls": "No saved URLs found",
    "server_urls": "Server URLs:",
    "view_saved_urls": "View Saved URLs",
    "summary": "Summary: {1} active tunnel(s)",
    "menu.show_saved_urls": "Show saved URLs",
    # New strings for active process management
    "active_urls": "Active URLs (Tunnels and Servers)",
    "no_active_processes": "No active tunnels or servers found.",
    "process_type_tunnel": "Tunnel",
    "process_type_server": "Server",
    "stop_process": "Stop",
    "process_stopped": "Process {1} stopped.",
    "process_stop_failed": "Failed to stop process {1}.",
    "choose_process_to_stop": "Choose a process to stop (number): ",
    "press_enter_to_continue": "Press Enter to continue...",
    "active_processes": "Active Processes",
    "pid": "PID",
    "port": "Port",
    "start_time": "Start Time",
    "type": "Type",
    "name": "Name",
    "url": "URL",
    "no_url_available": "No URL available",
    "no_urls_to_copy": "No URLs to copy.",
    "choose_action": "Choose action (number): ",
    "choose_url_to_copy": "Choose URL to copy (number): ",
    "view_active_urls": "View Active URLs"
}

# ---------------- Process Management ----------------
def save_process_info(name, pid, port, url=None, process_type="tunnel"):
    """Save process information to JSON file"""
    info = {
        "name": name,
        "pid": pid,
        "port": port,
        "type": process_type,
        "url": url,
        "start_time": datetime.datetime.now().isoformat()
    }
    
    pid_file = PID_DIR / f"{name}_{pid}.json"
    pid_file.write_text(json.dumps(info, indent=2), encoding="utf-8")
    
    # Also update active processes list
    active_file = DATA_DIR / "active_processes.json"
    active = {}
    if active_file.exists():
        active = json.loads(active_file.read_text(encoding="utf-8"))
    
    active[str(pid)] = info
    active_file.write_text(json.dumps(active, indent=2), encoding="utf-8")
    
    return pid_file

def remove_process_info(pid):
    """Remove process information"""
    # Remove individual PID file
    for pid_file in PID_DIR.glob(f"*_{pid}.json"):
        pid_file.unlink(missing_ok=True)
    
    # Remove from active processes
    active_file = DATA_DIR / "active_processes.json"
    if active_file.exists():
        active = json.loads(active_file.read_text(encoding="utf-8"))
        if str(pid) in active:
            del active[str(pid)]
            active_file.write_text(json.dumps(active, indent=2), encoding="utf-8")

def get_active_processes():
    """Get all active processes with validation"""
    active = []
    
    # Check from active processes file
    active_file = DATA_DIR / "active_processes.json"
    if active_file.exists():
        processes = json.loads(active_file.read_text(encoding="utf-8"))
        
        for pid_str, info in list(processes.items()):
            try:
                pid = int(pid_str)
                # Check if process is actually running
                os.kill(pid, 0)  # Will raise OSError if process doesn't exist
                active.append(info)
            except (OSError, ValueError):
                # Process is dead, remove it
                remove_process_info(pid)
    
    return active

def is_process_alive(pid):
    """Check if a process is still alive"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def cleanup_dead_processes():
    """Remove entries for processes that are no longer alive"""
    active_file = DATA_DIR / "active_processes.json"
    if not active_file.exists():
        return
    
    processes = json.loads(active_file.read_text(encoding="utf-8"))
    for pid_str in list(processes.keys()):
        try:
            pid = int(pid_str)
            if not is_process_alive(pid):
                remove_process_info(pid)
        except ValueError:
            remove_process_info(pid_str)

def stop_process_by_pid(pid):
    """Stop a process by PID"""
    if not is_process_alive(pid):
        remove_process_info(pid)
        return False
    
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait a bit for process to terminate
        for _ in range(10):
            if not is_process_alive(pid):
                break
            time.sleep(0.5)
        
        # Force kill if still alive
        if is_process_alive(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
        
        remove_process_info(pid)
        return True
    except Exception as e:
        cprint(f"Error stopping process {pid}: {e}", "red")
        return False

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
    s = I18N.get(key)
    if s is None:
        # If not found, try English fallback
        s = FALLBACK_EN.get(key, key)
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
        # Log to a generic location - individual server logs are handled by HttpServer class
        log_path = LOG_DIR / "http_server.log"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

# ============================================================================
# SUBSTITUA A CLASSE HttpServer (linha ~380) POR ESTA VERSÃO:
# ============================================================================

class HttpServer:
    """Classe para gerenciar um único servidor HTTP"""
    def __init__(self):
        self.httpd = None
        self.thread = None
        self.port = None
        self.directory = None
        self.pid = None  # PID único para este servidor
        self.log_path = None

    def start(self, port: int, directory: str):
        """Inicia o servidor HTTP (sem verificação de instância única)"""
        if self.httpd:
            return False  # Este servidor já está rodando
        
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
    <p>Server started on port {port}</p>
    <p>Directory: {dir_path}</p>
    <p>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>''')
                except Exception as e:
                    cprint(f"Error creating directory {dir_path}: {e}", "red")
                    return False
        except Exception as e:
            cprint(f"Path error: {e}", "red")
            return False
        
        # Cada servidor tem seu próprio log
        self.log_path = LOG_DIR / f"http_server_{port}.log"
        
        if self.log_path.exists():
            self.log_path.unlink()
        
        handler = lambda *args, **kwargs: QuietHTTPRequestHandler(*args, directory=str(dir_path), **kwargs)
        
        try:
            self.httpd = ThreadingHTTPServer(("", int(port)), handler)
            self.port = port
            self.directory = str(dir_path)
            
            # Gera um PID único para o servidor (usando threading.get_ident())
            import threading
            self.pid = f"http_{port}_{threading.get_ident()}"
            
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            
            # Save process info for HTTP server
            save_process_info(f"http_server_{port}", self.pid, port, 
                             url=f"http://{get_local_ip() or '127.0.0.1'}:{port}", 
                             process_type="server")
            
            (PID_DIR / f"http_server_{port}.json").write_text(json.dumps({
                "pid": self.pid,
                "port": port,
                "dir": to_portable_path(str(dir_path)),
                "start_time": datetime.datetime.now().isoformat()
            }))
            
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now().isoformat()}] HTTP Server started on port {port}, directory: {dir_path}\n")
            
            return True
        except OSError as e:
            if "Address already in use" in str(e):
                cprint(f"❌ Port {port} already in use!", "red")
            else:
                cprint(f"❌ Error starting server: {e}", "red")
            return False

    def stop(self):
        """Para o servidor HTTP"""
        if not self.httpd:
            return False
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] HTTP Server stopped\n")
        
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd = None
        
        # Remove process info
        if self.pid:
            remove_process_info(self.pid)
        
        try:
            (PID_DIR / f"http_server_{self.port}.json").unlink()
        except:
            pass
        return True
    
    def get_logs(self, lines=20):
        """Obtém últimas linhas do log"""
        if not self.log_path or not self.log_path.exists():
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        return all_lines[-lines:]
    
    def is_running(self):
        """Verifica se o servidor está rodando"""
        return self.httpd is not None


# ============================================================================
# SUBSTITUA A VARIÁVEL GLOBAL http_server (linha ~450) POR:
# ============================================================================

# Gerenciador de múltiplos servidores HTTP
http_servers = {}  # Dicionário: {port: HttpServer}


# ============================================================================
# ADICIONE ESTAS FUNÇÕES AUXILIARES (após http_servers):
# ============================================================================

def get_active_http_servers():
    """Retorna lista de servidores HTTP ativos"""
    active = []
    for port, server in list(http_servers.items()):
        if server.is_running():
            active.append({
                "port": port,
                "directory": server.directory,
                "url": f"http://{get_local_ip() or '127.0.0.1'}:{port}",
                "pid": server.pid
            })
        else:
            # Remove servidor morto
            del http_servers[port]
    return active

def stop_http_server(port):
    """Para um servidor HTTP específico"""
    if port in http_servers:
        success = http_servers[port].stop()
        if success:
            del http_servers[port]
        return success
    return False

def stop_all_http_servers():
    """Para todos os servidores HTTP"""
    for port in list(http_servers.keys()):
        stop_http_server(port)

# ============================================================================
# ADICIONE ESTA FUNÇÃO AUXILIAR (antes de show_active_urls):
# ============================================================================

def get_all_active_services():
    """
    Retorna TODOS os serviços ativos (servidores HTTP + túneis)
    em um formato unificado
    """
    all_services = []
    
    # 1. Adiciona servidores HTTP
    for port, server in list(http_servers.items()):
        if server.is_running():
            all_services.append({
                "name": f"HTTP Server (Port {port})",
                "type": "server",
                "port": port,
                "pid": server.pid,
                "url": f"http://{get_local_ip() or '127.0.0.1'}:{port}",
                "directory": to_portable_path(server.directory),
                "service_id": f"http_{port}",  # ID único para identificar
                "start_time": "N/A"  # Pode adicionar se quiser rastrear
            })
        else:
            # Remove servidor morto
            del http_servers[port]
    
    # 2. Adiciona túneis dos processos ativos
    active_processes = get_active_processes()
    tunnel_processes = [p for p in active_processes if p.get("type") == "tunnel"]
    
    for process in tunnel_processes:
        all_services.append({
            "name": process.get("name", "Unknown"),
            "type": "tunnel",
            "port": process.get("port", "?"),
            "pid": process.get("pid"),
            "url": process.get("url", tr("no_url_available")),
            "directory": None,
            "service_id": f"tunnel_{process.get('pid')}",
            "start_time": process.get("start_time", "N/A")
        })
    
    return all_services


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
        panel_content = f"[bold cyan]{centered_text}[/bold cyan]\n[bold cyan]AutoTunnel v1.4[/bold cyan]\n[green]Fast server + tunnel (cloudflared/ngrok)[/green]\n[dim]Portable • Settings saved in universal format[/dim]\n[yellow]👨💻 GitHub: https://github.com/marllondevsec[/yellow]\n[blue]🔗 LinkedIn: https://www.linkedin.com/in/marllondevsec/[/blue]"
        
        console.print(Panel(panel_content, 
                          border_style="cyan",
                          box=ROUNDED,
                          padding=(1, 2)))
    else:
        # Fallback without rich
        print(ASCII_ART_1)
        print("\n" + ASCII_ART_2)
        print("\n" + "="*60)
        print("AutoTunnel v1.4")
        print("Fast server + tunnel (cloudflared/ngrok)")
        print("Portable • Settings saved in universal format")
        print("👨💻 GitHub: https://github.com/marllondevsec")
        print("🔗 LinkedIn: https://www.linkedin.com/in/marllondevsec/")
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

# ============================================================================
# MODIFIQUE A FUNÇÃO start_tunnel_flow (linha ~700) - SEÇÃO DE SERVIDOR HTTP:
# ============================================================================

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
        
        # Verifica se a porta já está em uso
        if port in http_servers and http_servers[port].is_running():
            cprint(f"⚠️  Port {port} already has a server running!", "yellow")
            override = input("Start tunnel on existing server? (y/n): ").strip().lower()
            if override not in ['y', 'yes', 's', 'sim']:
                input(tr("press_enter"))
                return
        else:
            d = choose_dir()
            if not d:
                cprint(tr("aborted"), "red")
                input(tr("press_enter"))
                return
            
            # Cria novo servidor HTTP
            new_server = HttpServer()
            started = new_server.start(port, d)
            
            if started:
                http_servers[port] = new_server
                cprint(tr("server_started", port), "green")
                show_server_urls(port)
            else:
                cprint("❌ Failed to start server", "red")
                input(tr("press_enter"))
                return
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
    
    # Start tunnel
    plugin.start(port)
    
    cprint(tr("waiting_for_url"), "cyan")
    for i in range(40):
        url = getattr(plugin, "url", None)
        if url:
            cprint(f"✅ {tr('tunnel_url', url)}", "white")
            (DATA_DIR / "last_tunnel.url").write_text(url)
            
            # Update process info with URL
            if hasattr(plugin, 'pid') and plugin.pid:
                active_file = DATA_DIR / "active_processes.json"
                if active_file.exists():
                    try:
                        active = json.loads(active_file.read_text(encoding="utf-8"))
                        if str(plugin.pid) in active:
                            active[str(plugin.pid)]["url"] = url
                            active_file.write_text(json.dumps(active, indent=2), encoding="utf-8")
                    except:
                        pass
            
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
    """Stop a specific tunnel (interactive choice)"""
    # Clean up dead processes first
    cleanup_dead_processes()
    
    # Get active tunnel processes
    active = get_active_processes()
    tunnel_processes = [p for p in active if p.get("type") == "tunnel"]
    
    if not tunnel_processes:
        cprint(tr("no_tunnels_running"), "yellow")
        input(tr("press_enter"))
        return
    
    # If only one tunnel running, stop it directly
    if len(tunnel_processes) == 1:
        process = tunnel_processes[0]
        pid = process["pid"]
        name = process["name"]
        
        cprint(f"Stopping {name} (PID: {pid})...", "cyan")
        if stop_process_by_pid(pid):
            cprint(tr("process_stopped", name), "green")
        else:
            cprint(tr("process_stop_failed", name), "red")
        input(tr("press_enter"))
        return
    
    # Multiple tunnels - let user choose
    print_header()
    cprint(f"[bold]🛑 {tr('stop_process')}[/bold]", "cyan")
    
    opts = []
    for i, process in enumerate(tunnel_processes, 1):
        name = process.get("name", "Unknown")
        pid = process.get("pid", "?")
        port = process.get("port", "?")
        url = process.get("url", tr("no_url_available"))
        opts.append(f"{name} (PID: {pid}, Port: {port}) - {url}")
    
    opts.append(f"⬅️ {tr('back')}")
    
    sel = numeric_choice(tr("choose_process_to_stop"), opts)
    
    if sel is None or sel > len(tunnel_processes):
        return
    
    process = tunnel_processes[sel - 1]
    pid = process["pid"]
    name = process["name"]
    
    cprint(f"Stopping {name} (PID: {pid})...", "cyan")
    if stop_process_by_pid(pid):
        cprint(tr("process_stopped", name), "green")
    else:
        cprint(tr("process_stop_failed", name), "red")
    
    input(tr("press_enter"))

# ============================================================================
# SUBSTITUA A FUNÇÃO show_active_urls() COMPLETA POR ESTA:
# ============================================================================

def show_active_urls():
    """Show ACTIVE services (HTTP servers + tunnels) with management options"""
    # Clean up dead processes first
    cleanup_dead_processes()
    
    while True:
        print_header()
        cprint(f"[bold]🔗 {tr('active_urls')}[/bold]", "cyan")
        
        # Get ALL active services (servers + tunnels)
        all_services = get_all_active_services()
        
        if not all_services:
            cprint(tr("no_active_processes"), "yellow")
            
            # Still show saved URLs if no active services
            server_url_file = DATA_DIR / "last_server.url"
            tunnel_url_file = DATA_DIR / "last_tunnel.url"
            
            saved_urls = []
            if server_url_file.exists():
                saved_urls.append(("🌐 Último Servidor", server_url_file.read_text().strip()))
            if tunnel_url_file.exists():
                saved_urls.append(("🚇 Último Túnel", tunnel_url_file.read_text().strip()))
            
            if saved_urls:
                cprint(f"\n📋 URLs Salvas (não necessariamente ativas):", "yellow")
                for name, url in saved_urls:
                    cprint(f"  {name}: {url}", "white")
        
        else:
            # Display active services in a table
            if console:
                table = Table(box=None, show_header=True, padding=(0, 2))
                table.add_column("#", style="cyan", no_wrap=True)
                table.add_column(tr("name"), style="green")
                table.add_column(tr("type"), style="yellow")
                table.add_column(tr("port"), style="white")
                table.add_column(tr("url"), style="blue")
                
                for i, service in enumerate(all_services, 1):
                    name = service.get("name", "Unknown")
                    service_type = service.get("type", "unknown")
                    port = service.get("port", "?")
                    url = service.get("url", tr("no_url_available"))
                    
                    # Add directory info for HTTP servers
                    if service_type == "server" and service.get("directory"):
                        name = f"{name} ({service['directory']})"
                    
                    # Truncate long URLs for display
                    display_url = url
                    if len(url) > 50:
                        display_url = url[:47] + "..."
                    
                    # Translate type
                    type_display = tr(f"process_type_{service_type}")
                    if not type_display or type_display == f"process_type_{service_type}":
                        type_display = "Servidor" if service_type == "server" else "Túnel"
                    
                    table.add_row(
                        str(i),
                        name,
                        type_display,
                        str(port),
                        display_url
                    )
                
                console.print(table)
            
            else:
                # Fallback without Rich
                for i, service in enumerate(all_services, 1):
                    name = service.get("name", "Unknown")
                    service_type = service.get("type", "unknown")
                    port = service.get("port", "?")
                    url = service.get("url", tr("no_url_available"))
                    
                    type_display = "Servidor" if service_type == "server" else "Túnel"
                    print(f"{i}) {name} [{type_display}] - Port: {port} - {url}")
        
        # Options
        print("\n" + "="*60)
        opts = []
        
        if all_services:
            opts.append(f"🛑 Parar serviço específico")
            opts.append(f"⛔ Parar TODOS os serviços")
        
        opts.append(f"📋 {tr('copy_url')}")
        opts.append(f"⬅️ {tr('back')}")
        
        sel = numeric_choice(tr("choose_action"), opts)
        
        if sel is None:
            break
        
        # Option 1: Stop specific service
        if sel == 1 and all_services:
            if len(all_services) == 1:
                # Only one service - stop it directly
                service = all_services[0]
                service_type = service.get("type")
                name = service.get("name")
                
                cprint(f"Parando {name}...", "cyan")
                
                if service_type == "server":
                    port = service.get("port")
                    if stop_http_server(port):
                        cprint(f"✅ Servidor na porta {port} parado", "green")
                    else:
                        cprint(f"❌ Falha ao parar servidor", "red")
                else:  # tunnel
                    pid = service.get("pid")
                    if stop_process_by_pid(pid):
                        cprint(f"✅ Túnel {name} parado", "green")
                    else:
                        cprint(f"❌ Falha ao parar túnel", "red")
                
                time.sleep(1)
                continue  # Refresh the list
            
            else:
                # Multiple services - choose which to stop
                print_header()
                cprint("[bold]🛑 Parar Serviço[/bold]", "cyan")
                
                stop_opts = []
                for i, service in enumerate(all_services, 1):
                    name = service.get("name")
                    port = service.get("port")
                    service_type = service.get("type")
                    
                    type_emoji = "🌐" if service_type == "server" else "🚇"
                    stop_opts.append(f"{type_emoji} {name} (Port: {port})")
                
                stop_opts.append(f"⬅️ {tr('back')}")
                
                stop_sel = numeric_choice("Escolha o serviço para parar:", stop_opts)
                
                if stop_sel is None or stop_sel > len(all_services):
                    continue
                
                service = all_services[stop_sel - 1]
                service_type = service.get("type")
                name = service.get("name")
                
                cprint(f"Parando {name}...", "cyan")
                
                if service_type == "server":
                    port = service.get("port")
                    if stop_http_server(port):
                        cprint(f"✅ Servidor na porta {port} parado", "green")
                    else:
                        cprint(f"❌ Falha ao parar servidor", "red")
                else:  # tunnel
                    pid = service.get("pid")
                    if stop_process_by_pid(pid):
                        cprint(f"✅ Túnel {name} parado", "green")
                    else:
                        cprint(f"❌ Falha ao parar túnel", "red")
                
                time.sleep(1)
                continue  # Refresh the list
        
        # Option 2: Stop ALL services
        elif sel == 2 and all_services:
            print_header()
            cprint("[bold]⛔ Parar TODOS os Serviços[/bold]", "red")
            cprint(f"\nIsso irá parar:", "yellow")
            
            server_count = sum(1 for s in all_services if s.get("type") == "server")
            tunnel_count = sum(1 for s in all_services if s.get("type") == "tunnel")
            
            cprint(f"  • {server_count} servidor(es) HTTP", "white")
            cprint(f"  • {tunnel_count} túnel(s)", "white")
            
            confirm = input("\n❓ Tem certeza? (s/n): ").strip().lower()
            
            if confirm in ['s', 'y', 'sim', 'yes']:
                cprint("\n🛑 Parando todos os serviços...", "cyan")
                
                # Stop all HTTP servers
                stopped_servers = 0
                for service in all_services:
                    if service.get("type") == "server":
                        port = service.get("port")
                        if stop_http_server(port):
                            stopped_servers += 1
                
                # Stop all tunnels
                stopped_tunnels = 0
                for service in all_services:
                    if service.get("type") == "tunnel":
                        pid = service.get("pid")
                        if stop_process_by_pid(pid):
                            stopped_tunnels += 1
                
                cprint(f"\n✅ Parados: {stopped_servers} servidor(es), {stopped_tunnels} túnel(s)", "green")
                time.sleep(2)
                continue  # Refresh
            else:
                cprint("❌ Cancelado", "yellow")
                time.sleep(1)
                continue
        
        # Option 3 (or 1 if no services): Copy URL
        elif (sel == 3 and all_services) or (sel == 1 and not all_services):
            if not all_services:
                # No active services, try to copy saved URLs
                urls_to_copy = []
                
                server_url_file = DATA_DIR / "last_server.url"
                if server_url_file.exists():
                    urls_to_copy.append(("🌐 Último Servidor", server_url_file.read_text().strip()))
                
                tunnel_url_file = DATA_DIR / "last_tunnel.url"
                if tunnel_url_file.exists():
                    urls_to_copy.append(("🚇 Último Túnel", tunnel_url_file.read_text().strip()))
                
                if not urls_to_copy:
                    cprint(tr("no_urls_to_copy"), "yellow")
                    time.sleep(1)
                    continue
                
                if len(urls_to_copy) == 1:
                    url = urls_to_copy[0][1]
                    try:
                        import pyperclip
                        pyperclip.copy(url)
                        cprint(tr("url_copied_success"), "green")
                    except:
                        cprint(tr("url_copied"), "yellow")
                    time.sleep(1)
                else:
                    # Multiple saved URLs
                    print_header()
                    cprint(f"[bold]📋 {tr('copy_url')}[/bold]", "cyan")
                    
                    copy_opts = []
                    for i, (name, url) in enumerate(urls_to_copy, 1):
                        copy_opts.append(f"{name}")
                    
                    copy_opts.append(f"⬅️ {tr('back')}")
                    
                    copy_sel = numeric_choice(tr("choose_url_to_copy"), copy_opts)
                    
                    if copy_sel is None or copy_sel > len(urls_to_copy):
                        continue
                    
                    url = urls_to_copy[copy_sel - 1][1]
                    try:
                        import pyperclip
                        pyperclip.copy(url)
                        cprint(tr("url_copied_success"), "green")
                    except:
                        cprint(tr("url_copied"), "yellow")
                    time.sleep(1)
            
            else:
                # Copy URL from active service
                if len(all_services) == 1:
                    service = all_services[0]
                    url = service.get("url")
                    if url:
                        try:
                            import pyperclip
                            pyperclip.copy(url)
                            cprint(tr("url_copied_success"), "green")
                        except:
                            cprint(tr("url_copied"), "yellow")
                        time.sleep(1)
                    else:
                        cprint(tr("no_url_available"), "yellow")
                        time.sleep(1)
                else:
                    # Multiple services - choose which URL to copy
                    print_header()
                    cprint(f"[bold]📋 {tr('copy_url')}[/bold]", "cyan")
                    
                    copy_opts = []
                    for i, service in enumerate(all_services, 1):
                        name = service.get("name", "Unknown")
                        url = service.get("url", tr("no_url_available"))
                        service_type = service.get("type")
                        
                        type_emoji = "🌐" if service_type == "server" else "🚇"
                        
                        # Truncate for display
                        display_url = url if len(url) <= 40 else url[:37] + "..."
                        copy_opts.append(f"{type_emoji} {name}: {display_url}")
                    
                    copy_opts.append(f"⬅️ {tr('back')}")
                    
                    copy_sel = numeric_choice(tr("choose_url_to_copy"), copy_opts)
                    
                    if copy_sel is None or copy_sel > len(all_services):
                        continue
                    
                    service = all_services[copy_sel - 1]
                    url = service.get("url")
                    if url:
                        try:
                            import pyperclip
                            pyperclip.copy(url)
                            cprint(tr("url_copied_success"), "green")
                        except:
                            cprint(tr("url_copied"), "yellow")
                        time.sleep(1)
                    else:
                        cprint(tr("no_url_available"), "yellow")
                        time.sleep(1)
        
        else:
            break

# ============================================================================
# MODIFIQUE view_logs() PARA SUPORTAR MÚLTIPLOS SERVIDORES:
# ============================================================================

def view_logs():
    while True:
        print_header()
        cprint(f"[bold]{tr('menu.view_logs')}[/bold]", "cyan")
        
        logs_available = []
        
        # Adiciona logs de todos os servidores HTTP ativos
        for port, server in http_servers.items():
            if server.log_path and server.log_path.exists():
                logs_available.append((f"🌐 HTTP Server (Port {port})", server.log_path))
        
        # Adiciona logs dos plugins
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

# ============================================================================
# MODIFIQUE show_status() PARA MOSTRAR MÚLTIPLOS SERVIDORES:
# ============================================================================

def show_status():
    print_header()
    
    # Clean up dead processes first
    cleanup_dead_processes()
    
    # Get active processes
    active = get_active_processes()
    
    # Show HTTP server status
    active_servers = get_active_http_servers()
    
    if active_servers:
        cprint(f"✅ {tr('menu.start_server')}: {len(active_servers)} servidor(es) ativo(s)", "bold")
        for server_info in active_servers:
            port = server_info["port"]
            directory = to_portable_path(server_info["directory"])
            url = server_info["url"]
            
            cprint(f"\n   🌐 Port {port}:", "cyan")
            cprint(f"      Directory: {directory}", "dim")
            cprint(f"      URL: {url}", "green")
            
            # Mostra últimos logs se existir o servidor
            if port in http_servers:
                logs = http_servers[port].get_logs(2)
                if logs:
                    for log in logs[-2:]:
                        cprint(f"      {log.strip()}", "white")
    else:
        cprint(f"❌ {tr('menu.start_server')}: {tr('server_not_running')}", "bold")
    
    print()
    
    # Show tunnel status from active processes
    load_plugins()
    
    # Count active tunnels
    active_tunnels = [p for p in active if p.get("type") == "tunnel"]
    running_tunnels = len(active_tunnels)
    
    for idx, (name, plugin) in PLUGINS.items():
        installed = plugin.installed()
        
        # Check if this plugin is running
        is_running = any(p.get("name") == name for p in active_tunnels)
        
        if is_running:
            status = "✅"
        elif installed:
            status = "⚠️ "
        else:
            status = "❌"
        
        cprint(f"{status} {name}: {'running' if is_running else 'installed' if installed else 'not installed'}", "bold")
        
        # If running, show details
        if is_running:
            for process in active_tunnels:
                if process.get("name") == name:
                    url = process.get("url", None)
                    pid = process.get("pid", None)
                    if url:
                        cprint(f"   URL: {url}", "green")
                    if pid:
                        cprint(f"   PID: {pid}", "dim")
                    break
    
    print("\n" + "="*60)
    cprint(f"📊 Summary: {len(active_servers)} server(s), {running_tunnels} tunnel(s)", 
           "green" if (len(active_servers) > 0 or running_tunnels > 0) else "yellow")
    
    print("="*60)
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
    
    # Clean up dead processes on startup
    cleanup_dead_processes()
    
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
            f"🔗 {tr('view_active_urls')}",  # Changed from 'menu.show_saved_urls'
            f"⚙️ {tr('menu.settings')}",
            f"🚪 {tr('menu.exit')}"
        ]
        
        sel = numeric_choice(tr("prompt.choose_menu_numeric"), menu_opts)
        
        # ============================================================================
        # MODIFIQUE O MENU PRINCIPAL (linha ~1100) - OPÇÃO 1 (Start Server):
        # ============================================================================
        
        if sel == 1:
            port = cfg.get("default_port", 1337)
            p = input(tr("prompt.port", port) + " ").strip()
            if p:
                try:
                    port = int(p)
                except:
                    cprint(tr("invalid_port"), "red")
                    continue
            
            # Verifica se já existe servidor nesta porta
            if port in http_servers and http_servers[port].is_running():
                cprint(f"⚠️  Server already running on port {port}!", "yellow")
                input(tr("press_enter"))
                continue
            
            d = choose_dir()
            if not d:
                cprint(tr("aborted"), "red")
                time.sleep(1)
                continue
            
            # Cria novo servidor
            new_server = HttpServer()
            ok = new_server.start(port, d)
            
            if ok:
                http_servers[port] = new_server
                cprint(tr("server_started", port), "green")
                show_server_urls(port)
            else:
                cprint("❌ Failed to start server", "red")
            
            input(tr("press_enter"))
            
        elif sel == 2:
            start_tunnel_flow(only_tunnel=False)
            
        elif sel == 3:
            start_tunnel_flow(only_tunnel=True)
        
        # ============================================================================
        # MODIFIQUE O MENU PRINCIPAL - OPÇÃO 4 (Stop Server):
        # ============================================================================
            
        elif sel == 4:
            active_servers = get_active_http_servers()
            
            if not active_servers:
                cprint(tr("server_not_running"), "yellow")
                input(tr("press_enter"))
                continue
            
            if len(active_servers) == 1:
                # Para o único servidor
                port = active_servers[0]["port"]
                if stop_http_server(port):
                    cprint(tr("server_stopped"), "green")
                else:
                    cprint("❌ Failed to stop server", "red")
            else:
                # Múltiplos servidores - escolher qual parar
                print_header()
                cprint("[bold]🛑 Stop HTTP Server[/bold]", "cyan")
                
                opts = []
                for server in active_servers:
                    port = server["port"]
                    directory = to_portable_path(server["directory"])
                    opts.append(f"Port {port} - {directory}")
                
                opts.append("🛑 Stop ALL servers")
                opts.append(f"⬅️ {tr('back')}")
                
                stop_sel = numeric_choice("Choose server to stop:", opts)
                
                if stop_sel is None or stop_sel > len(opts):
                    continue
                elif stop_sel <= len(active_servers):
                    # Para servidor específico
                    port = active_servers[stop_sel - 1]["port"]
                    if stop_http_server(port):
                        cprint(f"✅ Server on port {port} stopped", "green")
                    else:
                        cprint("❌ Failed to stop server", "red")
                elif stop_sel == len(active_servers) + 1:
                    # Para todos
                    stop_all_http_servers()
                    cprint("✅ All servers stopped", "green")
            
            input(tr("press_enter"))
            
        elif sel == 5:
            stop_tunnel_flow()
            
        elif sel == 6:
            show_status()
            
        elif sel == 7:
            view_logs()
            
        elif sel == 8:  # Show active URLs
            show_active_urls()
            
        elif sel == 9:
            refresh = show_settings()
            if refresh:
                continue  # Refresh the interface with new language
        
        # ============================================================================
        # MODIFIQUE main() PARA PARAR TODOS OS SERVIDORES AO SAIR:
        # ============================================================================
            
        elif sel == 10:
            cprint("👋 Exiting...", "cyan")
            
            # Para todos os servidores HTTP
            stop_all_http_servers()
            
            # Para todos os túneis
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
