# tunnels/Ngrok.py - plugin portátil para ngrok
import shutil, subprocess, threading, re, os, time, json, sys
from pathlib import Path

# Import AutoTunnel functions
sys.path.insert(0, str(Path(__file__).parent.parent))
from AutoTunnel import save_process_info, remove_process_info

def get_autotunnel_data_dir():
    """Get portable data directory - matches AutoTunnel.py"""
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    if xdg_data_home:
        return Path(xdg_data_home) / "autotunnel"
    return Path.home() / ".local" / "share" / "autotunnel"

def get_autotunnel_config_dir():
    """Get portable config directory - matches AutoTunnel.py"""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        return Path(xdg_config_home) / "autotunnel"
    return Path.home() / ".config" / "autotunnel"

class TunnelPlugin:
    def __init__(self):
        self.proc = None
        self.pid = None
        self.url = None
        self._reader_thread = None
        self._active = False
        
        # Use portable paths
        data_dir = get_autotunnel_data_dir()
        self.log_path = data_dir / "logs" / "ngrok.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.config_dir = get_autotunnel_config_dir()

    def name(self):
        return "ngrok"

    def _get_auth_token(self):
        """Get ngrok token from config"""
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("ngrok_auth_token", "")
            except:
                pass
        return ""

    def installed(self):
        # Check if binary exists
        if shutil.which("ngrok"):
            # Also need token
            return bool(self._get_auth_token())
        
        # Check autotunnel local bin
        data_dir = get_autotunnel_data_dir()
        local_bin = data_dir / "bin" / "ngrok"
        if local_bin.exists():
            return bool(self._get_auth_token())
        
        return False

    def install(self):
        # Installation handled by main AutoTunnel
        return False

    def _write_log(self, line: str):
        """Write to log file"""
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {line}\n")
        except Exception:
            pass

    def _reader(self):
        """Read process output and extract URL"""
        if not self.proc or not self.proc.stdout:
            return
        
        for line in iter(self.proc.stdout.readline, ''):
            if not line:
                break
            
            line = line.rstrip("\n")
            self._write_log(line)
            
            # Extract ngrok URL
            patterns = [
                r"Forwarding\s+(https://[^\s]+\.ngrok\.io)\s+->",
                r"URL:\s+(https://[^\s]+\.ngrok\.io)",
                r"addr=https://([^\s]+\.ngrok\.io)",
                r"https://[^\s]+\.ngrok\.io",
                r"Forwarding\s+(http://[^\s]+\.ngrok\.io)\s+->",
                r"tunnel session started.*(https?://[^\s]+\.ngrok\.io)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    url = match.group(1) if match.groups() else match.group(0)
                    if not url.startswith("http"):
                        url = f"https://{url}"
                    
                    if not self.url:
                        self.url = url
                        self._write_log(f"URL encontrada: {url}")
                        
                        # Update process info with URL
                        if self.pid:
                            # We need to update the saved process info
                            data_dir = get_autotunnel_data_dir()
                            active_file = data_dir / "active_processes.json"
                            if active_file.exists():
                                try:
                                    active = json.loads(active_file.read_text(encoding="utf-8"))
                                    if str(self.pid) in active:
                                        active[str(self.pid)]["url"] = url
                                        active_file.write_text(json.dumps(active, indent=2), encoding="utf-8")
                                except:
                                    pass
                    break

    def start(self, local_port: int):
        if self.proc:
            self.stop()
        
        # Find ngrok binary (portable)
        bin_path = None
        
        # Check system PATH
        bin_path = shutil.which("ngrok")
        
        # Check autotunnel local bin
        if not bin_path:
            data_dir = get_autotunnel_data_dir()
            local_bin = data_dir / "bin" / "ngrok"
            if local_bin.exists():
                bin_path = str(local_bin)
        
        if not bin_path:
            self._write_log("ERRO: ngrok não encontrado")
            return False
        
        # Get auth token
        token = self._get_auth_token()
        if not token:
            self._write_log("ERRO: Token ngrok não configurado")
            return False
        
        self._write_log(f"Iniciando ngrok na porta {local_port}")
        
        # Configure token if needed
        config_result = subprocess.run(
            [bin_path, "config", "add-authtoken", token],
            capture_output=True,
            text=True
        )
        
        if config_result.returncode != 0:
            self._write_log(f"AVISO: Falha ao configurar token: {config_result.stderr[:100]}")
        
        # Start ngrok tunnel
        cmd = [bin_path, "http", str(local_port)]
        
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.pid = self.proc.pid
            self._active = True
            self._write_log(f"Processo iniciado com PID: {self.pid}")
            
            # Save process info
            save_process_info("ngrok", self.pid, local_port, process_type="tunnel")
            
            # Start reader thread
            self._reader_thread = threading.Thread(target=self._reader, daemon=True)
            self._reader_thread.start()
            
            return True
            
        except Exception as e:
            self._write_log(f"ERRO ao iniciar: {str(e)}")
            self.proc = None
            self._active = False
            return False

    def stop(self):
        if not self.proc and not self._active:
            return False
        
        self._write_log("Parando ngrok...")
        
        success = True
        
        try:
            if self.proc:
                self.proc.terminate()
                
                # Wait for termination
                for _ in range(10):
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.5)
                
                # Force kill if still running
                if self.proc.poll() is None:
                    self.proc.kill()
                    try:
                        self.proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                
                self._write_log("ngrok parado")
            
            # Remove process info
            if self.pid:
                remove_process_info(self.pid)
                
        except Exception as e:
            self._write_log(f"ERRO ao parar: {str(e)}")
            success = False
        finally:
            self.proc = None
            self.pid = None
            self.url = None
            self._active = False
        
        return success
    
    def is_running(self):
        """Check if tunnel is running"""
        if not self.proc:
            return False
        
        # Check if process is still alive
        try:
            return self.proc.poll() is None
        except:
            return False
