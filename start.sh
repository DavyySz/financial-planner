#!/usr/bin/env bash
# Financial Planer - ein Skript fuer alles.
#
#   ./start.sh   oder   start      Alles in einem: installieren, Admin-Konto anlegen (beim ersten Mal),
#                                  Server starten und per Tunnel eine oeffentliche HTTPS-Adresse holen,
#                                  die von jedem Geraet in jedem Netz erreichbar ist.
#   start url                      zeigt die aktuelle oeffentliche Adresse
#   start dev                      Entwicklungsserver auf http://127.0.0.1:8000 (Debug an)
#   start server                   nur der Server auf 0.0.0.0:8000, ohne Tunnel (fuer eigene Server)
#   start install-service          als systemd-Dienst einrichten (Autostart beim Boot, braucht sudo)
#   start install-command          richtet den Kurzbefehl "start" ein (macht ./start.sh automatisch)
#   start test                     Tests ausfuehren
#   start <befehl>                 beliebiger manage.py-Befehl (createsuperuser, shell, ...)
#
# Beim ersten Aufruf wird alles installiert: python3/venv (per apt, falls noetig), eine
# virtuelle Umgebung, die Python-Pakete und der Tunnel-Client cloudflared.
# Einstellungen stehen in .env (wird automatisch angelegt). Daten: local.sqlite3.
set -euo pipefail
cd "$(dirname "$0")"
APP_DIR="$(pwd)"
TOOLS="$APP_DIR/.tools"
URL_FILE="$APP_DIR/public_url.txt"

# ---- .env laden ------------------------------------------------------------
# (Variablen, die schon in der Umgebung gesetzt sind, haben Vorrang, z.B. BIND=0.0.0.0:8010 start)
if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|\#*) continue ;; esac
    key="${line%%=*}"; value="${line#*=}"
    [ -z "${!key:-}" ] && export "$key=$value"
  done < .env
fi

# ---- Hilfsfunktionen -------------------------------------------------------
say()  { printf '\n>> %s\n' "$*"; }
warn() { printf '\n!! %s\n' "$*" >&2; }

apt_install() {
  if command -v apt-get >/dev/null 2>&1; then
    say "Installiere Systempakete: $*"
    sudo apt-get update -qq && sudo apt-get install -y -qq "$@"
  else
    warn "Bitte installieren: $* (kein apt-get gefunden, z.B. dnf/yum/brew benutzen)"; exit 1
  fi
}

download() {  # download URL ZIEL
  if command -v curl >/dev/null 2>&1; then curl -fsSL -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then wget -qO "$2" "$1"
  else apt_install curl && curl -fsSL -o "$2" "$1"; fi
}

# ---- Python und venv sicherstellen -----------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  apt_install python3 python3-venv python3-pip
fi

if [ -x "../bin/python" ] && [ -f "../pyvenv.cfg" ]; then
  PY="$APP_DIR/../bin/python"            # vorhandene venv des Projekts (myworld/)
elif [ -x ".venv/bin/python" ]; then
  PY="$APP_DIR/.venv/bin/python"
else
  say "Lege virtuelle Umgebung .venv an ..."
  if ! python3 -m venv .venv 2>/dev/null; then
    rm -rf .venv
    apt_install python3-venv python3-pip
    python3 -m venv .venv
  fi
  PY="$APP_DIR/.venv/bin/python"
fi

if ! "$PY" -c "import django, dj_database_url, whitenoise, gunicorn" 2>/dev/null; then
  say "Installiere Python-Pakete ..."
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -r requirements.txt
fi

# ---- .env fuer den Serverbetrieb anlegen -----------------------------------
ensure_env_file() {
  if [ -f .env ]; then return; fi
  say "Lege .env mit neuem geheimen Schluessel an ..."
  SECRET="$("$PY" -c 'import secrets; print(secrets.token_urlsafe(50))')"
  cat > .env <<ENV
# Einstellungen fuer den Betrieb (start). Nicht ins Git einchecken.
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=0
# Erlaubte Hostnamen/IPs, kommagetrennt. Leer = alle (einfachster Start).
DJANGO_ALLOWED_HOSTS=
# Nur bei eigener Domain hinter Caddy/nginx: DJANGO_HTTPS=1 und Domain eintragen
DJANGO_HTTPS=0
DJANGO_CSRF_TRUSTED_ORIGINS=
# Adresse/Port des Servers und Anzahl Worker
BIND=0.0.0.0:8000
WEB_CONCURRENCY=3
# Tunnel fuer eine oeffentliche Adresse ohne eigenen Server: cloudflare | off
TUNNEL=cloudflare
# Andere Datenbank, z.B. DATABASE_URL=postgres://user:pass@127.0.0.1:5432/financial_planer
#DATABASE_URL=
ENV
  chmod 600 .env
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|\#*) continue ;; esac
    key="${line%%=*}"; value="${line#*=}"
    [ -z "${!key:-}" ] && export "$key=$value"
  done < .env
}

port_free() {   # port_free PORT -> 0 wenn frei
  ! "$PY" -c "import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(0 if s.connect_ex(('127.0.0.1', $1))==0 else 1)" 2>/dev/null
}

# ---- Kurzbefehl "start" ----------------------------------------------------
install_command() {
  BIN="$HOME/.local/bin"; mkdir -p "$BIN"
  cat > "$BIN/start" <<CMD
#!/usr/bin/env bash
# Financial Planer:  start  |  start url  |  start dev  |  start server  |  start test  |  start <manage.py-befehl>
cd "$APP_DIR" || exit 1
exec ./start.sh "\$@"
CMD
  chmod +x "$BIN/start"
  case ":$PATH:" in *":$BIN:"*) ;; *)
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    say "$BIN zum PATH in ~/.bashrc hinzugefuegt (neues Terminal oeffnen)";;
  esac
}

# ---- Admin-Konto beim ersten Start -----------------------------------------
ensure_admin() {
  if "$PY" manage.py shell -c "import sys; from django.contrib.auth.models import User; sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>/dev/null; then
    return   # es gibt schon einen Admin
  fi
  local user="${DJANGO_SUPERUSER_USERNAME:-}" pass="${DJANGO_SUPERUSER_PASSWORD:-}" pass2
  if [ -z "$user" ] || [ -z "$pass" ]; then
    if [ ! -t 0 ]; then
      warn "Noch kein Admin-Konto. Spaeter anlegen mit:  start createsuperuser"
      return
    fi
    echo
    echo "=============================================================="
    echo " Erster Start: Admin-Konto anlegen (fuer /admin/ und Dashboard)"
    echo "=============================================================="
    while true; do
      read -r -p "Admin-Benutzername [$(id -un)]: " user; user="${user:-$(id -un)}"
      read -r -s -p "Admin-Passwort: " pass; echo
      read -r -s -p "Passwort wiederholen: " pass2; echo
      if [ -z "$pass" ]; then echo "Das Passwort darf nicht leer sein."; continue; fi
      if [ "$pass" != "$pass2" ]; then echo "Die Passwoerter stimmen nicht ueberein."; continue; fi
      break
    done
  fi
  DJANGO_SUPERUSER_USERNAME="$user" DJANGO_SUPERUSER_PASSWORD="$pass" "$PY" manage.py shell -c "
import os
from django.contrib.auth.models import User
from members.models import Member
u, _ = User.objects.get_or_create(username=os.environ['DJANGO_SUPERUSER_USERNAME'])
u.set_password(os.environ['DJANGO_SUPERUSER_PASSWORD']); u.is_staff = True; u.is_superuser = True; u.save()
Member.objects.get_or_create(user=u, defaults={'firstname': u.username, 'lastname': ''})
print('>> Admin-Konto \"%s\" angelegt.' % u.username)
"
}

# ---- Tunnel (oeffentliche Adresse) -----------------------------------------
ensure_cloudflared() {
  if command -v cloudflared >/dev/null 2>&1; then CLOUDFLARED="$(command -v cloudflared)"; return 0; fi
  CLOUDFLARED="$TOOLS/cloudflared"
  if [ -x "$CLOUDFLARED" ]; then return 0; fi
  local arch
  case "$(uname -m)" in
    x86_64) arch=amd64 ;; aarch64|arm64) arch=arm64 ;; armv7l) arch=arm ;;
    *) warn "Unbekannte Architektur $(uname -m), Tunnel nicht verfuegbar"; return 1 ;;
  esac
  say "Lade Tunnel-Client cloudflared herunter ..."
  mkdir -p "$TOOLS"
  if download "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$arch" "$CLOUDFLARED.tmp"; then
    mv "$CLOUDFLARED.tmp" "$CLOUDFLARED"; chmod +x "$CLOUDFLARED"; return 0
  fi
  rm -f "$CLOUDFLARED.tmp"
  warn "Download von cloudflared fehlgeschlagen (kein Internet?). Die App laeuft nur lokal."
  return 1
}

start_tunnel() {   # start_tunnel PORT
  ensure_cloudflared || return 0
  local log="$APP_DIR/.tools/tunnel.log"
  : > "$log"
  "$CLOUDFLARED" tunnel --url "http://127.0.0.1:$1" --no-autoupdate >"$log" 2>&1 &
  TUNNEL_PID=$!
  local url="" i
  for i in $(seq 1 60); do
    url="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$log" | head -1 || true)"
    [ -n "$url" ] && break
    kill -0 "$TUNNEL_PID" 2>/dev/null || break
    sleep 1
  done
  if [ -z "$url" ]; then
    warn "Tunnel konnte keine Adresse bekommen (siehe $log). Die App laeuft nur lokal."
    return 0
  fi
  # warten, bis die neue Adresse weltweit aufloesbar ist (dauert meist 5-20 s)
  for i in $(seq 1 40); do
    "$PY" -c "import urllib.request as u; u.urlopen('$url/login/', timeout=10)" 2>/dev/null && break
    sleep 3
  done
  echo "$url" > "$URL_FILE"
  echo
  echo "=============================================================="
  echo "  OEFFENTLICHE ADRESSE (von ueberall erreichbar, HTTPS):"
  echo
  echo "      $url"
  echo
  echo "  Konto anlegen:  $url/signup/"
  echo "  Admin:          $url/admin/"
  echo "  Die Adresse aendert sich bei jedem Start (start url zeigt sie an)."
  echo "=============================================================="
}

run_server() {   # run_server [BIND] [mit_tunnel]
  ensure_env_file
  export DJANGO_DEBUG=0
  local bind="${1:-${BIND:-0.0.0.0:8000}}" with_tunnel="${2:-no}" port
  port="${bind##*:}"
  if ! port_free "$port"; then
    warn "Port $port ist schon belegt. Laeuft die App bereits (anderes Terminal, Dienst)?"
    echo "   Dort mit Strg+C beenden bzw.  sudo systemctl stop financial-planer  oder anderen Port nehmen:  BIND=0.0.0.0:8010 start"
    exit 1
  fi
  "$PY" manage.py migrate --noinput
  "$PY" manage.py collectstatic --noinput --clear >/dev/null
  "$PY" manage.py check --deploy --fail-level ERROR
  ensure_admin
  rm -f "$URL_FILE"

  "$PY" -m gunicorn --bind "$bind" --workers "${WEB_CONCURRENCY:-3}" \
        --access-logfile - --error-logfile - financial_planer.wsgi &
  SERVER_PID=$!
  TUNNEL_PID=""
  trap 'echo; say "Beende ..."; [ -n "$TUNNEL_PID" ] && kill "$TUNNEL_PID" 2>/dev/null; kill "$SERVER_PID" 2>/dev/null; wait; rm -f "$URL_FILE"; exit 0' INT TERM

  local i
  for i in $(seq 1 30); do
    "$PY" -c "import urllib.request as u; u.urlopen('http://127.0.0.1:$port/login/')" 2>/dev/null && break
    kill -0 "$SERVER_PID" 2>/dev/null || { warn "Server konnte nicht starten."; exit 1; }
    sleep 1
  done
  say "Server laeuft auf $bind  (lokal: http://127.0.0.1:$port/)"

  if [ "$with_tunnel" = "yes" ] && [ "${TUNNEL:-cloudflare}" != "off" ]; then
    start_tunnel "$port"
  fi
  say "Beenden mit Strg+C."
  wait "$SERVER_PID" || true
  [ -n "$TUNNEL_PID" ] && kill "$TUNNEL_PID" 2>/dev/null
  rm -f "$URL_FILE"
}

# ---- Befehle ---------------------------------------------------------------
case "${1:-}" in
  "")
    [ -x "$HOME/.local/bin/start" ] || install_command
    run_server "${BIND:-0.0.0.0:8000}" yes
    ;;
  server)
    run_server "${2:-${BIND:-0.0.0.0:8000}}" no
    ;;
  url)
    if [ -s "$URL_FILE" ]; then cat "$URL_FILE"; else echo "Kein Tunnel aktiv. Starten mit:  start"; exit 1; fi
    ;;
  dev)
    "$PY" manage.py migrate --noinput
    say "Entwicklungsserver: http://127.0.0.1:${2:-8000}  (Beenden mit Strg+C)"
    exec "$PY" manage.py runserver "127.0.0.1:${2:-8000}"
    ;;
  install-command)
    install_command
    say "Fertig. Ab jetzt reicht im Terminal:  start"
    ;;
  install-service)
    ensure_env_file
    ensure_admin
    SERVICE=/etc/systemd/system/financial-planer.service
    say "Schreibe $SERVICE (braucht sudo) ..."
    sudo tee "$SERVICE" >/dev/null <<UNIT
[Unit]
Description=Financial Planer (Django/gunicorn + Tunnel)
After=network-online.target
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
    sudo systemctl daemon-reload
    sudo systemctl enable --now financial-planer
    sleep 3
    sudo systemctl --no-pager --lines=5 status financial-planer || true
    say "Dienst laeuft und startet bei jedem Boot. Logs: journalctl -u financial-planer -f"
    echo "   Oeffentliche Adresse: start url   (kurz nach dem Start verfuegbar)"
    ;;
  *)
    exec "$PY" manage.py "$@"
    ;;
esac
