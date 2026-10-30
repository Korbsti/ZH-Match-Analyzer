"""
ZH Match Analyzer - Launcher
============================
Double-click (or run the built ZH_Match_Analyzer.exe) to:

  1. start a tiny local web server (127.0.0.1 only - nothing is exposed to the network),
  2. open the analyzer in your default browser,
  3. serve your Zero Hour replay folder to the page so replays load automatically,
  4. create a Desktop shortcut the first time it runs.

Options
  --port N         preferred port (default 8765, falls forward if busy)
  --replays DIR    replay folder to serve (otherwise auto-detected)
  --no-browser     do not open the browser
  --shortcut       (re)create the Desktop shortcut and exit
  --no-shortcut    never create a shortcut
  --record         also run the live telemetry recorder in this window
"""

import argparse
import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

APP_NAME = "ZH Match Analyzer"
HTML_NAME = "ZH_Replay_Analyzer.html"
DEFAULT_PORT = 8765
PING_PATH = "/__zhma_ping"
PING_REPLY = b"ZHMA-OK"
REPLAY_EXTS = (".rep", ".zhtelemetry")
MAX_LISTING = 200

FROZEN = getattr(sys, "frozen", False)
BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~/.config"), "ZHMatchAnalyzer")


# ----------------------------------------------------------------------------
# Locating files
# ----------------------------------------------------------------------------
def html_path():
    """Prefer an HTML file sitting next to the exe (so users can edit/update it)."""
    for base in (HOME_DIR, BUNDLE_DIR):
        p = os.path.join(base, HTML_NAME)
        if os.path.isfile(p):
            return p
    return None


def find_replay_dir(cli_dir=None):
    if cli_dir and os.path.isdir(cli_dir):
        return os.path.abspath(cli_dir)
    env = os.environ.get("ZH_REPLAY_DIR")
    if env and os.path.isdir(env):
        return env
    saved = os.path.join(CONFIG_DIR, "replay_dir.txt")
    try:
        with open(saved, encoding="utf-8") as f:
            p = f.read().strip()
        if p and os.path.isdir(p):
            return p
    except OSError:
        pass

    names = [
        "Command and Conquer Generals Zero Hour Data",
        "Command & Conquer Generals Zero Hour Data",
        "Command and Conquer Generals Data",
    ]
    roots = [
        os.path.expanduser("~/OneDrive/Documents"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/OneDrive/Dokumente"),
        os.path.expanduser("~/Dokumente"),
    ]
    for root in roots:
        for n in names:
            p = os.path.join(root, n, "Replays")
            if os.path.isdir(p):
                return p
    # next to the exe / current folder
    for base in (HOME_DIR, os.getcwd()):
        try:
            if any(f.lower().endswith(".rep") for f in os.listdir(base)):
                return base
        except OSError:
            pass
    return None


# ----------------------------------------------------------------------------
# HTTP server
# ----------------------------------------------------------------------------
class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "ZHMA/6.0"
    replay_dir = None

    def log_message(self, *args):  # keep the console quiet
        pass

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        return host in ("127.0.0.1", "localhost", "[::1]", "")

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_HEAD = None  # set below

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"Forbidden")
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == PING_PATH:
            return self._send(200, PING_REPLY)

        if path in ("/", "/index.html", "/" + HTML_NAME):
            hp = html_path()
            if not hp:
                return self._send(500, ("%s not found next to the launcher." % HTML_NAME).encode())
            with open(hp, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")

        if path == "/replays/" or path == "/replays":
            return self._listing()

        if path.startswith("/replays/"):
            return self._replay_file(path[len("/replays/"):])

        if path == "/__info":
            info = {"app": APP_NAME, "replay_dir": self.replay_dir, "frozen": FROZEN}
            return self._send(200, json.dumps(info).encode(), "application/json")

        self._send(404, b"Not found")

    do_HEAD = do_GET

    def _listing(self):
        d = self.replay_dir
        rows = []
        if d and os.path.isdir(d):
            try:
                for n in os.listdir(d):
                    if n.lower().endswith(REPLAY_EXTS):
                        fp = os.path.join(d, n)
                        try:
                            rows.append((os.path.getmtime(fp), n))
                        except OSError:
                            pass
            except OSError:
                pass
        rows.sort(reverse=True)
        links = "\n".join(
            '<a href="/replays/%s">%s</a>' % (urllib.parse.quote(n), n.replace("<", "&lt;"))
            for _, n in rows[:MAX_LISTING]
        )
        page = "<!doctype html><meta charset=utf-8><title>Replays</title><body>%s</body>" % links
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def _replay_file(self, name):
        d = self.replay_dir
        base = os.path.basename(name)
        if not d or base != name or not base.lower().endswith(REPLAY_EXTS):
            return self._send(404, b"Not found")
        fp = os.path.join(d, base)
        if not os.path.isfile(fp):
            return self._send(404, b"Not found")
        with open(fp, "rb") as f:
            self._send(200, f.read(), "application/octet-stream")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"  # on Windows reuse would allow port hijacking


def already_running(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, PING_PATH), timeout=0.8) as r:
            return r.read() == PING_REPLY
    except Exception:
        return False


def port_free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


# ----------------------------------------------------------------------------
# Desktop shortcut
# ----------------------------------------------------------------------------
def _ps_quote(s):
    return "'" + s.replace("'", "''") + "'"


def create_shortcut_windows():
    if FROZEN:
        target, args, icon = sys.executable, "", sys.executable + ",0"
        workdir = HOME_DIR
    else:
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        target = pyw if os.path.isfile(pyw) else sys.executable
        args = '"%s"' % os.path.abspath(__file__)
        ico = os.path.join(HOME_DIR, "zh_icon.ico")
        icon = ico if os.path.isfile(ico) else target + ",0"
        workdir = HOME_DIR
    script = (
        "$d=[Environment]::GetFolderPath('Desktop');"
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d %s));"
        "$s.TargetPath=%s;$s.Arguments=%s;$s.WorkingDirectory=%s;$s.IconLocation=%s;"
        "$s.Description=%s;$s.Save()"
    ) % (
        _ps_quote(APP_NAME + ".lnk"), _ps_quote(target), _ps_quote(args),
        _ps_quote(workdir), _ps_quote(icon), _ps_quote("Open the " + APP_NAME),
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                       capture_output=True, text=True, creationflags=flags)
    return r.returncode == 0


def create_shortcut_linux():
    desk = os.path.expanduser("~/Desktop")
    if not os.path.isdir(desk):
        return False
    exe = sys.executable if FROZEN else "%s %s" % (sys.executable, os.path.abspath(__file__))
    p = os.path.join(desk, APP_NAME + ".desktop")
    with open(p, "w", encoding="utf-8") as f:
        f.write("[Desktop Entry]\nType=Application\nName=%s\nExec=%s\nTerminal=true\n" % (APP_NAME, exe))
    os.chmod(p, 0o755)
    return True


def ensure_shortcut(force=False):
    marker = os.path.join(CONFIG_DIR, "shortcut_created")
    if not force and os.path.exists(marker):
        return False
    ok = False
    try:
        if os.name == "nt":
            ok = create_shortcut_windows()
        elif sys.platform.startswith("linux"):
            ok = create_shortcut_linux()
    except Exception:
        ok = False
    if ok:
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(marker, "w") as f:
                f.write(str(time.time()))
        except OSError:
            pass
        print("[+] Desktop shortcut created: %s" % APP_NAME)
    elif force:
        print("[!] Could not create the Desktop shortcut.")
    return ok


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def minimize_console():
    if os.name != "nt":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except Exception:
        pass


def main(argv=None):
    ap = argparse.ArgumentParser(description=APP_NAME + " launcher")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--replays")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--shortcut", action="store_true")
    ap.add_argument("--no-shortcut", action="store_true")
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if a.shortcut:
        ensure_shortcut(force=True)
        return 0

    if not html_path():
        print("[!] %s was not found next to the launcher." % HTML_NAME)
        input("Press Enter to exit...")
        return 1

    # Re-use an already running instance instead of starting a second one
    for p in range(a.port, a.port + 20):
        if already_running(p):
            if not a.no_browser:
                webbrowser.open("http://localhost:%d/" % p)
            print("%s is already running on port %d - opened it in your browser." % (APP_NAME, p))
            return 0

    port = next((p for p in range(a.port, a.port + 20) if port_free(p)), None)
    if port is None:
        print("[!] No free port found between %d and %d." % (a.port, a.port + 19))
        input("Press Enter to exit...")
        return 1

    Handler.replay_dir = find_replay_dir(a.replays)
    if a.replays and Handler.replay_dir:
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(os.path.join(CONFIG_DIR, "replay_dir.txt"), "w", encoding="utf-8") as f:
                f.write(Handler.replay_dir)
        except OSError:
            pass

    srv = Server(("127.0.0.1", port), Handler)
    url = "http://localhost:%d/" % port

    print("=" * 62)
    print("   %s" % APP_NAME.upper())
    print("=" * 62)
    print(" App      : %s" % url)
    print(" Replays  : %s" % (Handler.replay_dir or "not found - use 'Open Folder' in the app"))
    print(" Stop     : close this window (or press Ctrl+C)")
    print("=" * 62)

    if not a.no_shortcut:
        ensure_shortcut()

    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    if not a.no_browser:
        webbrowser.open(url)
    if FROZEN and not a.record:
        time.sleep(1.2)
        minimize_console()

    try:
        if a.record:
            try:
                import zh_recorder
                zh_recorder.main()
            except ImportError:
                print("[!] zh_recorder.py not found - recorder not started.")
                while True:
                    time.sleep(3600)
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
