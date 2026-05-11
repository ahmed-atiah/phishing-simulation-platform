@echo off
title Cyber Aware
color 0A

:: Bat dosyasinin bulundugu klasore git (cift tiklamada bile calisir)
pushd "%~dp0"

echo.
echo  +------------------------------------------+
echo  ^|       Cyber Aware - Guvenik Platformu    ^|
echo  +------------------------------------------+
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo  [HATA] Python bulunamadi. https://python.org adresinden yukleyin.
    pause
    exit /b
)

:: Virtual environment kontrolu
if not exist "venv\" (
    echo  [1/4] Sanal ortam olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo  [HATA] venv olusturulamadi.
        pause
        exit /b
    )
)

:: Sanal ortami aktif et
call venv\Scripts\activate.bat

:: Paket kurulumu
echo  [2/4] Paketler kontrol ediliyor...
pip install -r requirements.txt --quiet --no-warn-script-location
if errorlevel 1 (
    echo  [HATA] Paket kurulumu basarisiz oldu.
    pause
    exit /b
)

:: core klasorune gec (manage.py burada)
pushd core
if errorlevel 1 (
    echo  [HATA] core klasoru bulunamadi.
    pause
    exit /b
)

:: Veritabani migration
echo  [3/4] Veritabani guncelleniyor...
python manage.py migrate >nul 2>&1

:: Superuser var mi kontrol et
python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ------------------------------------------
    echo   Ilk kurulum - yonetici hesabi olusturun
    echo  ------------------------------------------
    python manage.py createsuperuser
)

:: Sunucuyu baslat
echo  [4/4] Sunucu baslatiliyor...
echo.
echo  +------------------------------------------+
echo  ^|  Cyber Aware calisiyor                    ^|
echo  ^|                                          ^|
echo  ^|  Adres : http://127.0.0.1:8000           ^|
echo  ^|  Panel  : http://127.0.0.1:8000/login    ^|
echo  ^|                                          ^|
echo  ^|  Durdurmak icin: Ctrl + C                ^|
echo  +------------------------------------------+
echo.

:: Tarayiciyi 3 saniye sonra ac
start /b "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

python manage.py runserver 127.0.0.1:8000

popd
popd
pause
