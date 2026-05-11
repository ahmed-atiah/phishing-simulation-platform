@echo off
chcp 65001 >nul
title Cyber Aware — ngrok Tunnel

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         Cyber Aware — ngrok Modu         ║
echo  ╚══════════════════════════════════════════╝
echo.

REM --- Django sunucusunu arka planda başlat
echo  [1/2] Django sunucusu başlatılıyor...
start "Django" cmd /k "cd /d %~dp0core && ..\venv\Scripts\python.exe manage.py runserver 8000"

timeout /t 3 /nobreak >nul

REM --- ngrok'u başlat
echo  [2/2] ngrok tüneli açılıyor...
echo.
echo  ngrok çalışınca çıkan https://xxxx.ngrok-free.app linkini kopyala
echo  Sonra core\.env dosyasında BASE_TRACKING_URL satırını güncelle:
echo.
echo    BASE_TRACKING_URL=https://xxxx.ngrok-free.app/track/
echo.
echo  (xxxx yerine ngrok'un verdiği kodu yaz)
echo.
echo  DAHA SONRA Django'yu yeniden başlatmayı unutma!
echo.
ngrok http 8000

pause
