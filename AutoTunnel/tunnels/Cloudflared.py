# tunnels/Cloudflared.py - plugin portátil para cloudflared
import shutil, subprocess, threading, re, os, time, json
from pathlib import Path

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
        
        # Use portable paths
        data_dir = get_autotunnel_data_dir()
        self.log_path = data_dir / "logs" / "cloudflared.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def name(self):
        return "cloudflared"

    def installed(self):
        # Try system PATH first
        if shutil.which("cloudflared"):
            return True
        
        # Try autotunnel local bin (portable)
        data_dir = get_autotunnel_data_dir()
        local_bin = data_dir / "bin" / "cloudflared"
        return local_bin.exists()

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
            
            # Extract cloudflared URL
            patterns = [
                r"https://[^\s]+\.trycloudflare\.com",
                r"\|\s+(https://[^\s]+\.trycloudflare\.com)\s+\|"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    url = match.group(1) if match.groups() else match.group(0)
                    if not self.url:
                        self.url = url
                        self._write_log(f"URL encontrada: {url}")
                    break

    def start(self, local_port: int):
        if self.proc:
            return
        
        # Find cloudflared binary (portable)
        bin_path = None
        
        # Check system PATH
        bin_path = shutil.which("cloudflared")
        
        # Check autotunnel local bin
        if not bin_path:
            data_dir = get_autotunnel_data_dir()
            local_bin = data_dir / "bin" / "cloudflared"
            if local_bin.exists():
                bin_path = str(local_bin)
        
        if not bin_path:
            self._write_log("ERRO: cloudflared não encontrado")
            return
        
        self._write_log(f"Iniciando cloudflared na porta {local_port}")
        
        # Start cloudflared tunnel
        cmd = [bin_path, "tunnel", "--url", f"http://localhost:{local_port}"]
        
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.pid = self.proc.pid
            self._write_log(f"Processo iniciado com PID: {self.pid}")
            
            # Start reader thread
            self._reader_thread = threading.Thread(target=self._reader, daemon=True)
            self._reader_thread.start()
            
        except Exception as e:
            self._write_log(f"ERRO ao iniciar: {str(e)}")
            self.proc = None

    def stop(self):
        if not self.proc:
            return False
        
        self._write_log("Parando cloudflared...")
        
        try:
            self.proc.terminate()
            
            # Wait for termination
            for _ in range(10):
                if self.proc.poll() is not None:
                    break
                time.sleep(0.5)
            
            # Force kill if still running
            if self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait(timeout=2)
            
            self._write_log("cloudflared parado")
            
        except Exception as e:
            self._write_log(f"ERRO ao parar: {str(e)}")
            return False
        finally:
            self.proc = None
            self.pid = None
            self.url = None
        
        return True
