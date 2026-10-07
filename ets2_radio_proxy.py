"""
ETS2 Radio Proxy & Real-Time Audio Transcoder
Mentranscode stream AAC dari RCS Revma (Delta FM, Female Radio, Prambors) menjadi stream MP3 murni
secara on-the-fly agar dapat diputar dengan sempurna oleh audio engine FMOD Euro Truck Simulator 2.
"""

import os
import sys
import shutil
import subprocess
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler

# Penanganan output stream jika dijalankan via pythonw.exe (windowless mode)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "proxy.log")

if sys.stdout is None:
    try:
        sys.stdout = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    except Exception:
        sys.stdout = open(os.devnull, "w")

if sys.stderr is None:
    try:
        sys.stderr = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    except Exception:
        sys.stderr = open(os.devnull, "w")

PORT = 8000

# Pemetaan stasiun radio ke URL stream sumber resmi (AAC)
STREAMS = {
    "/deltafm.mp3": {
        "name": "Delta FM Jakarta",
        "url": "https://stream.rcs.revma.com/k02rmq48kxcwv",
        "bitrate": "128k"
    },
    "/femaleradio.mp3": {
        "name": "FeMale Radio Jakarta",
        "url": "https://stream.rcs.revma.com/9thenqqd2ncwv",
        "bitrate": "128k"
    },
    "/prambors.mp3": {
        "name": "Prambors FM Jakarta",
        "url": "https://stream.rcs.revma.com/h77wwp48kxcwv",
        "bitrate": "128k"
    },
    "/genfm.mp3": {
        "name": "Gen FM Jakarta",
        "url": "https://ic.mari.co.id:8443/genfm",
        "bitrate": "128k"
    },
    "/kisfm.mp3": {
        "name": "KIS FM Jakarta",
        "url": "https://ic.mari.co.id:8443/kisfm",
        "bitrate": "128k"
    },
    "/aberadio.mp3": {
        "name": "Abe Radio Online - Jazz",
        "url": "https://stream.zeno.fm/hslkouvwisovv",
        "bitrate": "128k"
    },
    "/waveanime.mp3": {
        "name": "Wave Anime Radio",
        "url": "https://channel_1.waveani.fun/stream",
        "bitrate": "192k"
    },
    "/j1hits.mp3": {
        "name": "J1 HITS Tokyo",
        "url": "https://jenny.torontocast.com:2000/stream/J1HITS",
        "bitrate": "128k"
    },
    "/j1gold.mp3": {
        "name": "J1 GOLD Tokyo",
        "url": "https://jenny.torontocast.com:2000/stream/J1GOLD",
        "bitrate": "128k"
    },
    "/onlyhits.mp3": {
        "name": "OnlyHits Japan",
        "url": "https://cdn.onlyhitsradio.net/japan",
        "bitrate": "128k"
    },
    "/listenmoe.mp3": {
        "name": "LISTEN.moe J-Pop",
        "url": "https://listen.moe/fallback",
        "bitrate": "192k"
    },
    "/citypop.mp3": {
        "name": "BOX - Japan City Pop",
        "url": "https://play.streamafrica.net/japancitypop",
        "bitrate": "128k"
    },
    "/fmsetagaya.mp3": {
        "name": "FM Setagaya 83.4",
        "url": "https://fmsetagaya834.out.airtime.pro/fmsetagaya834_a",
        "bitrate": "128k"
    },
    "/jrock.mp3": {
        "name": "J-Rock Powerplay",
        "url": "https://kathy.torontocast.com:3340/;",
        "bitrate": "128k"
    },
    "/sakura.mp3": {
        "name": "J-Pop Sakura",
        "url": "http://quincy.torontocast.com:2070/stream.mp3",
        "bitrate": "128k"
    }
}

def get_ffmpeg_path():
    # 1. Cek dari PATH
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg

    # 2. Cek lokasi default winget / localappdata
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local_app_data, "Microsoft", "WinGet", "Links", "ffmpeg.exe"),
        r"C:\Users\Alfa\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    # 3. Cari di folder WinGet Packages jika link belum terbuat
    pkg_dir = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages")
    if os.path.isdir(pkg_dir):
        for root, dirs, files in os.walk(pkg_dir):
            if "ffmpeg.exe" in files:
                return os.path.join(root, "ffmpeg.exe")

    return "ffmpeg"


FFMPEG_BIN = get_ffmpeg_path()


class RadioProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if sys.stdout and not sys.stdout.closed:
            try:
                sys.stdout.write(f"[{self.log_date_time_string()}] {args[0]} - {args[1]} - {args[2]}\n")
                sys.stdout.flush()
            except Exception:
                pass

    def do_HEAD(self):
        path = self.path.split("?")[0]
        if path in STREAMS:
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Accept-Ranges", "none")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("icy-name", STREAMS[path]["name"])
            self.send_header("icy-br", "128")
            self.end_headers()
        else:
            self.send_error(404, "Station not found")

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/health", "/status"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = f"""
            <html>
            <head><title>ETS2 Radio Transcoder Proxy</title></head>
            <body style="font-family: sans-serif; padding: 20px; line-height: 1.6;">
                <h2>ETS2 Radio Transcoder Proxy (Active)</h2>
                <p>Status: <b>Online</b> | FFmpeg: <code>{FFMPEG_BIN}</code></p>
                <h3>Available Streams (MP3 Transcoded):</h3>
                <ul>
            """
            for endpoint, info in STREAMS.items():
                html += f'<li><a href="{endpoint}">{info["name"]}</a> - <code>http://127.0.0.1:{PORT}{endpoint}</code></li>'
            html += """
                </ul>
                <p style="color: green;">Radio streams siap diputar oleh Euro Truck Simulator 2.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
            return

        if path not in STREAMS:
            self.send_error(404, "Stream not found")
            return

        station = STREAMS[path]
        print(f"[*] Client terhubung ke: {station['name']} ({station['url']})")

        # Kirim header HTTP audio/mpeg (MP3)
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Accept-Ranges", "none")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Connection", "close")
        self.send_header("icy-name", station["name"])
        self.send_header("icy-br", "128")
        self.end_headers()

        # Jalankan FFmpeg untuk transcode AAC ke MP3 secara real-time via stdout pipe
        cmd = [
            FFMPEG_BIN,
            "-hide_banner",
            "-loglevel", "error",
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "-reconnect", "1",
            "-reconnect_at_eof", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", station["url"],
            "-vn",
            "-c:a", "libmp3lame",
            "-b:a", station.get("bitrate", "128k"),
            "-ar", "44100",
            "-ac", "2",
            "-f", "mp3",
            "pipe:1"
        ]

        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NO_WINDOW

        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**6,
                creationflags=flags
            )

            # Stream chunks langsung ke socket game
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Normal: Pemain mematikan radio atau mengganti stasiun di dalam game
            pass
        except Exception as e:
            print(f"[!] Error saat streaming: {e}")
        finally:
            if proc:
                try:
                    proc.kill()
                    proc.wait(timeout=1)
                except Exception:
                    pass
            print(f"[-] Client terputus dari: {station['name']}. Transcoder dihentikan.")


HTTP_SERVER = None

def create_server(port=PORT):
    global HTTP_SERVER
    HTTP_SERVER = ThreadingHTTPServer(("127.0.0.1", port), RadioProxyHandler)
    return HTTP_SERVER

def stop_server():
    global HTTP_SERVER
    if HTTP_SERVER:
        try:
            HTTP_SERVER.shutdown()
            HTTP_SERVER.server_close()
        except Exception:
            pass
        HTTP_SERVER = None

def main():
    print("=" * 60)
    print("   ETS2 Radio Transcoder Proxy (AAC -> MP3)")
    print(f"   Listening on: http://127.0.0.1:{PORT}")
    print(f"   Using FFmpeg: {FFMPEG_BIN}")
    print("=" * 60)
    for endpoint, info in STREAMS.items():
        print(f" - {info['name']}: http://127.0.0.1:{PORT}{endpoint}")
    print("=" * 60)
    print("Tekan Ctrl+C untuk menghentikan server.")

    server = create_server(PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Menghentikan proxy server...")
    finally:
        stop_server()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        if sys.stderr and not sys.stderr.closed:
            sys.stderr.flush()
