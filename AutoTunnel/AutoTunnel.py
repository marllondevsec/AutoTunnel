#!/usr/bin/env python3
"""
AutoTunnel - Minimal, numeric menus, colored (rich), auto-install cloudflared/ngrok,
and default to the user's current working directory (pwd).
"""
import os, sys, json, shutil, subprocess, threading, time, re, importlib.util
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import datetime

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
    "installed_tunnels": {},
    "ngrok_auth_token": ""
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
            # ensure default_dir is at least current cwd if missing or invalid
            default_dir = cfg.get("default_dir", "")
            if not default_dir or not Path(default_dir).exists():
                cfg["default_dir"] = str(Path.cwd())
            return cfg
        except Exception:
            pass
    
    # Try to set a reasonable default directory
    cwd = str(Path.cwd())
    # Check if we're in a web directory
    web_dirs = ['public', 'www', 'htdocs', 'html', 'src', 'dist', 'build']
    for web_dir in web_dirs:
        if Path(cwd, web_dir).exists():
            cwd = str(Path(cwd, web_dir))
            break
    
    DEFAULT_CONFIG["default_dir"] = cwd
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

# ---------------- Custom HTTP Handler to suppress logs ----------------
class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Only log to file, not to console
        log_entry = "%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args
        )
        # Write to HTTP server log file
        log_path = LOG_DIR / "http_server.log"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

# ---------------- HttpServer minimal ----------------
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
        
        # Validate and resolve directory
        dir_path = Path(directory).expanduser()
        if not dir_path.exists():
            # Try to create directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                # Create a simple index.html if directory is empty
                index_file = dir_path / "index.html"
                if not index_file.exists():
                    index_file.write_text(f"""
<!DOCTYPE html>
<html>
<head><title>AutoTunnel Server</title></head>
<body>
    <h1>AutoTunnel HTTP Server</h1>
    <p>Server is running on port {port}</p>
    <p>Directory: {dir_path}</p>
    <p>Started at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>
                    """)
            except Exception as e:
                cprint(f"Erro criando diretório {dir_path}: {e}", "red")
                return False
        
        directory = str(dir_path.resolve())
        
        # Clear old log
        if self.log_path.exists():
            self.log_path.unlink()
        
        handler = lambda *args, **kwargs: QuietHTTPRequestHandler(*args, directory=directory, **kwargs)
        self.httpd = ThreadingHTTPServer(("", int(port)), handler)
        self.port = port
        self.directory = directory
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        
        (PID_DIR / "http_server.json").write_text(json.dumps({
            "pid": os.getpid(),
            "port": port,
            "dir": directory,
            "start_time": datetime.datetime.now().isoformat()
        }))
        
        # Log startup
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] HTTP Server started on port {port}, directory: {directory}\n")
        
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
        """Return last n lines of server logs"""
        if not self.log_path.exists():
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        return all_lines[-lines:]

http_server = HttpServer()

# ---------------- Plugin loader ----------------
PLUGINS = {}  # index(int) -> (name, instance)
def load_plugins():
    PLUGINS.clear()
    if not PLUGIN_DIR.exists():
        return
    
    # Always load Cloudflared
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
    
    # Try to load Ngrok if file exists
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
            cprint(f"Erro carregando plugin {name}: {e}", "yellow")
            continue
        
        if hasattr(mod, "TunnelPlugin"):
            try:
                inst = mod.TunnelPlugin()
                PLUGINS[idx] = (inst.name(), inst)
                idx += 1
            except Exception as e:
                cprint(f"Erro inicializando plugin {name}: {e}", "yellow")

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
        console.print(Panel("[bold cyan]AutoTunnel[/bold cyan]\n[green]Servidor rápido + túnel (cloudflared/ngrok)[/green]"), justify="center")
    else:
        print("\n=== AutoTunnel ===\nServidor rápido + túnel (cloudflared/ngrok)\n")

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

# ---------------- Directory selection (improved) ----------------
def choose_dir():
    """Improved directory selection with validation"""
    cwd = str(Path.cwd())
    default_dir = cfg.get("default_dir", cwd)
    
    # Check if default directory exists
    if not Path(default_dir).exists():
        cprint(f"Diretório padrão não existe: {default_dir}", "yellow")
        # Try to create it
        try:
            Path(default_dir).mkdir(parents=True, exist_ok=True)
            cprint(f"Diretório criado: {default_dir}", "green")
        except Exception as e:
            cprint(f"Erro criando diretório {default_dir}: {e}", "red")
            default_dir = cwd
    
    while True:
        print_header()
        cprint(f"Diretório atual: {cwd}", "cyan")
        cprint(f"Diretório padrão: {default_dir}", "cyan")
        
        opts = [
            "Diretório atual (PWD)",
            "Diretório padrão",
            "Especificar outro diretório",
            "Criar novo diretório",
            "Voltar"
        ]
        
        sel = numeric_choice("Escolha diretório:", opts)
        
        if sel == 1:
            return cwd
        elif sel == 2:
            return default_dir
        elif sel == 3:
            path = input("Digite o caminho do diretório: ").strip()
            if not path:
                continue
            try:
                full_path = str(Path(path).expanduser().resolve())
                if Path(full_path).exists():
                    return full_path
                else:
                    cprint(f"Diretório não existe: {full_path}", "yellow")
                    create = input("Criar diretório? (s/n): ").strip().lower()
                    if create in ['s', 'y', 'sim', 'yes']:
                        Path(full_path).mkdir(parents=True, exist_ok=True)
                        return full_path
            except Exception as e:
                cprint(f"Erro no caminho: {e}", "red")
        elif sel == 4:
            path = input("Digite o caminho do novo diretório: ").strip()
            if path:
                try:
                    full_path = str(Path(path).expanduser().resolve())
                    Path(full_path).mkdir(parents=True, exist_ok=True)
                    cprint(f"Diretório criado: {full_path}", "green")
                    # Update default directory in config
                    cfg["default_dir"] = full_path
                    save_config()
                    time.sleep(1)
                    return full_path
                except Exception as e:
                    cprint(f"Erro criando diretório {path}: {e}", "red")
                    time.sleep(2)
        elif sel == 5 or sel is None:
            return None

# ---------------- Cloudflared installer helper ----------------
def install_cloudflared_auto():
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    tmp = Path("/tmp/cloudflared-autotunnel")
    
    try:
        import urllib.request
        cprint("Baixando e instalando cloudflared...", "yellow")
        urllib.request.urlretrieve(url, str(tmp))
        tmp.chmod(0o755)
        
        # Try system installation first
        target = Path("/usr/local/bin/cloudflared")
        try:
            subprocess.run(["sudo", "mv", str(tmp), str(target)], check=True)
            subprocess.run(["sudo", "chmod", "+x", str(target)], check=False)
            cprint(f"cloudflared instalado em {target} (sistema)", "green")
            cfg.setdefault("installed_tunnels", {})["cloudflared"] = str(target)
            save_config()
            return True
        except Exception:
            # Fallback to local bin
            dst = LOCAL_BIN / "cloudflared"
            shutil.copy(str(tmp), str(dst))
            dst.chmod(0o755)
            tmp.unlink()
            cprint(f"cloudflared instalado localmente em {dst}", "green")
            cfg.setdefault("installed_tunnels", {})["cloudflared"] = str(dst)
            save_config()
            return True
    except Exception as e:
        cprint(f"Erro instalando cloudflared: {e}", "red")
        return False

# ---------------- Ngrok installer helper ----------------
def install_ngrok_auto():
    """Install ngrok and configure auth token"""
    # Download ngrok
    url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
    tmp_tar = Path("/tmp/ngrok.tgz")
    
    try:
        import urllib.request
        import tarfile
        
        cprint("Baixando e instalando ngrok...", "yellow")
        urllib.request.urlretrieve(url, str(tmp_tar))
        
        # Extract ngrok
        with tarfile.open(tmp_tar, 'r:gz') as tar:
            tar.extract('ngrok', path="/tmp")
        
        tmp_ngrok = Path("/tmp/ngrok")
        
        # Move to local bin
        dst = LOCAL_BIN / "ngrok"
        shutil.copy(str(tmp_ngrok), str(dst))
        dst.chmod(0o755)
        
        # Clean up
        tmp_tar.unlink()
        tmp_ngrok.unlink()
        
        # Configure auth token if not set
        if not cfg.get("ngrok_auth_token"):
            cprint("Ngrok requer token de autenticação", "yellow")
            cprint("Obtenha um token em: https://dashboard.ngrok.com/get-started/your-authtoken", "cyan")
            token = input("Digite seu token do ngrok: ").strip()
            if token:
                cfg["ngrok_auth_token"] = token
                save_config()
                # Configure ngrok with token
                subprocess.run([str(dst), "config", "add-authtoken", token], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cprint("Token do ngrok salvo", "green")
        
        cfg.setdefault("installed_tunnels", {})["ngrok"] = str(dst)
        save_config()
        cprint(f"ngrok instalado em {dst}", "green")
        return True
        
    except Exception as e:
        cprint(f"Erro instalando ngrok: {e}", "red")
        return False

# ---------------- Save config helper ----------------
def save_config():
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# ---------------- Tunnel orchestration ----------------
def start_tunnel_flow(only_tunnel=False):
    load_plugins()
    if not PLUGINS:
        cprint("Nenhum plugin encontrado", "red")
        input("Pressione Enter para continuar...")
        return
    
    # Show plugin options
    opts = [f"{name}" for _, (name,_) in PLUGINS.items()]
    sel = numeric_choice("Escolha um plugin (número):", opts)
    
    if sel is None:
        cprint("Escolha inválida", "red")
        input("Pressione Enter para continuar...")
        return
    
    name, plugin = PLUGINS[sel]
    
    # Check if plugin is installed
    if not plugin.installed():
        cprint(f"Plugin {name} não está instalado", "yellow")
        install_now = input("Instalar agora? (s/n): ").strip().lower()
        
        if install_now in ['s', 'y', 'sim', 'yes']:
            if name == "cloudflared":
                ok = install_cloudflared_auto()
            elif name == "ngrok":
                ok = install_ngrok_auto()
            else:
                ok = plugin.install()
            
            if not ok:
                cprint("Instalação falhou", "red")
                input("Pressione Enter para continuar...")
                return
        else:
            cprint("Instalação cancelada", "yellow")
            input("Pressione Enter para continuar...")
            return
    
    # Get port
    port = cfg.get("default_port", 1337)
    if not only_tunnel:
        p = input(f"Porta HTTP (padrão {port}): ").strip()
        if p:
            try:
                port = int(p)
            except:
                cprint("Porta inválida", "red")
                port = cfg.get("default_port", 1337)
        
        # Start HTTP server
        d = choose_dir()
        if not d:
            cprint("Abortado", "red")
            input("Pressione Enter para continuar...")
            return
        
        started = http_server.start(port, d)
        if started:
            cprint(f"Servidor iniciado na porta {port}", "green")
        else:
            cprint("Servidor já está rodando", "yellow")
    else:
        # Tunnel only mode - still need port
        p = input(f"Porta local para o túnel (padrão {port}): ").strip()
        if p:
            try:
                port = int(p)
            except:
                cprint("Porta inválida", "red")
                port = cfg.get("default_port", 1337)
    
    # Start tunnel
    cprint(f"Iniciando túnel ({name})...", "cyan")
    
    # For ngrok, check if auth token is configured
    if name == "ngrok" and not cfg.get("ngrok_auth_token"):
        cprint("Token do ngrok não configurado", "yellow")
        token = input("Digite seu token do ngrok: ").strip()
        if token:
            cfg["ngrok_auth_token"] = token
            save_config()
            # Configure ngrok
            ngrok_path = cfg.get("installed_tunnels", {}).get("ngrok", "ngrok")
            subprocess.run([ngrok_path, "config", "add-authtoken", token],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    plugin.start(port)
    
    # Wait for URL
    cprint("Aguardando URL do túnel...", "cyan")
    for i in range(40):
        url = getattr(plugin, "url", None)
        if url:
            cprint(f"Túnel ativo: {url}", "bold green")
            (DATA_DIR / "last_tunnel.url").write_text(url)
            
            # Copy URL to clipboard if possible
            try:
                import pyperclip
                pyperclip.copy(url)
                cprint("URL copiada para a área de transferência", "green")
            except:
                pass
            
            input("Pressione Enter para continuar...")
            return
        time.sleep(0.5)
    
    cprint("Túnel iniciado mas URL não encontrada (ver logs).", "yellow")
    cprint("Verifique os logs para mais informações", "cyan")
    input("Pressione Enter para continuar...")

def stop_tunnel_flow():
    load_plugins()
    if not PLUGINS:
        cprint("Nenhum plugin encontrado", "red")
        input("Pressione Enter para continuar...")
        return
    
    # Get running tunnels
    running_tunnels = []
    for idx, (name, plugin) in PLUGINS.items():
        if hasattr(plugin, 'proc') and plugin.proc:
            running_tunnels.append((idx, name, plugin))
    
    if not running_tunnels:
        cprint("Nenhum túnel em execução", "yellow")
        input("Pressione Enter para continuar...")
        return
    
    # If only one tunnel running, stop it directly
    if len(running_tunnels) == 1:
        idx, name, plugin = running_tunnels[0]
        ok = plugin.stop()
        cprint(f"Túnel {name}: {'sucesso' if ok else 'falhou'}", 
               "green" if ok else "red")
        input("Pressione Enter para continuar...")
        return
    
    # Multiple tunnels - let user choose
    opts = [f"{name}" for _, name, _ in running_tunnels]
    sel = numeric_choice("Escolha o túnel para parar:", opts)
    
    if sel is None:
        cprint("Escolha inválida", "red")
        input("Pressione Enter para continuar...")
        return
    
    # Find selected tunnel
    for i, (_, name, plugin) in enumerate(running_tunnels, 1):
        if i == sel:
            ok = plugin.stop()
            cprint(f"Túnel {name}: {'sucesso' if ok else 'falhou'}",
                   "green" if ok else "red")
            input("Pressione Enter para continuar...")
            return

# ---------------- Log viewer ----------------
def view_logs():
    """View logs from different sources"""
    while True:
        print_header()
        cprint("[bold]Visualizador de Logs[/bold]", "cyan")
        
        logs_available = []
        
        # Check HTTP server logs
        if http_server.log_path.exists():
            logs_available.append(("HTTP Server", http_server.log_path))
        
        # Check tunnel logs
        load_plugins()
        for idx, (name, plugin) in PLUGINS.items():
            if hasattr(plugin, 'log_path') and plugin.log_path and Path(plugin.log_path).exists():
                logs_available.append((f"Tunnel {name}", plugin.log_path))
        
        if not logs_available:
            cprint("Nenhum log disponível", "yellow")
            input("Pressione Enter para continuar...")
            return
        
        # Build menu options
        opts = [f"{name}" for name, _ in logs_available]
        opts.append("Voltar")
        
        sel = numeric_choice("Escolha o log para visualizar:", opts)
        
        if sel is None or sel > len(logs_available):
            return
        
        if sel <= len(logs_available):
            name, log_path = logs_available[sel - 1]
            show_log_file(name, log_path)

def show_log_file(name, log_path):
    """Display log file content"""
    while True:
        print_header()
        cprint(f"[bold]Log: {name}[/bold]", "cyan")
        cprint(f"[dim]Arquivo: {log_path}[/dim]", "white")
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                cprint("Log vazio", "yellow")
            else:
                # Show last 50 lines
                start = max(0, len(lines) - 50)
                for line in lines[start:]:
                    # Color code different types of log entries
                    line = line.rstrip()
                    if "ERROR" in line or "error" in line.lower():
                        cprint(line, "red")
                    elif "WARN" in line or "warning" in line.lower():
                        cprint(line, "yellow")
                    elif "https://" in line:
                        # Highlight URLs
                        parts = line.split("https://")
                        if len(parts) > 1:
                            cprint(parts[0], "white", end="")
                            cprint("https://" + parts[1], "green")
                        else:
                            cprint(line, "white")
                    else:
                        cprint(line, "white")
            
            print("\n" + "="*60)
            opts = [
                "Atualizar",
                "Limpar log",
                "Monitorar em tempo real",
                "Voltar"
            ]
            
            sel = numeric_choice("Ação:", opts)
            
            if sel == 1:
                continue  # Refresh
            elif sel == 2:
                # Clear log
                confirm = input("Tem certeza que deseja limpar o log? (s/n): ").strip().lower()
                if confirm in ['s', 'y', 'sim', 'yes']:
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write(f"[{datetime.datetime.now().isoformat()}] Log cleared\n")
                    cprint("Log limpo", "green")
                    time.sleep(1)
            elif sel == 3:
                # Tail mode (follow log)
                tail_log(name, log_path)
            else:
                break
                
        except Exception as e:
            cprint(f"Erro lendo log: {e}", "red")
            input("Pressione Enter para continuar...")
            break

def tail_log(name, log_path):
    """Follow log file in real-time"""
    print_header()
    cprint(f"[bold]Monitorando: {name}[/bold]", "cyan")
    cprint(f"[dim]Pressione Ctrl+C para voltar[/dim]", "white")
    print("-" * 60)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    line = line.rstrip()
                    if "ERROR" in line or "error" in line.lower():
                        cprint(line, "red")
                    elif "WARN" in line or "warning" in line.lower():
                        cprint(line, "yellow")
                    elif "https://" in line:
                        parts = line.split("https://")
                        if len(parts) > 1:
                            cprint(parts[0], "white", end="")
                            cprint("https://" + parts[1], "green")
                        else:
                            cprint(line, "white")
                    else:
                        cprint(line, "white")
                else:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        cprint(f"Erro: {e}", "red")

# ---------------- Status display ----------------
def show_status():
    """Display current status of servers and tunnels"""
    print_header()
    
    # HTTP Server status
    if http_server.httpd:
        cprint(f"[green]●[/green] HTTP Server: porta {http_server.port}", "bold")
        cprint(f"   Diretório: {http_server.directory}", "dim")
        
        # Show last few requests
        logs = http_server.get_logs(5)
        if logs:
            cprint("\n   Últimas requisições:", "cyan")
            for log in logs[-5:]:
                cprint(f"   {log.strip()}", "white")
    else:
        cprint(f"[red]●[/red] HTTP Server: parado", "bold")
    
    print()
    
    # Tunnel status
    load_plugins()
    running_tunnels = 0
    
    for idx, (name, plugin) in PLUGINS.items():
        installed = plugin.installed()
        is_running = hasattr(plugin, 'proc') and plugin.proc and plugin.proc.poll() is None
        
        if is_running:
            running_tunnels += 1
            status_icon = "[green]●[/green]"
            status_text = "executando"
        elif installed:
            status_icon = "[yellow]●[/yellow]"
            status_text = "instalado"
        else:
            status_icon = "[red]●[/red]"
            status_text = "não instalado"
        
        cprint(f"{status_icon} {name}: {status_text}", "bold")
        
        if is_running:
            url = getattr(plugin, 'url', None)
            pid = getattr(plugin, 'pid', None)
            if url:
                cprint(f"   URL: {url}", "green")
            if pid:
                cprint(f"   PID: {pid}", "dim")
    
    print("\n" + "="*60)
    cprint(f"Resumo: {running_tunnels} túnel(s) ativo(s)", 
           "green" if running_tunnels > 0 else "yellow")
    input("Pressione Enter para continuar...")

# ---------------- Settings ----------------
def show_settings():
    """Configuration settings"""
    global I18N, LANG
    
    while True:
        print_header()
        cprint("[bold]Configurações[/bold]", "cyan")
        
        cprint(f"\nIdioma atual: {LANG}", "white")
        cprint(f"Porta padrão: {cfg.get('default_port', 1337)}", "white")
        cprint(f"Diretório padrão: {cfg.get('default_dir', '')}", "white")
        
        if cfg.get('ngrok_auth_token'):
            cprint(f"Ngrok Token: {'*' * 20}", "white")
        else:
            cprint("Ngrok Token: Não configurado", "yellow")
        
        print()
        opts = [
            "Alterar idioma",
            "Alterar porta padrão",
            "Alterar diretório padrão",
            "Configurar token do ngrok",
            "Voltar"
        ]
        
        sel = numeric_choice("Escolha configuração:", opts)
        
        if sel == 1:
            # Change language
            lang_opts = ["Português (pt)", "English (en)"]
            lsel = numeric_choice("Escolha o idioma (número):", lang_opts)
            if lsel == 1:
                cfg["language"] = "pt"
            elif lsel == 2:
                cfg["language"] = "en"
            save_config()
            # Update global variables
            LANG = cfg["language"]
            I18N = load_lang(LANG)
            cprint("Idioma salvo", "green")
            time.sleep(1)
            return  # Need to reload the interface
        elif sel == 2:
            # Change default port
            new_port = input("Nova porta padrão: ").strip()
            if new_port:
                try:
                    cfg["default_port"] = int(new_port)
                    save_config()
                    cprint("Porta salva", "green")
                    time.sleep(1)
                except:
                    cprint("Porta inválida", "red")
                    time.sleep(2)
        elif sel == 3:
            # Change default directory
            new_dir = choose_dir()
            if new_dir:
                cfg["default_dir"] = new_dir
                save_config()
                cprint("Diretório salvo", "green")
                time.sleep(1)
        elif sel == 4:
            # Configure Ngrok token
            token = input("Digite seu token do ngrok: ").strip()
            if token:
                cfg["ngrok_auth_token"] = token
                save_config()
                cprint("Token do ngrok salvo", "green")
                time.sleep(1)
        else:
            break

# ---------------- Main loop ----------------
def main():
    load_plugins()
    
    while True:
        print_header()
        
        menu_opts = [
            "Iniciar servidor HTTP",
            "Iniciar túnel com servidor",
            "Iniciar túnel sem servidor",
            "Parar servidor HTTP",
            "Parar túnel",
            "Status atual",
            "Visualizar logs",
            "Configurações",
            "Sair"
        ]
        
        sel = numeric_choice("Escolha uma opção (número):", menu_opts)
        
        if sel == 1:
            # Start HTTP server
            port = cfg.get("default_port", 1337)
            p = input(f"Porta HTTP (padrão {port}): ").strip()
            if p:
                try:
                    port = int(p)
                except:
                    cprint("Porta inválida", "red")
                    continue
            
            d = choose_dir()
            if not d:
                cprint("Abortado", "red")
                time.sleep(1)
                continue
            
            ok = http_server.start(port, d)
            cprint(f"Servidor iniciado na porta {port}" if ok else "Servidor já está rodando", "green")
            input("Pressione Enter para continuar...")
            
        elif sel == 2:
            # Start tunnel with server
            start_tunnel_flow(only_tunnel=False)
            
        elif sel == 3:
            # Start tunnel only
            start_tunnel_flow(only_tunnel=True)
            
        elif sel == 4:
            # Stop HTTP server
            if http_server.stop():
                cprint("Servidor parado", "green")
            else:
                cprint("Servidor não está em execução", "yellow")
            input("Pressione Enter para continuar...")
            
        elif sel == 5:
            # Stop tunnel
            stop_tunnel_flow()
            
        elif sel == 6:
            # Status
            show_status()
            
        elif sel == 7:
            # View logs
            view_logs()
            
        elif sel == 8:
            # Settings
            show_settings()
            
        elif sel == 9:
            # Exit
            cprint("Saindo...", "cyan")
            try:
                http_server.stop()
            except:
                pass
            
            # Stop all running tunnels
            load_plugins()
            for _, (_, plugin) in PLUGINS.items():
                try:
                    if hasattr(plugin, 'proc') and plugin.proc:
                        plugin.stop()
                except:
                    pass
            
            break
        else:
            cprint("Escolha inválida", "red")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cprint("\nInterrompido pelo usuário", "yellow")
    except Exception as e:
        cprint(f"\nErro fatal: {e}", "red")
        import traceback
        traceback.print_exc()
