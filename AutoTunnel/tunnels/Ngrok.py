# tunnels/Ngrok.py - plugin for ngrok tunnel
import shutil, subprocess, threading, re, os, time, json
from pathlib import Path

class TunnelPlugin:
    def __init__(self):
        self.proc = None
        self.pid = None
        self.url = None
        self._reader_thread = None
        # log path
        self.log_path = Path.home() / ".local" / "share" / "autotunnel" / "logs" / "ngrok.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # config path
        self.config_path = Path.home() / ".config" / "autotunnel" / "config.json"

    def name(self):
        return "ngrok"

    def _get_auth_token(self):
        """Get ngrok auth token from config or environment"""
        if self.config_path.exists():
            try:
                cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
                token = cfg.get("ngrok_auth_token")
                if token:
                    return token
            except:
                pass
        return os.environ.get("NGROK_AUTH_TOKEN", "")

    def installed(self):
        """Check if ngrok is installed and configured"""
        # Check binary
        binp = shutil.which("ngrok")
        if not binp:
            alt = Path.home() / ".local" / "share" / "autotunnel" / "bin" / "ngrok"
            if not alt.exists():
                return False
            binp = str(alt)
        
        # Check if we have auth token
        token = self._get_auth_token()
        if not token:
            return False
        
        return True

    def install(self):
        """Install ngrok - will be called from main AutoTunnel"""
        # Installation is handled by install_ngrok_auto in main script
        return True

    def _write_log(self, line: str):
        """Write log entry to file"""
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line.rstrip() + "\n")
        except Exception:
            pass

    def _reader(self):
        """Read output from ngrok process and extract URL"""
        if not self.proc or not self.proc.stdout:
            return
        
        for line in iter(self.proc.stdout.readline, ''):
            if not line:
                break
            
            line = line.rstrip("\n")
            self._write_log(line)
            
            # Extract ngrok URL - multiple patterns for different ngrok versions
            patterns = [
                r"Forwarding\s+(https://[^\s]+\.ngrok\.io)\s+->",
                r"addr=https://([^\s]+\.ngrok\.io)",
                r"URL:\s+(https://[^\s]+\.ngrok\.io)",
                r"https://[^\s]+\.ngrok\.io"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    if "->" in line or "URL:" in line or "addr=" in line:
                        # Full line with context
                        url = match.group(1) if match.groups() else match.group(0)
                        if not url.startswith("http"):
                            url = f"https://{url}"
                        self.url = url
                        self._write_log(f"[INFO] URL encontrada: {self.url}")
                    else:
                        # Just the URL in the line
                        self.url = match.group(0)
                        self._write_log(f"[INFO] URL encontrada: {self.url}")
                    break
            
            # Also check for error messages
            if "error" in line.lower() or "failed" in line.lower():
                self._write_log(f"[ERROR] {line}")

    def start(self, local_port: int):
        """Start ngrok tunnel"""
        if self.proc:
            self._write_log("[WARN] Ngrok já está em execução")
            return
        
        # Find ngrok binary
        binp = shutil.which("ngrok")
        if not binp:
            alt = Path.home() / ".local" / "share" / "autotunnel" / "bin" / "ngrok"
            if not alt.exists():
                self._write_log("[ERROR] Ngrok não encontrado")
                return
            binp = str(alt)
        
        # Get auth token
        token = self._get_auth_token()
        if not token:
            self._write_log("[ERROR] Token de autenticação do ngrok não configurado")
            return
        
        # Clear previous URL
        self.url = None
        
        # Start ngrok
        cmd = [binp, "http", str(local_port)]
        
        # Set environment with auth token
        env = os.environ.copy()
        env["NGROK_AUTH_TOKEN"] = token
        
        self._write_log(f"[INFO] Iniciando ngrok na porta {local_port}")
        self._write_log(f"[INFO] Comando: {' '.join(cmd)}")
        
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            self.pid = self.proc.pid
            self._write_log(f"[INFO] Ngrok iniciado com PID: {self.pid}")
            
            # Start reader thread
            self._reader_thread = threading.Thread(target=self._reader, daemon=True)
            self._reader_thread.start()
            
        except Exception as e:
            self._write_log(f"[ERROR] Falha ao iniciar ngrok: {str(e)}")
            self.proc = None

    def stop(self):
        """Stop ngrok tunnel"""
        if not self.proc:
            return False
        
        self._write_log(f"[INFO] Parando ngrok (PID: {self.pid})")
        
        try:
            # Try graceful termination
            self.proc.terminate()
            
            # Wait for process to end
            for _ in range(10):  # 5 seconds max
                if self.proc.poll() is not None:
                    break
                time.sleep(0.5)
            
            # Force kill if still running
            if self.proc.poll() is None:
                self._write_log("[WARN] Forçando término do ngrok")
                self.proc.kill()
                self.proc.wait(timeout=2)
            
            self._write_log(f"[INFO] Ngrok parado")
            
        except Exception as e:
            self._write_log(f"[ERROR] Erro ao parar ngrok: {str(e)}")
            return False
        finally:
            self.proc = None
            self.pid = None
            self.url = None
        
        return True

    def status(self):
        """Get current status"""
        is_running = self.proc and self.proc.poll() is None
        return {
            "running": is_running,
            "pid": self.pid,
            "url": self.url,
            "installed": self.installed(),
            "log_file": str(self.log_path)
        }
