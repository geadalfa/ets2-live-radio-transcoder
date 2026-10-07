"""
ETS2 Radio Transcoder - Windows System Tray Application
Menjalankan local transcoder proxy di background dengan ikon System Tray di taskbar (seperti Steam).
Klik kanan pada ikon di tray untuk membuka menu atau menutup aplikasi secara bersih.
"""

import os
import sys
import webbrowser
import threading
import subprocess
from http.server import ThreadingHTTPServer

# Pastikan working directory ke folder script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# Import modul proxy
import ets2_radio_proxy
from ets2_radio_proxy import PORT, RadioProxyHandler, STREAMS

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication

class ProxyServerThread(threading.Thread):
    def __init__(self, port=PORT):
        super().__init__(daemon=True)
        self.port = port
        self.server = None
        self._is_running = False

    def run(self):
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", self.port), RadioProxyHandler)
            ets2_radio_proxy.HTTP_SERVER = self.server
            self._is_running = True
            self.server.serve_forever()
        except Exception as e:
            print(f"[!] Server error: {e}")
        finally:
            self._is_running = False

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
            ets2_radio_proxy.HTTP_SERVER = None
            self._is_running = False


class RadioTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Setup icon
        icon_path = os.path.join(SCRIPT_DIR, "radio_tray_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(SCRIPT_DIR, "radio_tray_icon.png")

        self.icon = QIcon(icon_path)
        self.app.setWindowIcon(self.icon)

        # Inisialisasi System Tray Icon
        self.tray = QSystemTrayIcon(self.icon, self.app)
        self.tray.setToolTip(f"ETS2 Radio Transcoder (Port {PORT}) - Aktif")

        # Buat Menu Konteks (Right Click)
        self.menu = QMenu()

        # 1. Header Judul
        title_action = QAction("📻 ETS2 Radio Transcoder", self.menu)
        title_font = QFont()
        title_font.setBold(True)
        title_action.setFont(title_font)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)

        # Status text
        status_action = QAction(f"● Status: Online (127.0.0.1:{PORT})", self.menu)
        status_action.setEnabled(False)
        self.menu.addAction(status_action)

        self.menu.addSeparator()

        # 2. Buka Dashboard Web
        web_action = QAction("🌐 Buka Dashboard Status (Browser)", self.menu)
        web_action.triggered.connect(self.open_dashboard)
        self.menu.addAction(web_action)

        # 3. Buka Folder Config
        folder_action = QAction("📂 Buka Folder Radio ETS2", self.menu)
        folder_action.triggered.connect(self.open_folder)
        self.menu.addAction(folder_action)

        self.menu.addSeparator()

        # 4. Restart Server
        restart_action = QAction("🔄 Restart Server Transcoder", self.menu)
        restart_action.triggered.connect(self.restart_server)
        self.menu.addAction(restart_action)

        self.menu.addSeparator()

        # 5. Keluar / Exit
        exit_action = QAction("❌ Tutup / Exit Radio ETS2", self.menu)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)

        # Jalankan HTTP Proxy Server di background thread
        self.server_thread = None
        self.start_server()

        # Tampilkan Tray Icon
        self.tray.show()

        # Kirim notifikasi toast pertama kali
        self.tray.showMessage(
            "ETS2 Radio Transcoder",
            f"Transcoder aktif di background (Port {PORT}).\nSiap memutar Delta FM, Female, KIS, Prambors, J1 Hits, dll!",
            QSystemTrayIcon.Information,
            3500
        )

    def start_server(self):
        if self.server_thread and self.server_thread._is_running:
            return
        self.server_thread = ProxyServerThread(PORT)
        self.server_thread.start()

    def restart_server(self):
        if self.server_thread:
            self.server_thread.stop()
        self.kill_ffmpeg()
        self.start_server()
        self.tray.showMessage(
            "ETS2 Radio Transcoder",
            "Server proxy berhasil di-restart!",
            QSystemTrayIcon.Information,
            2000
        )

    def open_dashboard(self):
        webbrowser.open(f"http://127.0.0.1:{PORT}/health")

    def open_folder(self):
        os.startfile(SCRIPT_DIR)

    def on_tray_activated(self, reason):
        # Double click membuka browser dashboard
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_dashboard()

    def kill_ffmpeg(self):
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/f", "/im", "ffmpeg.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        except Exception:
            pass

    def exit_app(self):
        print("[*] Menghentikan ETS2 Radio Tray App...")
        # 1. Hentikan HTTP server thread
        if self.server_thread:
            self.server_thread.stop()

        # 2. Hentikan child FFmpeg processes
        self.kill_ffmpeg()

        # 3. Sembunyikan tray icon agar langsung hilang dari taskbar
        self.tray.hide()

        # 4. Quit Qt Application
        QCoreApplication.quit()
        sys.exit(0)

    def run(self):
        return self.app.exec_()


if __name__ == "__main__":
    app = RadioTrayApp()
    sys.exit(app.run())
