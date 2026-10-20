# Financial Planer

Webanwendung zur monatlichen Finanzplanung, geschrieben in Python mit Django.
Nutzer registrieren sich, tragen ihr monatliches Einkommen ein, legen Kategorien
(„Budgettöpfe“) mit einer monatlichen Rate an, z. B. Auto oder Urlaub, und buchen
einmalige Ein- und Auszahlungen. Das Dashboard zeigt jederzeit, wie viel vom Einkommen
frei bleibt und wie viel Geld in jedem Topf liegt. Jeder Nutzer sieht nur seine eigenen Daten.

**Inhalt**

1. [Schnellstart](#1-schnellstart)
2. [Bedienung](#2-bedienung)
3. [Rechenlogik](#3-rechenlogik)
4. [Das Startskript `start.sh`](#4-das-startskript-startsh)
5. [Auf einem Server hosten](#5-auf-einem-server-hosten)
6. [Konfiguration](#6-konfiguration)
7. [Technischer Aufbau](#7-technischer-aufbau)
8. [Entwicklung](#8-entwicklung)
9. [Fehlerbehebung](#9-fehlerbehebung)
10. [Project Description (original)](#10-project-description-original)

---

## 1. Schnellstart

Voraussetzung: ein Linux-Rechner mit Internet (Python 3.12 oder neuer; fehlt es, wird es
per apt nachinstalliert). Eine Datenbank muss nicht installiert werden.

```bash
git clone <adresse-deines-repos> financial_planer
cd financial_planer
./start.sh
```

Beim ersten Start passiert automatisch:

1. Falls nötig werden `python3` und `python3-venv` per `apt` installiert (fragt nach sudo).
2. Eine virtuelle Umgebung wird angelegt und die Pakete aus `requirements.txt` installiert.
3. Eine Datei `.env` mit einem zufälligen Secret-Key und Produktionseinstellungen wird erzeugt.
4. Der Kurzbefehl `start` wird eingerichtet; ab dann reicht `start` in jedem Terminal.
5. Die Datenbank `local.sqlite3` wird angelegt und die statischen Dateien gesammelt.
6. **Du wirst nach Benutzername und Passwort für das Admin-Konto gefragt.** Dieses Konto
   kann sich im Dashboard anmelden und zusätzlich unter `/admin/` alle Daten einsehen.
7. Der Webserver gunicorn startet auf Port 8000.
8. Der Tunnel-Client `cloudflared` wird heruntergeladen und gestartet. Er verbindet deinen
   Rechner mit dem Cloudflare-Netz und liefert eine **öffentliche HTTPS-Adresse**, z. B.
   `https://zwei-drei-woerter.trycloudflare.com`. Die Adresse wird groß im Terminal angezeigt.

Diese Adresse funktioniert von jedem Gerät in jedem Netz, auch über Mobilfunk, ohne dass
du Router, Firewall oder Portfreigaben anfassen musst. Jeder kann sich darunter unter
`/signup/` ein Konto anlegen. Dein Rechner muss dafür laufen und online sein; Beenden mit
`Strg+C` schaltet Server und Tunnel ab.

Die Adresse ändert sich bei jedem Start. `start url` zeigt die aktuelle an. Eine feste
Adresse bekommst du mit einem eigenen Server (Abschnitt 5) oder einem kostenlosen
Cloudflare-Konto mit eigener Domain (Abschnitt 5.3).

## 2. Bedienung

### 2.1 Seiten

| Adresse | Zweck |
|---|---|
| `/` | leitet zum Dashboard bzw. zum Login weiter |
| `/signup/` | Konto anlegen (Benutzername, Passwort zweimal) |
| `/login/` | Anmelden |
| `/logout/` | Abmelden (Button oben rechts) |
| `/dashboard/` | Hauptseite: Übersicht, Kategorien, Buchungen |
| `/dashboard/change_data/?category=NAME` | Rate und Kommentar einer Kategorie ändern, Verlauf ansehen |
| `/passwort-vergessen/` | neues Passwort beim Admin beantragen |
| `/adminboard/` | Adminboard: Nutzerübersicht, wer online ist, Passwort-Anfragen, Verwaltung (nur Admin) |
| `/admin/` | technischer Django-Admin mit direktem Datenbankzugriff (nur Admin) |

### 2.2 Konto anlegen und anmelden

Auf der Login-Seite auf „Jetzt registrieren“ klicken. Das Passwort muss mindestens
8 Zeichen lang sein, darf nicht nur aus Zahlen bestehen und nicht zu ähnlich zum
Benutzernamen sein. Nach der Registrierung bist du direkt angemeldet.

### 2.3 Dashboard

Das Dashboard besteht aus vier Bereichen, von oben nach unten:

**Monatsübersicht.** Hier trägst du dein monatliches Einkommen ein (Gehalt und andere
regelmäßige Einnahmen zusammen). Darunter erscheinen vier Kennzahlen:

| Kennzahl | Bedeutung |
|---|---|
| Einkommen | der eingetragene Betrag |
| Einzahlungen in Töpfe | Summe aller positiven Raten (Geld, das monatlich in Kategorien zurückgelegt wird) |
| monatliche Abbuchungen | Summe aller negativen Raten (z. B. Miete, Kredit), als Betrag angezeigt |
| frei verfügbar | Einkommen minus Einzahlungen minus Abbuchungen; rot, wenn negativ |
| Guthaben in allen Töpfen | Summe der Kontostände aller Kategorien |

**Kategorien / Budgettöpfe.** Eine Tabelle mit allen Kategorien. Pro Zeile:

| Spalte | Bedeutung |
|---|---|
| Kategorie | Name; Klick öffnet die Änderungsseite |
| Rate pro Monat | aktuell gültige monatliche Rate; positiv = Einzahlung in den Topf, negativ (rot) = monatliche Abbuchung |
| Monate aktiv | seit wie vielen Monaten die Rate läuft, Erstellungsmonat zählt mit |
| eingezahlte Raten | Summe aller Monatsraten seit Erstellung (bei Abbuchungen negativ: bisher gezahlt) |
| Ein-/Auszahlungen | Summe der einmaligen Buchungen (grün positiv, rot negativ) |
| Kontostand | eingezahlte Raten plus Ein-/Auszahlungen; rot, wenn negativ |
| Kommentar | freier Text |
| ändern / löschen | Rate ändern bzw. Kategorie samt Buchungen löschen (mit Rückfrage) |

**Neue Kategorie** und **Ein-/Auszahlung buchen.** Zwei Formulare nebeneinander.
Eine Kategorie braucht einen Namen (max. 25 Zeichen, pro Nutzer eindeutig, Groß-/
Kleinschreibung egal) und eine monatliche Rate. Die Rate darf negativ sein: `100` legt
jeden Monat 100 € in den Topf zurück (Sparen), `-800` ist eine monatliche Abbuchung wie
Miete oder eine Kreditrate. Bei einer Abbuchung wird der Kontostand der Kategorie jeden
Monat um den Betrag kleiner und zeigt so, was bisher gezahlt wurde. Eine Buchung braucht eine Kategorie und
einen Betrag: positiv = Einzahlung, negativ = Auszahlung (z. B. `-150` für eine Reparatur).
Beträge dürfen mit Komma oder Punkt geschrieben werden (`99,90` oder `99.90`).

**Ein- und Auszahlungen.** Liste aller Buchungen, neueste zuerst, mit Löschen-Button.
Eine Buchung lässt sich nicht bearbeiten; löschen und neu anlegen erfüllt denselben Zweck.

### 2.4 Rate einer Kategorie ändern

Auf den Kategorienamen oder „ändern“ klicken. Die neue Rate gilt ab dem laufenden Monat
(einschließlich) für die Zukunft. Frühere Monate werden weiterhin mit der damals gültigen
Rate gerechnet. Rechts siehst du den Verlauf aller Raten mit Gültigkeitsbeginn. Wird die
Rate im selben Monat mehrfach geändert, zählt nur der letzte Wert für diesen Monat.

### 2.5 Mehrere Nutzer

Jedes Konto hat seine eigenen Kategorien und Buchungen. Ein Nutzer kann die Daten eines
anderen weder sehen noch ändern oder löschen; entsprechende Versuche enden mit „Nicht
gefunden“. Das ist durch Tests abgesichert.

### 2.6 Passwort vergessen

Es gibt keinen E-Mail-Versand. Stattdessen klickt der Nutzer auf der Login-Seite auf
„Neues Passwort beim Admin beantragen“, gibt seinen Benutzernamen und optional eine
Nachricht ein (z. B. wie er erreichbar ist). Der Admin sieht die Anfrage sofort als
Hinweis auf jeder Seite und im Adminboard, setzt dort ein neues Passwort und teilt es dem
Nutzer mit. Pro Benutzername gibt es höchstens eine offene Anfrage.

### 2.7 Adminboard

Das Konto, das beim ersten `start` angelegt wurde, ist Admin. Admins sehen in der
Kopfzeile den Link „Adminboard“ mit einer roten Zahl, sobald Passwort-Anfragen offen sind.
Das Adminboard zeigt:

| Bereich | Inhalt |
|---|---|
| Kennzahlen | Benutzer gesamt, gerade online, offene Passwort-Anfragen, neue und aktive Nutzer der letzten 7 Tage, Admins, Kategorien und Buchungen gesamt |
| Passwort-Anfragen | offene Anfragen mit Zeit, Benutzername und Nachricht; direkt daneben ein Feld zum Setzen des neuen Passworts; „erledigt“ oder „löschen“; aufklappbar die zuletzt erledigten |
| Benutzer | pro Nutzer: Online-Punkt, Name, Rolle, Status, zuletzt aktiv, Registrierungsdatum, Einkommen, Anzahl Kategorien, Guthaben, Anzahl Buchungen; unter „Passwort / Verwalten“: Passwort setzen, sperren/entsperren, Admin-Rechte geben/nehmen, Nutzer löschen |
| Letzte Buchungen | die zehn neuesten Buchungen aller Nutzer |

„Online“ bedeutet: in den letzten 5 Minuten eine Seite aufgerufen. Dafür merkt sich die
App bei jeder Anfrage eines angemeldeten Nutzers den Zeitpunkt (höchstens einmal pro
Minute).

**Zugangsdaten.** Benutzernamen sind sichtbar. Passwörter werden von Django nur als
Hash gespeichert und können von niemandem angezeigt werden, auch nicht vom Admin. Der
Admin kann aber jederzeit ein neues Passwort setzen. Ein Admin kann sich nicht selbst
sperren, löschen oder die Admin-Rechte nehmen.

Der technische Django-Admin unter `/admin/` bleibt erreichbar (Link im Adminboard) und
erlaubt den direkten Zugriff auf alle Tabellen.

---

## 3. Rechenlogik

Alle Werte werden bei jedem Seitenaufruf aus den gespeicherten Daten neu berechnet; es
gibt keine abgeleiteten Werte, die veralten könnten. Gerechnet wird mit `Decimal`, nicht
mit Gleitkommazahlen, damit Centbeträge exakt bleiben.

### 3.1 Begriffe

Für eine Kategorie ist die **Raten-Historie** eine Liste von Einträgen
$(r_i,\ y_i,\ m_i)$: Rate $r_i$ gilt ab Monat $m_i$ des Jahres $y_i$. Der erste Eintrag
entsteht beim Anlegen der Kategorie, jede Änderung in einem neuen Monat fügt einen
Eintrag an.

Die Anzahl Monate zwischen zwei Monatsangaben ist

$$
\text{months}(y_a, m_a;\ y_b, m_b) = 12\,(y_b - y_a) + (m_b - m_a).
$$

### 3.2 Formeln

**Monate aktiv** (heute = $(y_h, m_h)$, Erstellung = $(y_c, m_c)$):

$$
\text{aktiv} = \text{months}(y_c, m_c;\ y_h, m_h) + 1
$$

**Eingezahlte Raten.** Jeder Eintrag zahlt monatlich seine Rate, bis der nächste Eintrag
beginnt; der letzte Eintrag läuft bis heute einschließlich:

$$
\text{Raten} = \sum_{i} r_i \cdot n_i,\qquad
n_i = \begin{cases}
\text{months}(y_i, m_i;\ y_{i+1}, m_{i+1}) & \text{wenn ein Eintrag } i{+}1 \text{ folgt}\\[4pt]
\text{months}(y_i, m_i;\ y_h, m_h) + 1 & \text{für den letzten Eintrag}
\end{cases}
$$

**Kontostand** einer Kategorie und **frei verfügbar**:

$$
\text{Kontostand} = \text{Raten} + \sum \text{Buchungen},\qquad
\text{frei} = \text{Einkommen} - \sum_{\text{Kategorien}} \lvert r_{\text{aktuell}} \rvert
$$

Raten gehen mit Vorzeichen in die Historie und den Kontostand ein (eine Abbuchung von
$-800$ € über 3 Monate ergibt einen Kontostand von $-2400$ €). Für den frei verfügbaren
Betrag zählt der Betrag ohne Vorzeichen, weil sowohl Einzahlungen in Töpfe als auch
Abbuchungen das Einkommen verringern.

### 3.3 Beispiel

Kategorie „Urlaub“, angelegt im März 2026 mit 50 €, im Juli 2026 auf 100 € geändert,
heute ist Oktober 2026. Eine Auszahlung von 30 € für einen Koffer.

1. Historie: $(50,\ 2026,\ 3)$ und $(100,\ 2026,\ 7)$.
2. Erster Eintrag: $n_1 = \text{months}(2026,3;\ 2026,7) = 4$ Monate (März bis Juni), also $4 \cdot 50 = 200$ €.
3. Letzter Eintrag: $n_2 = \text{months}(2026,7;\ 2026,10) + 1 = 4$ Monate (Juli bis Oktober), also $4 \cdot 100 = 400$ €.
4. Eingezahlte Raten: $200 + 400 = 600$ €. Monate aktiv: $7 + 1 = 8$.
5. Kontostand: $600 - 30 = 570$ €.

Die Ratenrechnung dieses Beispiels (600 €) ist als Test in `members/tests.py` hinterlegt.

---

## 4. Das Startskript `start.sh`

`start.sh` ist der einzige Einstiegspunkt. Es sorgt selbst für Python, virtuelle Umgebung,
Pakete und Tunnel-Client, liest die Datei `.env` und führt dann den gewünschten Befehl aus.
Nach dem ersten Lauf steht der Kurzbefehl `start` zur Verfügung, der genau dasselbe tut.

| Aufruf | Wirkung |
|---|---|
| `start` (= `./start.sh`) | alles: installieren, Admin anlegen (nur beim ersten Mal), Server auf `0.0.0.0:8000`, Tunnel mit öffentlicher HTTPS-Adresse |
| `start url` | zeigt die aktuelle öffentliche Adresse |
| `start dev` | Entwicklungsserver auf `127.0.0.1:8000`, Debug an, lädt bei Codeänderungen neu |
| `start dev 8080` | Entwicklungsserver auf anderem Port |
| `start server` | nur der Server auf `0.0.0.0:8000`, ohne Tunnel (für eigene Server mit öffentlicher IP) |
| `start server 127.0.0.1:8000` | Server auf anderer Adresse, z. B. hinter einem Reverse-Proxy |
| `start install-service` | systemd-Dienst `financial-planer` einrichten (Autostart beim Boot, braucht sudo) |
| `start install-command` | Kurzbefehl `start` (neu) einrichten |
| `start test` | führt die Tests aus |
| `start createsuperuser` | weiteres Admin-Konto anlegen |
| `start <befehl>` | jeder andere `manage.py`-Befehl, z. B. `shell`, `migrate`, `changepassword` |

Umgebungsvariablen vor dem Befehl haben Vorrang vor `.env`, z. B. `BIND=0.0.0.0:8010 start`.

Unterschied Entwicklung und Betrieb:

| | Entwicklung (`start dev`) | Betrieb (`start`) |
|---|---|---|
| Webserver | Django `runserver` | gunicorn, 3 Worker |
| erreichbar | nur vom eigenen Rechner | aus dem Internet über die Tunnel-Adresse, im lokalen Netz über die IP |
| `DEBUG` | an: ausführliche Fehlerseiten | aus: neutrale Fehlerseiten |
| statische Dateien | Django liefert sie direkt | `collectstatic` + whitenoise |
| Secret-Key | aus `.env`, sonst `.secret_key` (automatisch erzeugt) | aus `.env`, automatisch erzeugt |

Ist der Port schon belegt (z. B. weil `start` in einem anderen Terminal läuft), bricht das
Skript mit einem Hinweis ab, statt doppelt zu starten.

Welche virtuelle Umgebung benutzt wird: zuerst eine vorhandene im übergeordneten Ordner
(`../bin/python`, so liegt das Projekt in der Entwicklungsumgebung), sonst `.venv` im
Projektordner, die bei Bedarf angelegt wird. Der Tunnel-Client liegt in `.tools/`.

## 5. Auf einem Server hosten

### 5.0 Wie lange ist die App erreichbar?

Nach `start` ist die App genau so lange erreichbar, wie alle drei Punkte gelten:

1. **Das Terminal mit `start` läuft.** `Strg+C`, Schließen des Terminals oder Abmelden
   beendet Server und Tunnel sofort. Eine Zeitbegrenzung gibt es nicht.
2. **Der Rechner ist an und wach.** Zuklappen oder Standby unterbricht die Verbindung;
   nach dem Aufwachen verbindet sich der Tunnel meist von selbst wieder, die Adresse bleibt.
   Für längeren Betrieb in den Energieeinstellungen den Standby bei geschlossenem Deckel
   abschalten.
3. **Der Rechner ist online.** Ein Wechsel der (Mobilfunk-)IP stört nicht, weil der Tunnel
   von innen nach außen aufgebaut wird. Nach einem Verbindungsabbruch verbindet sich der
   Tunnel-Client automatisch neu.

Einschränkungen des Schnelltunnels (ohne Cloudflare-Konto): keine Verfügbarkeitsgarantie,
Cloudflare kann die Verbindung jederzeit trennen, und bei jedem Neustart gibt es eine neue
Adresse. Für gelegentliches Nutzen und Vorführen reicht das; für Dauerbetrieb mit mehreren
Nutzern einen der folgenden Wege wählen.

| Ziel | Weg |
|---|---|
| läuft nach einem Neustart des Rechners von selbst wieder | `start install-service` (Abschnitt 5.1), Adresse mit `start url` |
| feste Adresse, die sich nicht ändert | Cloudflare-Konto mit eigener Domain (Abschnitt 5.2, „Feste Tunnel-Adresse“) |
| rund um die Uhr, unabhängig vom eigenen Rechner | gemieteter Server (Abschnitt 5.2) oder Docker (5.3) oder fly.io (5.4) |

### 5.1 Eigener Rechner, dauerhaft (Tunnel + Autostart)

```bash
start install-service      # Dienst einrichten, startet nach jedem Reboot automatisch
start url                  # öffentliche Adresse (kurz nach dem Start verfügbar)
journalctl -u financial-planer -f     # Logs, dort steht auch die Adresse
```

Der Dienst startet Server und Tunnel zusammen. Die Adresse ändert sich bei jedem Neustart.

### 5.2 Variante A: gemieteter Linux-Server mit öffentlicher IP

Geeignet ist jeder Linux-Server mit SSH-Zugang, z. B. ein kleiner VPS bei Hetzner, Strato,
IONOS, AWS oder DigitalOcean; Ubuntu oder Debian werden vom Skript voll unterstützt.
Hier ist kein Tunnel nötig, die IP ist direkt erreichbar.

```bash
# auf dem Server
git clone <adresse-deines-repos> financial_planer
cd financial_planer
./start.sh                 # erster Start: installiert alles, fragt nach dem Admin-Konto; Strg+C
sed -i 's/^TUNNEL=.*/TUNNEL=off/' .env     # Tunnel aus, die IP ist ja öffentlich
start install-service      # dauerhaft als Dienst
sudo ufw allow 8000/tcp    # Port öffnen, falls ufw aktiv ist
```

Jetzt ist die App unter `http://<server-ip>:8000` für alle erreichbar.

Nützliche Befehle im laufenden Betrieb:

```bash
sudo systemctl status financial-planer     # läuft der Dienst?
journalctl -u financial-planer -f          # Logs live
sudo systemctl restart financial-planer    # Neustart, z. B. nach git pull
```

Updates einspielen: `git pull`, dann `sudo systemctl restart financial-planer`. Das Skript
führt beim Start neue Migrationen automatisch aus.

#### HTTPS mit eigener Domain

Ohne HTTPS gehen Passwörter unverschlüsselt durch das Internet. (Die Tunnel-Adresse aus
dem Schnellstart ist bereits HTTPS.) Für einen eigenen Server eine Domain auf die IP zeigen
lassen und **Caddy** davorschalten; Caddy holt und erneuert das Zertifikat automatisch.
Ports 80 und 443 müssen offen sein.

```bash
sudo apt install -y caddy
printf 'finanzen.example.de {\n    reverse_proxy 127.0.0.1:8000\n}\n' | sudo tee /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Dann in `.env` eintragen und den Dienst neu starten:

```
DJANGO_HTTPS=1
DJANGO_ALLOWED_HOSTS=finanzen.example.de
DJANGO_CSRF_TRUSTED_ORIGINS=https://finanzen.example.de
BIND=127.0.0.1:8000
TUNNEL=off
```

`BIND=127.0.0.1` sorgt dafür, dass die App nur noch über Caddy erreichbar ist; Port 8000
kann dann in der Firewall wieder geschlossen werden.

#### Feste Tunnel-Adresse mit Cloudflare-Konto

Wer keinen Server mieten will, aber eine feste Adresse braucht: kostenloses Cloudflare-Konto
anlegen, eigene Domain dort verwalten und einen benannten Tunnel einrichten
(`cloudflared tunnel login`, `cloudflared tunnel create ...`, siehe Cloudflare-Doku
„Cloudflare Tunnel“). Dann in `.env` `TUNNEL=off` setzen und den benannten Tunnel auf
`http://127.0.0.1:8000` zeigen lassen.

### 5.3 Variante B: Docker

Wenn auf dem Server Docker läuft, braucht es keine Python-Installation:

```bash
docker compose up -d --build        # -> http://<server-ip>:8000
docker compose logs -f              # Logs
docker compose down                 # stoppen (Daten bleiben im Volume)
```

Mit Domain und automatischem HTTPS (startet zusätzlich einen Caddy-Container):

```bash
DOMAIN=finanzen.example.de docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --build
```

Datenbank und Secret-Key liegen im Docker-Volume `fp-data`. Einstellungen können in einer
`.env` neben der `docker-compose.yml` stehen.

### 5.4 Variante C: fly.io (kostenpflichtig, nicht mehr genutzt)

`fly.toml` und `Dockerfile` sind für fly.io vorbereitet, werden aber nicht mehr benötigt:
Alle anderen Wege in dieser Anleitung sind kostenlos. Die GitHub-Action
`.github/workflows/fly-deploy.yml` startet **nur noch manuell** (GitHub → Actions →
„Run workflow“), ein Push löst kein Deployment mehr aus.

Damit bei fly.io keine Gebühren mehr anfallen, im fly.io-Dashboard (<https://fly.io/dashboard>)
die App `financial-planer-2` und die zugehörige Postgres-App löschen („Settings → Delete app“)
und unter „Billing“ die Zahlungsmethode entfernen. Das geht nur dort mit deinem Login.

---

## 6. Konfiguration

Alle Einstellungen kommen aus Umgebungsvariablen. Im Serverbetrieb stehen sie in der Datei
`.env` im Projektordner, die `start.sh` beim ersten `start` anlegt und bei jedem Aufruf
einliest. Die Datei ist von Git ausgeschlossen.

| Variable | Standard | Bedeutung |
|---|---|---|
| `DJANGO_SECRET_KEY` | automatisch erzeugt | Schlüssel für Sessions und CSRF-Schutz. Fehlt er, wird einer erzeugt und in `.secret_key` (bzw. `DJANGO_SECRET_KEY_FILE`) abgelegt |
| `DJANGO_DEBUG` | `1` | `1` Entwicklung, `0` Produktion. `start`/`./start.sh server` setzen immer `0` |
| `DJANGO_ALLOWED_HOSTS` | leer = alle | erlaubte Hostnamen oder IPs, kommagetrennt. Für den einfachen Start leer lassen, bei einer Domain eintragen |
| `DJANGO_HTTPS` | `0` | `1`, wenn die App hinter HTTPS läuft: Cookies nur über HTTPS, Umleitung von http auf https |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | leer | bei HTTPS hinter Proxy: `https://deine-domain` |
| `BIND` | `0.0.0.0:8000` | Adresse und Port für gunicorn |
| `WEB_CONCURRENCY` | `3` | Anzahl gunicorn-Worker |
| `TUNNEL` | `cloudflare` | `cloudflare` = bei `start` öffentliche Adresse per Cloudflare-Schnelltunnel holen; `off` = kein Tunnel |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` | leer | nur für unbeaufsichtigte Installation: Admin-Konto ohne Rückfrage anlegen |
| `DATABASE_URL` | SQLite `local.sqlite3` | andere Datenbank, z. B. `postgres://user:passwort@127.0.0.1:5432/financial_planer` |

Eine frisch erzeugte `.env` sieht so aus:

```
DJANGO_SECRET_KEY=<zufällig>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=
DJANGO_HTTPS=0
DJANGO_CSRF_TRUSTED_ORIGINS=
BIND=0.0.0.0:8000
WEB_CONCURRENCY=3
TUNNEL=cloudflare
#DATABASE_URL=
```

**Datenbank.** SQLite reicht für private Nutzung und kleine Gruppen völlig aus; die Datei
`local.sqlite3` enthält alle Daten und lässt sich zum Sichern einfach kopieren. Für viele
gleichzeitige Nutzer PostgreSQL per `DATABASE_URL` anbinden; die Migrationen laufen dort
genauso. Die alte Datei `db.sqlite3` im Projekt stammt aus einer früheren Projektphase mit
anderer Migrationshistorie und wird nicht mehr verwendet.

---

## 7. Technischer Aufbau

### 7.1 Projektstruktur

```
financial_planer/               Django-Projekt
  settings.py                   Einstellungen (liest Umgebungsvariablen, siehe Abschnitt 6)
  urls.py                       Login/Logout/Admin, bindet members/urls.py ein
  wsgi.py, asgi.py              Einstiegspunkte für gunicorn
members/                        die eigentliche App
  models.py                     Datenmodell und Berechnungen (Member, MemberAttribute, Transaction)
  views.py                      Seitenlogik: Registrierung, Dashboard, Buchungen, Löschen
  forms.py                      Registrierungsformular
  middleware.py                 merkt sich die letzte Aktivitaet (fuer "online")
  context_processors.py         Zahl offener Passwort-Anfragen fuer die Kopfzeile
  urls.py                       Adressen der App
  admin.py                      Anzeige im Django-Admin
  tests.py                      automatische Tests
  Calculate_monthly_payments.py Rechenfunktionen für die Monatsraten
  date.py                       Monate seit Erstellung
  Check_whether_category_is_duplicated.py  Duplikatprüfung
  migrations/                   Datenbankschema-Historie (0001 bis 0009)
  templates/
    base.html                   Grundgerüst mit Kopfzeile, Menü und Stil
    dashboard.html              Hauptseite
    change_data.html            Rate ändern
    adminboard.html             Adminboard
    registration/login.html, signup.html, password_request.html
start.sh                        Startskript (Abschnitt 4); .tools/ = Tunnel-Client, .env = Einstellungen
requirements.txt                Python-Pakete
Dockerfile, docker-compose.yml, docker-compose.https.yml   Docker-Betrieb
fly.toml                        fly.io-Konfiguration
```

Nicht mehr genutzte Reste aus der Anfangsphase: `members/calculate_new_value.py` sowie die
Templates `main.html`, `master.html`, `all_members.html`, `details.html`, `template.html`,
`404.html`, `members/myfirst.html`. Sie werden von keiner Seite mehr verwendet und können
gelöscht werden.

### 7.2 Datenmodell

```mermaid
classDiagram
  class User {
    username
    password
  }
  class Member {
    firstname
    lastname
    monthly_salary
  }
  class MemberAttribute {
    category
    monthly_amount
    comment
    creation_date_of_the_category
  }
  class Transaction {
    amount
    comment
    created
  }
  class PasswordResetRequest {
    username
    message
    created
    resolved
  }
  User "1" -- "*" PasswordResetRequest
  User "1" -- "1" Member
  Member "1" -- "*" MemberAttribute : attributes
  MemberAttribute "1" -- "*" Transaction : transactions
```

- **User** ist Djangos eingebautes Benutzerkonto (Benutzername, gehashtes Passwort).
- **Member** hängt eins zu eins am User und speichert das monatliche Einkommen. Er wird beim
  ersten Aufruf des Dashboards automatisch angelegt.
- **MemberAttribute** ist eine Kategorie bzw. ein Budgettopf. Das Feld `monthly_amount`
  enthält die Raten-Historie als JSON-Liste `[[betrag, jahr, monat], ...]`, z. B.
  `[["50.00", 2026, 3], ["100.00", 2026, 7]]`. Einige weitere Felder (`monthly_amount_value`,
  `total_monthly_payments`, `new_amount`, …) stammen aus früheren Versionen und werden
  nicht mehr für die Anzeige verwendet; alle Kennzahlen werden live berechnet.
- **Transaction** ist eine einmalige Buchung mit Betrag (positiv/negativ), Kommentar und
  Zeitstempel.
- **PasswordResetRequest** ist eine „Passwort vergessen“-Anfrage an den Admin mit
  Benutzername, Nachricht, Zeit und Status (offen/erledigt).
- **Member.last_seen** hält den Zeitpunkt der letzten Aktivität für die Online-Anzeige.

Beim Löschen eines Users verschwinden Member, Kategorien und Buchungen automatisch mit
(`on_delete=CASCADE`), ebenso die Buchungen beim Löschen einer Kategorie.

### 7.3 Ablauf einer Anfrage

```mermaid
flowchart LR
  B["Browser"] --> G["gunicorn / runserver"]
  G --> M["Middleware: Session, CSRF, Auth"]
  M --> V["views.py"]
  V --> D["models.py + SQLite/Postgres"]
  V --> T["Templates"]
  T --> B
```

Alle Seiten außer Login und Registrierung verlangen eine Anmeldung (`@login_required`).
Ändernde Aktionen (anlegen, buchen, löschen, Rate ändern) laufen ausschließlich über
POST-Formulare mit CSRF-Token. Rückmeldungen erscheinen als farbige Hinweise oben auf der
Seite (Django messages).

### 7.4 Verwendete Pakete

| Paket | Zweck |
|---|---|
| Django 6 | Webframework, Nutzerverwaltung, Datenbankzugriff |
| gunicorn | Produktions-Webserver |
| whitenoise | liefert statische Dateien (CSS des Admins) ohne extra Webserver |
| dj-database-url | liest `DATABASE_URL` |
| psycopg | PostgreSQL-Treiber; wird auch bei SQLite installiert, weil ältere Migrationen ihn importieren |

---

## 8. Entwicklung

```bash
start dev                        # Entwicklungsserver, lädt bei Codeänderungen neu
start test                       # alle Tests
start test members.tests.CalculationTests   # nur eine Testklasse
start makemigrations             # nach Änderungen an models.py
start migrate                    # Schema anwenden
start shell                      # Django-Shell
start createsuperuser            # Admin-Konto, danach /admin/
```

Die Tests in `members/tests.py` decken ab: Monatsrechnung mit Ratenänderung, Überschreiben
der Rate im selben Monat, Kontostand mit Buchungen, Registrierung, den kompletten
Dashboard-Ablauf (anlegen, ändern, buchen, löschen), Fehlermeldungen bei ungültigen
Eingaben, die Trennung der Daten zwischen Nutzern, Passwort-Anfragen, Online-Status und
die Zugriffsbeschränkung des Adminboards. Sie laufen in einer temporären
SQLite-Datenbank und berühren keine echten Daten.

Migration `0008` hat das frühere Postgres-spezifische `ArrayField` durch ein `JSONField`
ersetzt, damit die App mit SQLite und PostgreSQL läuft; vorhandene Daten werden dabei
übernommen. Die Migrationen `0001` bis `0007` dürfen nicht verändert werden, weil
bestehende Datenbanken (z. B. auf fly.io) darauf aufbauen.

---

## 9. Fehlerbehebung

**`start: Befehl nicht gefunden`.** `./start.sh install-command` ausführen und ein neues
Terminal öffnen. Prüfen, dass `~/.local/bin` im `PATH` liegt (`echo $PATH`).

**Es erscheint keine öffentliche Adresse.** Der Tunnel braucht Internet. Prüfe
`.tools/tunnel.log`. Steht in `.env` `TUNNEL=off`, wird kein Tunnel gestartet. Die
Adresse ist erst 5 bis 20 Sekunden nach dem Start weltweit erreichbar; das Skript wartet
darauf, bevor es sie anzeigt.

**„Port 8000 ist schon belegt“.** `start` läuft bereits in einem anderen Terminal oder als
Dienst. Dort mit `Strg+C` beenden bzw. `sudo systemctl stop financial-planer`, oder einen
anderen Port nehmen: `BIND=0.0.0.0:8010 start`.

**Das Handy oder ein anderer Rechner erreicht die App nicht.** Läuft `start` (nicht
`start dev`)? Ist der Port in der Firewall offen (`sudo ufw allow 8000/tcp`)? Sind beide
Geräte im selben Netz? Gäste-WLANs trennen Geräte oft voneinander.

**„Verboten (403): CSRF-Verifizierung fehlgeschlagen“.** Tritt auf, wenn die App hinter
HTTPS läuft, aber `DJANGO_CSRF_TRUSTED_ORIGINS=https://deine-domain` fehlt. Eintragen und
Dienst neu starten.

**„Bad Request (400)“ bei einer Domain.** `DJANGO_ALLOWED_HOSTS` enthält die Domain nicht.
Eintragen oder leer lassen (dann sind alle Hosts erlaubt).

**Admin-Seite ohne Formatierung.** Im Produktionsbetrieb wurde `collectstatic` nicht
ausgeführt. `start` erledigt das automatisch; bei manueller Ausführung
`./start.sh collectstatic --noinput`.

**Port 8000 ist belegt.** In `.env` `BIND=0.0.0.0:8080` setzen oder
`./start.sh server 0.0.0.0:8080`.

**Passwort vergessen.** Der Nutzer stellt auf der Login-Seite eine Anfrage; der Admin
setzt im Adminboard ein neues Passwort. Hat der Admin selbst sein Passwort vergessen:
`start changepassword <benutzername>` im Terminal.

**Alle Daten zurücksetzen.** Erst den laufenden `start` beenden, dann `local.sqlite3`
löschen, dann `start` (fragt erneut nach dem Admin-Konto). Die Datei niemals löschen,
während die App läuft: Der laufende Server arbeitet dann auf einer verschwundenen Datei
weiter und neue Anfragen landen in einer leeren Datenbank, was zu Fehlern beim Löschen
und Anmelden führt. Bei Docker
`docker compose down -v`.

**Datensicherung.** Die Datei `local.sqlite3` kopieren (bei laufendem Betrieb besser
`start dumpdata > backup.json`, zurückspielen mit `start loaddata backup.json`).

---

## 10. Project Description (original)

As part of the module Introduction to Python, a web-based financial planning system will be developed that enables users to manage their monthly finances in a structured and transparent way. The objective of the project is to design an application that allows personal income, expenses, and budgets to be recorded, managed, and analyzed in a clear and organized manner. The focus lies both on the proper modeling of financial data and on the technical implementation of a user-specific web application.

The application allows registered users to store fixed monthly income such as salaries or other regular sources of income. In addition, monthly expenses can be recorded, for example for rent, groceries, insurance, or transportation. These income and expense entries are assigned to different categories in order to ensure a clear structure and improved analyzability. Based on this data, a monthly overview is generated that transparently displays total income, total expenses, and the available balance.

A central feature of the application is the use of so-called contingents or budget pots. These enable users to define monthly budget amounts for specific purposes, such as a car, vacation, or leisure activities. Regular deposits can be made into these budget pots, while withdrawals are also possible, for example in the case of unexpected expenses such as repairs. The current balance of each budget pot is continuously calculated and visualized, allowing users to see at any time how much money is still available.

The monthly budget amounts as well as individual deposits and withdrawals can be adjusted flexibly. Changes to these values are dynamically reflected in all relevant calculations, while the consistency of the stored data is maintained at all times. This also allows different financial scenarios to be modeled and analyzed.

The application is implemented as a web application with user registration and login functionality, enabling multiple users to manage their finances independently from one another. The backend of the application is implemented in Python and uses a relational database for persistent storage of user data. The goal of the project is to practically apply and deepen fundamental concepts of software development with Python, in particular data modeling, web development, and secure user management.
