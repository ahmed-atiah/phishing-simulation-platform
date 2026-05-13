#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# PDF için Türkçe destekli DejaVu font'u bul ve kopyala
mkdir -p core/fonts
DEJAVU=$(find /nix /usr /run -name "DejaVuSans.ttf" 2>/dev/null | head -1)
if [ -n "$DEJAVU" ]; then
    cp "$DEJAVU" core/fonts/DejaVuSans.ttf
    echo "DejaVu font bulundu: $DEJAVU"
else
    echo "Uyari: DejaVu font bulunamadi"
fi

cd core
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --no-input 2>/dev/null || true
