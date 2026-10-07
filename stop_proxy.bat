@echo off
title Hentikan ETS2 Radio Proxy
echo Menghentikan proses proxy dan transcode...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*ets2_radio_proxy.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
taskkill /f /im ffmpeg.exe 2>nul
echo ETS2 Radio Proxy telah dihentikan.
ping 127.0.0.1 -n 2 >nul
