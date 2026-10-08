"""
ETS2 Radio Proxy & Real-Time Audio Transcoder
Mentranscode stream AAC dari RCS Revma (Delta FM, Female Radio, Prambors) menjadi stream MP3 murni
secara on-the-fly agar dapat diputar dengan sempurna oleh audio engine FMOD Euro Truck Simulator 2.
"""

import os
import sys
import time
import queue
import shutil
import threading
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
    # --- Radio Bahasa Inggris / Simulation Radio ---
    "/truckersfm.mp3": {
        "name": "TruckersFM",
        "url": "https://radio.truckers.fm/",
        "bitrate": "128k",
        "volume": "1dB"
    },
    "/simulatorradio.mp3": {
        "name": "Simulator Radio",
        "url": "http://radio.simulatorradio.com:8002/stream.mp3",
        "bitrate": "128k",
        "volume": "4.5dB"
    },
    "/trucksimfm.mp3": {
        "name": "TruckSimFM",
        "url": "http://radio.trucksim.fm:8000/stream",
        "bitrate": "128k",
        "volume": "2.5dB"
    },
    "/simliveradio.mp3": {
        "name": "SimLiveRadio",
        "url": "http://stream.laut.fm/simliveradio",
        "bitrate": "128k",
        "volume": "0dB"
    },
    "/greatesthits.mp3": {
        "name": "Geratest Hits Non-Stop",
        "url": "https://strw3.openstream.co/422?aw_0_1st.collectionid=7465&stationId=7465&publisherId=242&k=1772636426",
        "bitrate": "128k",
        "volume": "0dB"
    },

    # --- Radio Bahasa Indonesia ---
    "/deltafm.mp3": {
        "name": "Delta FM Jakarta",
        "url": "https://stream.rcs.revma.com/k02rmq48kxcwv",
        "bitrate": "128k",
        "volume": "1dB",
        "persistent": True
    },
    "/femaleradio.mp3": {
        "name": "FeMale Radio Jakarta",
        "url": "https://stream.rcs.revma.com/9thenqqd2ncwv",
        "bitrate": "128k",
        "volume": "5dB",
        "persistent": True
    },
    "/iradio.mp3": {
        "name": "I-Radio / I-Rock Jakarta",
        "url": "http://stream.radiojar.com/4ywdgup3bnzuv",
        "bitrate": "128k",
        "volume": "1dB"
    },
    "/kisfm.mp3": {
        "name": "KIS FM Jakarta",
        "url": "https://ic.mari.co.id:8443/kisfm",
        "bitrate": "128k",
        "volume": "4dB"
    },
    "/genfm.mp3": {
        "name": "Gen FM Jakarta",
        "url": "https://ic.mari.co.id:8443/genfm",
        "bitrate": "128k",
        "volume": "4dB"
    },
    "/sonora.mp3": {
        "name": "Sonora FM 92 Jakarta",
        "url": "https://sonora-radio.arenastreaming.com/8130/stream",
        "bitrate": "128k",
        "volume": "1.5dB"
    },
    "/vradio.mp3": {
        "name": "V Radio 106.6 FM Jakarta",
        "url": "http://8.215.206.157:8008/;",
        "bitrate": "128k",
        "volume": "3.5dB"
    },
    "/hardrock.mp3": {
        "name": "Hard Rock FM 87.6 Jakarta",
        "url": "http://stream.radiojar.com/7csmg90fuqruv",
        "bitrate": "128k",
        "volume": "0.5dB"
    },
    "/prambors.mp3": {
        "name": "Prambors FM Jakarta",
        "url": "https://stream.rcs.revma.com/h77wwp48kxcwv",
        "bitrate": "128k",
        "volume": "2.5dB",
        "persistent": True
    },
    "/aberadio.mp3": {
        "name": "Abe Radio Online - Jazz",
        "url": "https://stream.zeno.fm/hslkouvwisovv",
        "bitrate": "128k",
        "volume": "4.5dB"
    },
    "/deltabandung.mp3": {
        "name": "Delta FM Bandung (Direct Icecast)",
        "url": "https://stream-pd-bdg.dimasalfaridzi.my.id/delta",
        "bitrate": "128k",
        "volume": "0dB"
    },

    # --- Radio Bahasa Jepang ---
    "/j1hits.mp3": {
        "name": "J1 HITS Tokyo",
        "url": "https://jenny.torontocast.com:2000/stream/J1HITS",
        "bitrate": "128k",
        "volume": "4.5dB"
    },
    "/onlyhits.mp3": {
        "name": "OnlyHits Japan",
        "url": "https://cdn.onlyhitsradio.net/japan",
        "bitrate": "128k",
        "volume": "11dB"
    },
    "/japanhits.mp3": {
        "name": "Japan Hits - asia DREAM radio",
        "url": "http://quincy.torontocast.com:2020/stream.mp3",
        "bitrate": "128k",
        "volume": "3.5dB"
    },
    "/jrock.mp3": {
        "name": "J-Rock Powerplay",
        "url": "https://kathy.torontocast.com:3340/;",
        "bitrate": "128k",
        "volume": "8dB"
    },
    "/listenmoe.mp3": {
        "name": "LISTEN.moe J-Pop",
        "url": "https://listen.moe/fallback",
        "bitrate": "192k",
        "volume": "0dB"
    },
    "/jpop.mp3": {
        "name": "J-Pop Powerplay",
        "url": "https://kathy.torontocast.com:3560/;",
        "bitrate": "128k",
        "volume": "2dB"
    },
    "/jpopkawaii.mp3": {
        "name": "J-Pop Powerplay Kawaii",
        "url": "https://kathy.torontocast.com:3060/;",
        "bitrate": "128k",
        "volume": "4dB"
    },
    "/sakura.mp3": {
        "name": "J-Pop Sakura",
        "url": "http://quincy.torontocast.com:2070/stream.mp3",
        "bitrate": "128k",
        "volume": "14dB"
    },
    "/stereoanime.mp3": {
        "name": "Stereo Anime",
        "url": "https://radio.stereoanime.com/listen/stereoanime/128",
        "bitrate": "128k",
        "volume": "2dB"
    },
    "/waveanime.mp3": {
        "name": "Wave Anime Radio",
        "url": "https://channel_1.waveani.fun/stream",
        "bitrate": "192k",
        "volume": "0.5dB"
    },
    "/animefm.mp3": {
        "name": "Anime FM",
        "url": "https://animefm.stream.laut.fm/animefm",
        "bitrate": "128k",
        "volume": "4dB"
    },
    "/justplay.mp3": {
        "name": "Justplay Anime & J-Pop",
        "url": "https://justplay.stream.laut.fm/justplay",
        "bitrate": "128k",
        "volume": "3.5dB"
    },
    "/kibofm.mp3": {
        "name": "Kibo.FM",
        "url": "http://listen.kibo.fm:8000/kibofm",
        "bitrate": "192k",
        "volume": "14dB"
    },
    "/otakuworld.mp3": {
        "name": "Otaku World",
        "url": "https://otaku-world.stream.laut.fm/otaku-world",
        "bitrate": "128k",
        "volume": "1dB"
    },
    "/citypop.mp3": {
        "name": "BOX - Japan City Pop",
        "url": "https://play.streamafrica.net/japancitypop",
        "bitrate": "128k",
        "volume": "6dB"
    },
    "/freefmtokyo.mp3": {
        "name": "Free FM Tokyo",
        "url": "https://rocafmadrid.radioca.st/stream",
        "bitrate": "128k",
        "volume": "2dB"
    },
    "/bigbradio.mp3": {
        "name": "Big B Radio - JPOP",
        "url": "http://pureplay.cdnstream1.com/6027_128.mp3",
        "bitrate": "128k",
        "volume": "1.5dB"
    },
    "/j1gold.mp3": {
        "name": "J1 GOLD Tokyo",
        "url": "https://jenny.torontocast.com:2000/stream/J1GOLD",
        "bitrate": "128k",
        "volume": "7dB"
    },
    "/fmsetagaya.mp3": {
        "name": "FM Setagaya 83.4",
        "url": "https://fmsetagaya834.out.airtime.pro/fmsetagaya834_a",
        "bitrate": "128k",
        "volume": "12dB"
    },
    "/shonanbeach.mp3": {
        "name": "Shonan Beach FM 78.9",
        "url": "http://shonanbeachfm.out.airtime.pro:8000/shonanbeachfm_a",
        "bitrate": "128k",
        "volume": "6.5dB"
    },
    "/mikuradio.mp3": {
        "name": "Miku Radio",
        "url": "https://miku.fm/listen/miku/mp3-320",
        "bitrate": "128k",
        "volume": "6.5dB"
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


class StreamBroadcaster:
    """
    Persistent Live Stream Broadcaster.
    Menjaga koneksi upstream ke server CDN (seperti RCS Revma) tetap terbuka di background
    sehingga jeda iklan pre-roll (DAI) hanya terjadi sekali di awal saat proxy start,
    dan pemain di ETS2 dapat berpindah-pindah radio secara instan tanpa jeda iklan/kaset ke-reset.
    """
    def __init__(self, name, url, bitrate="128k", volume=None):
        self.name = name
        self.url = url
        self.bitrate = bitrate
        self.volume = volume
        self.clients = set()
        self.lock = threading.Lock()
        self.running = True
        self.proc = None
        self.recent_chunks = []
        self.max_recent = 4  # Buffer ~16KB untuk instant start FMOD di game
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            print(f"[*] Menghubungkan persistent live relay: {self.name}...")
            cmd = [
                FFMPEG_BIN,
                "-hide_banner",
                "-loglevel", "error",
                "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
                "-i", self.url,
                "-vn",
            ]
            vol_boost = self.volume if self.volume else "0dB"
            cmd.extend(["-af", f"volume={vol_boost},alimiter=limit=0.95"])
            cmd.extend([
                "-c:a", "libmp3lame",
                "-b:a", self.bitrate,
                "-ar", "44100",
                "-ac", "2",
                "-f", "mp3",
                "pipe:1"
            ])

            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW

            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=10**6,
                    creationflags=flags
                )

                while self.running and self.proc.poll() is None:
                    chunk = self.proc.stdout.read(4096)
                    if not chunk:
                        break

                    with self.lock:
                        self.recent_chunks.append(chunk)
                        if len(self.recent_chunks) > self.max_recent:
                            self.recent_chunks.pop(0)

                        for q in list(self.clients):
                            try:
                                q.put_nowait(chunk)
                            except queue.Full:
                                try:
                                    q.get_nowait()
                                    q.put_nowait(chunk)
                                except Exception:
                                    pass
            except Exception as e:
                print(f"[!] Upstream error pada {self.name}: {e}")
            finally:
                if self.proc:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass

            if self.running:
                print(f"[!] Upstream terputus untuk {self.name}. Reconnecting dalam 3 detik...")
                time.sleep(3)

    def add_client(self):
        q = queue.Queue(maxsize=150)
        with self.lock:
            for c in self.recent_chunks:
                try:
                    q.put_nowait(c)
                except Exception:
                    pass
            self.clients.add(q)
        return q

    def remove_client(self, q):
        with self.lock:
            self.clients.discard(q)

    def stop(self):
        self.running = False
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass


BROADCASTERS = {}
BROADCASTERS_LOCK = threading.Lock()

def get_broadcaster(path, station_info):
    with BROADCASTERS_LOCK:
        if path not in BROADCASTERS:
            b = StreamBroadcaster(
                name=station_info["name"],
                url=station_info["url"],
                bitrate=station_info.get("bitrate", "128k"),
                volume=station_info.get("volume")
            )
            BROADCASTERS[path] = b
        return BROADCASTERS[path]

def start_persistent_relays():
    for path, info in STREAMS.items():
        if info.get("persistent"):
            get_broadcaster(path, info)


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

        # Jika stasiun menggunakan persistent relay (bebas iklan pre-roll & instant switch)
        if station.get("persistent"):
            broadcaster = get_broadcaster(path, station)
            q = broadcaster.add_client()
            print(f"[*] Client terhubung ke live persistent relay: {station['name']}")
            try:
                while True:
                    try:
                        chunk = q.get(timeout=5)
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except queue.Empty:
                        continue
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            except Exception as e:
                print(f"[!] Error saat streaming persistent relay: {e}")
            finally:
                broadcaster.remove_client(q)
                print(f"[-] Client terputus dari: {station['name']} (relay tetap aktif di background).")
            return

        print(f"[*] Client terhubung ke (on-demand): {station['name']} ({station['url']})")

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
        ]

        vol_boost = station.get("volume", "0dB")
        # Boost volume terkalibrasi dan pasang brickwall audio limiter agar tidak digital clipping/pecah
        cmd.extend(["-af", f"volume={vol_boost},alimiter=limit=0.95"])

        cmd.extend([
            "-c:a", "libmp3lame",
            "-b:a", station.get("bitrate", "128k"),
            "-ar", "44100",
            "-ac", "2",
            "-f", "mp3",
            "pipe:1"
        ])

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
    start_persistent_relays()
    return HTTP_SERVER

def stop_server():
    global HTTP_SERVER, BROADCASTERS
    with BROADCASTERS_LOCK:
        for b in list(BROADCASTERS.values()):
            b.stop()
        BROADCASTERS.clear()
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
