# tunnels/cloudflared.py - plugin minimal (log to file, don't print to stdout)
import shutil, subprocess, threading, re, os, time
from pathlib import Path

class TunnelPlugin:
    def __init__(self):
        self.proc = None
        self.pid = None
        self.url = None
        self._reader_thread = None
        # log path in the user's autotunnel data dir
        self.log_path = Path.home() / ".local" / "share" / "autotunnel" / "logs" / "cloudflared.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def name(self):
        return "cloudflared"

    def installed(self):
        p = shutil.which("cloudflared")
        if p:
            return True
        alt = Path.home() / ".local" / "share" / "autotunnel" / "bin" / "cloudflared"
        return alt.exists()

    def install(self):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            dst = Path.home() / ".local" / "share" / "autotunnel" / "bin"
            dst.mkdir(parents=True, exist_ok=True)
            out = dst / "cloudflared"
            import urllib.request
            urllib.request.urlretrieve(url, str(out))
            out.chmod(0o755)
            return True
        except Exception:
            return False

    def _write_log(self, line: str):
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line.rstrip() + "\n")
        except Exception:
            pass

    def _reader(self):
        # read stdout, write to log file and extract URL
        if not self.proc or not self.proc.stdout:
            return
        for ln in self.proc.stdout:
            if ln is None:
                continue
            ln = ln.rstrip("\n")
            # write to logfile only
            self._write_log(ln)
            # extract trycloudflare url (quick tunnel)
            m = re.search(r"https://[^\s]+\.trycloudflare\.com", ln)
            if m and not self.url:
                self.url = m.group(0)
            # also extract other possible https urls (ngrok style)
            if not self.url:
                m2 = re.search(r"https://[^\s]+\.(ngrok|loca\.lt|serveo\.net|trycloudflare)\b[^\s]*", ln)
                if m2:
                    self.url = m2.group(0)
        # reader finished

    def start(self, local_port: int):
        if self.proc:
            return
        binp = shutil.which("cloudflared") or str(Path.home() / ".local" / "share" / "autotunnel" / "bin" / "cloudflared")
        if not Path(binp).exists():
            # nothing printed to stdout here; caller should invoke install or handle this case
            self._write_log("cloudflared not found")
            return
        cmd = [binp, "tunnel", "--url", f"http://localhost:{local_port}"]
        # start the process capturing stdout/stderr
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.pid = self.proc.pid
        # spawn reader thread to parse output and write to log
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()
        # return immediately; autotunnel polls plugin.url

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                # give a short grace period then kill if necessary
                try:
                    self.proc.wait(timeout=3)
                except Exception:
                    self.proc.kill()
                # log stop event
                self._write_log(f"cloudflared stopped at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception:
                pass
            self.proc = None
            self.pid = None
            return True
        return False

    def status(self):
        return {"pid": self.pid, "url": self.url, "installed": self.installed(), "log": str(self.log_path)}
