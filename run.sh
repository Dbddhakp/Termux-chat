#!/usr/bin/env bash
set -e

cd ~/termux-chat

# 1) Virtualenv aktivieren
if [ -f venv/bin/activate ]; then
  source venv/bin/activate
else
  echo "ERROR: Virtualenv nicht gefunden. Bitte erst Script von vorher ausführen."
  exit 1
fi

# 2) Mit pip alle Abhängigkeiten installieren
pip install --upgrade pip
pip install flask flask-login flask-sqlalchemy flask-socketio eventlet flask-wtf passlib

# 3) App starten
python app.py
