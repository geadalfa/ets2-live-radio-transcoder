# 🚛 ETS2 Live Radio Transcoder & System Tray Controller

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-5.0+-007808?style=flat&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Euro Truck Simulator 2](https://img.shields.io/badge/Compatibility-ETS2%20%7C%20ATS-E66E14?style=flat)](https://eurotrucksimulator2.com/)
[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=flat&logo=windows&logoColor=white)](https://microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, real-time audio proxy and transcoder with a native **Windows System Tray** controller for **Euro Truck Simulator 2 (ETS2)** and **American Truck Simulator (ATS)**. 

Bypasses SCS Software FMOD audio engine limitations, enabling playback of modern **AAC, AAC+, HE-AAC, HLS, and SSL-restricted streams** (e.g., Masima Network, MARI, TorontoCast, Cloudflare-protected CDNs) directly in your truck's in-game radio.

---

## 🇬🇧 English Documentation

### 🔍 Background & The Problem

Euro Truck Simulator 2 and American Truck Simulator utilize the **FMOD Studio** sound engine to power in-game radio playback (`live_streams.sii`). FMOD enforces strict streaming constraints:
- **Only MP3 (`audio/mpeg`) and OGG Vorbis (`audio/ogg`)** codecs are natively supported (`uset g_stream_exts ".ogg;.mp3"`).
- Modern AAC / AAC+ / HE-AAC streams (used by almost all modern commercial radio stations worldwide) fail to decode and stay silent.
- FMOD drops connections to non-standard HTTPS ports (such as `:2000`), throwing `<ERROR> [fmod] (21) A HTTP error occurred`.
- Cloudflare and modern CDN edges drop requests from FMOD's raw netstream client due to missing User-Agent headers.

### 💡 The Solution

**ETS2 Live Radio Transcoder** runs locally on `127.0.0.1:8000`. 
When you tune into a transcoded radio station in ETS2, the proxy:
1. Spawns an on-demand FFmpeg pipeline that fetches the live AAC/Icecast/HTTPS source stream with full TLS 1.3 and browser User-Agent support.
2. Transcodes the audio into pristine **MP3** (`audio/mpeg`) on-the-fly with near-zero latency.
3. Streams the chunks directly into ETS2's local socket.
4. **0% Idle CPU:** When you turn off the radio or switch stations in-game, the transcoder automatically kills the child process instantly.

---

### ✨ Features
- **Native Windows System Tray App:** Runs quietly in the notification area (next to your taskbar clock and Steam).
- **1-Click Launch & Exit:** Right-click tray icon to Open Status Web Dashboard, Restart Server, or Cleanly Exit (just like Steam).
- **Zero Window Footprint:** Runs windowless with `pythonw.exe` without distracting command prompt popups.
- **Pre-Configured Station Catalog:**
  - **Indonesia:** Delta FM, FeMale Radio, Prambors FM, Gen FM, KIS FM, I-Radio, Hard Rock FM, Sonora FM 92, V Radio 106.6, Abe Radio Jazz.
  - **Japan & Anime:** J1 HITS Tokyo, OnlyHits Japan (YOASOBI, Official HIGE DANDISM, Ado), J-Rock Powerplay, LISTEN.moe, Wave Anime Radio, Stereo Anime, BOX Japan City Pop, Free FM 80 Tokyo, FM Setagaya 83.4, Miku Radio.
  - **Sim Radios:** TruckersFM, Simulator Radio, TruckSimFM, SimLiveRadio, Greatest Hits Non-Stop.

---

### 📦 Prerequisites & Installation

#### 1. Install FFmpeg
The transcoder requires FFmpeg in your system PATH. On Windows 10/11, install via Windows Package Manager (WinGet):
```powershell
winget install Gyan.FFmpeg
```

#### 2. Clone the Repository & Install Dependencies
```bash
git clone https://github.com/geadalfa/ets2-live-radio-transcoder.git
cd ets2-live-radio-transcoder
pip install -r requirements.txt
```

---

### 🚀 Usage

#### Option A: Single-Click System Tray App (Recommended)
Run the tray controller:
```powershell
pythonw ets2_radio_tray.py
```
- A radio icon will appear in your Windows System Tray.
- Right-click the icon to open the web dashboard or exit the application.
- To make a Desktop Shortcut, right-click `ets2_radio_tray.py` -> *Send to* -> *Desktop (create shortcut)*, and set its target to `pythonw.exe`.

#### Option B: Standalone CLI
```powershell
python ets2_radio_proxy.py
```

---

### 🛠️ Tutorial: How to Add Your Own Favorite Radio Stations

Adding any station—regardless of codec—takes just 2 simple steps:

#### Step 1: Add the Stream to `ets2_radio_proxy.py`
Open `ets2_radio_proxy.py` in any text editor. Locate the `STREAMS` dictionary and add your station:
```python
STREAMS = {
    # Existing stations...
    
    "/myradio.mp3": {
        "name": "My Favorite Radio",
        "url": "https://stream.example.com/live.aac",   # Direct source stream URL (AAC, AAC+, MP3, etc.)
        "bitrate": "128k"                               # Output MP3 bitrate (128k, 192k, 256k, 320k)
    }
}
```

#### Step 2: Register the Station in ETS2's `live_streams.sii`
Open your ETS2 radio config file:
`Documents\Euro Truck Simulator 2\live_streams.sii`

1. Increase the count at line 4:
   ```text
   stream_data: <N+1>
   ```
2. Add your new stream entry:
   ```text
   stream_data[<index>]: "http://127.0.0.1:8000/myradio.mp3|My Favorite Radio|Pop, Hits|EN|128|1"
   ```
   *Format explanation:*
   - `http://127.0.0.1:8000/myradio.mp3` = The local proxy endpoint matching what you defined in Step 1.
   - `My Favorite Radio` = Station display name in ETS2 radio menu.
   - `Pop, Hits` = Genre.
   - `EN` / `ID` / `JP` = Language tag.
   - `128` = Bitrate display.
   - `1` = Favorite flag (`1` for favorited, `0` for normal).

Save the file, launch Euro Truck Simulator 2, open your in-game Radio (`R` key), and enjoy!

---
---

## 🇮🇩 Panduan Bahasa Indonesia

### 🔍 Latar Belakang & Masalah

Game **Euro Truck Simulator 2 (ETS2)** dan **American Truck Simulator (ATS)** menggunakan engine audio **FMOD Studio** untuk memutar radio siaran langsung di dalam kabin truk (`live_streams.sii`). FMOD memiliki batasan teknis:
- **Hanya mendukung codec MP3 (`audio/mpeg`) dan OGG Vorbis (`audio/ogg`)**.
- Stasiun radio modern di Indonesia dan dunia saat ini menggunakan format streaming **AAC, AAC+, atau HE-AAC** (seperti grup Masima: Delta FM, FeMale Radio, Prambors; dan grup MARI: Gen FM, KIS FM). Format ini **tidak didukung oleh FMOD** sehingga radio akan hening atau langsung mati saat dipilih.
- Stasiun radio dengan port SSL non-standar (misalnya `:2000` seperti J1 HITS) atau proteksi Cloudflare akan mengalami error `<ERROR> [fmod] (21) A HTTP error occurred`.

### 💡 Solusi: ETS2 Live Radio Transcoder

Aplikasi ini berjalan sebagai server perantara (proxy) lokal di komputer kamu pada alamat `127.0.0.1:8000`. 
Saat kamu memilih radio di game:
1. Proxy lokal memanggil FFmpeg secara otomatis di background untuk mengambil audio sumber resmi (AAC/AAC+/SSL).
2. Audio langsung di-transcode secara real-time menjadi format **MP3 murni** tanpa jeda (zero latency).
3. Audio MP3 disuapkan ke engine game ETS2.
4. **0% Beban CPU Saat Diam:** Begitu radio dimatikan di game atau kamu ganti stasiun, proses FFmpeg langsung otomatis dimatikan seketika.

---

### ✨ Fitur Unggulan
- **Aplikasi System Tray Windows (Mirip Steam):** Berjalan di latar belakang tanpa jendela command prompt hitam yang mengganggu. Ikon radio muncul di pojok kanan bawah taskbar.
- **1 Tombol Start & Exit:** Cukup double-click untuk mulai. Klik kanan ikon di tray untuk membuka dashboard status atau keluar (*Exit*) secara bersih.
- **Daftar Stasiun Populer Siap Pakai:**
  - **Indonesia:** Delta FM, FeMale Radio, Prambors FM, Gen FM, KIS FM, I-Radio Jakarta, Hard Rock FM, Sonora FM 92, V Radio 106.6, Abe Radio Jazz.
  - **Jepang & Anime:** J1 HITS Tokyo, OnlyHits Japan (YOASOBI, Official HIGE DANDISM, Ado), J-Rock Powerplay, LISTEN.moe, Wave Anime Radio, Stereo Anime, BOX Japan City Pop, Free FM 80 Tokyo, FM Setagaya 83.4, Miku Radio.
  - **Simulator:** TruckersFM, Simulator Radio, TruckSimFM, SimLiveRadio, Greatest Hits Non-Stop.

---

### 📦 Persyaratan & Instalasi

#### 1. Pasang FFmpeg
Aplikasi ini membutuhkan FFmpeg. Di Windows 10/11, kamu bisa pasang dengan mudah via PowerShell:
```powershell
winget install Gyan.FFmpeg
```

#### 2. Unduh Repositori & Pasang Paket Python
```bash
git clone https://github.com/geadalfa/ets2-live-radio-transcoder.git
cd ets2-live-radio-transcoder
pip install -r requirements.txt
```

---

### 🚀 Cara Menjalankan

#### Cara A: Aplikasi System Tray (Direkomendasikan)
Jalankan file controller tray:
```powershell
pythonw ets2_radio_tray.py
```
- Ikon radio akan langsung muncul di System Tray Windows (dekat jam).
- Klik kanan ikon tray untuk membuka status atau keluar (*Tutup / Exit*).

#### Cara B: Terminal Biasa
```powershell
python ets2_radio_proxy.py
```

---

### 🛠️ Tutorial: Cara Menambahkan Stasiun Radio Favorit Sendiri

Ingin menambahkan radio favorit kamu yang belum ada di daftar? Cukup 2 langkah mudah:

#### Langkah 1: Daftarkan URL Streaming di `ets2_radio_proxy.py`
Buka file `ets2_radio_proxy.py` dengan text editor (Notepad, VS Code, dll). Cari bagian `STREAMS` dan tambahkan stasiun baru:
```python
STREAMS = {
    # Stasiun yang sudah ada...
    
    "/radiorock.mp3": {
        "name": "Radio Rock Indonesia",
        "url": "https://stream.server.com/live.aac",   # URL stream asli (format apa saja: AAC, AAC+, dsb.)
        "bitrate": "128k"                              # Kualitas bitrate MP3 output
    }
}
```

#### Langkah 2: Daftarkan ke `live_streams.sii` di Game ETS2
Buka file konfigurasi radio ETS2 kamu di:
`Documents\Euro Truck Simulator 2\live_streams.sii`

1. Tambahkan jumlah stasiun di baris ke-4:
   ```text
   stream_data: <total_stasiun_baru>
   ```
2. Tambahkan baris baru sesuai nomor urut indeks:
   ```text
   stream_data[<nomor_indeks>]: "http://127.0.0.1:8000/radiorock.mp3|Radio Rock Indonesia|Rock, Hits|ID|128|1"
   ```
   *Arti format tanda pipa (`|`):*
   - `http://127.0.0.1:8000/radiorock.mp3` = Alamat lokal proxy yang kamu buat di Langkah 1.
   - `Radio Rock Indonesia` = Nama stasiun yang tampil di layar radio game.
   - `Rock, Hits` = Kategori genre.
   - `ID` = Bahasa / Negara.
   - `128` = Tampilan bitrate di game.
   - `1` = Status favorit (`1` = Bintang favorit, `0` = Biasa).

Simpan file `live_streams.sii`, buka Euro Truck Simulator 2, masuk ke truk, tekan tombol **R** (Radio), dan stasiun favoritmu siap dinikmati di perjalanan!

---

## 📄 License
Project ini dilisensikan di bawah [MIT License](LICENSE).
Dikembangkan oleh [Geadalfa Giyanda](https://github.com/geadalfa) & asisten AI **Gemi**.
