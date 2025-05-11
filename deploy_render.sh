#!/usr/bin/env bash
set -euo pipefail

REPO_URL="$1"

if [ -z "$REPO_URL" ]; then
  echo "Usage: $0 <git-repo-ssh-or-https-url>"
  exit 1
fi

echo "🔧 1) Erstelle requirements.txt"
cat > requirements.txt << 'EOF'
flask
flask-login
flask-sqlalchemy
flask-socketio
eventlet
flask-wtf
passlib
gunicorn
EOF

echo "🔧 2) Erstelle .gitignore"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtualenv
venv/
instance/
*.db

# Logs
*.log

# OS
.DS_Store
EOF

echo "🔧 3) Git initialisieren (falls nötig)"
if [ ! -d .git ]; then
  git init
  echo "→ Git-Repo angelegt."
else
  echo "→ Git-Repo existiert bereits."
fi

echo "🔧 4) Remote setzen"
if git remote | grep -q origin; then
  echo "→ Remote 'origin' existiert schon, setze URL neu."
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
  echo "→ Remote 'origin' hinzugefügt."
fi

echo "🔧 5) Auf main-Branch wechseln"
git branch -M main

echo "🔧 6) Alle Dateien zum Commit vormerken"
git add .

echo "🔧 7) Commit erstellen"
git commit -m "Prep for Render deployment" || echo "→ Keine Änderungen zum Committen."

echo "🔧 8) Push zu GitHub"
git push -u origin main

echo ""
echo "🎉 Fertig! Dein Repo ist nun auf GitHub."
echo "   Du kannst jetzt auf Render.com dein Web Service anlegen."
