# 🏠 MietSystem — Plattform für Immobilienvermietung

**MietSystem** ist eine moderne Backend-Plattform zur Wohnraummiete in Deutschland.  
Sie unterstützt mehrere Rollen (Admin, Vermieter, Mieter) mit separaten Dashboards und einem granularen Berechtigungssystem.  
Die Anwendung bietet umfassende Funktionen für **Immobilienverwaltung, Buchungssystem, Bewertungen und Analytik**.

## ✨ Hauptfunktionen

### 🏠 Anzeigenverwaltung
- Erstellen, Bearbeiten und Löschen von Inseraten  
- Mehrsprachige Titel und Beschreibungen (DE / EN / RU)  
- Upload von Fotos (JPEG/PNG ≤ 5 MB)  
- Verwaltung der Verfügbarkeit über Kalender  
- Aktivierungsstatus der Anzeige  

### 🔍 Suche & Filter
- **FULLTEXT**-Suche in Titeln und Beschreibungen  
- Filter nach Preis, Zimmerzahl und Immobilientyp  
- Sortierung nach Beliebtheit, Preis oder Datum  
- Paginierung (20 Ergebnisse pro Seite)  
- Caching der Ergebnisse in **Redis**  

### 👥 Rollen & Berechtigungen
- **Mieter (Tenant):** Suche, Buchungen, Bewertungen  
- **Vermieter (Landlord):** Verwaltung von Inseraten & Buchungen  
- **Administrator (Admin):** Vollzugriff auf alle Module  

### 📅 Buchungssystem
- Erstellung von Buchungen mit automatischer Verfügbarkeitsprüfung  
- Preisberechnung in Echtzeit  
- Bestätigung oder Ablehnung durch Vermieter  
- Stornierung bis 48 Stunden vor Beginn  

### ⭐ Bewertungen
- Bewertungen nach abgeschlossener Buchung  
- Moderation durch Administrator  
- Durchschnittsbewertung mit Caching  
- Antworten durch Vermieter  

### 📊 Analytik
- Beliebtheitsformel: `(views × 0.3 + reviews × 0.5 + time_decay × 0.2)`  
- Nutzer-Suchhistorie & Anzeigehistorie  
- Export von Analyse-Daten als **CSV**

## 🛠 Technischer Stack

### Backend
- **Python 3.11**  
- **Django 5.0**  
- **Django REST Framework (DRF)**  
- **MySQL 8.0** (FULLTEXT, JSON, Indizes)  
- **Redis 7.0** (Caching, ElastiCache)  
- **Celery + RabbitMQ** (asynchrone Tasks)  

### Frontend (Dashboard)
- **Django Admin Panel**  
- **DRF Browsable API**  
- **Swagger / Redoc** (drf-spectacular)  
- **Mehrsprachigkeit** (DE / EN / RU)  

### Sicherheit
- **JWT-Authentifizierung** (SimpleJWT)  
- **2FA (TOTP)**  
- **Rate Limiting** (100 req/min)  
- **django-axes** (Brute-Force-Schutz)  
- **CSRF/XSS-Schutz**

## 📁 Projektstruktur

``` bash
Project_MietSystem/
├── analytics/          # Analytik und Berichte
├── bookings/           # Buchungssystem
├── core/               # Kernapp (Routing, Settings, Middleware)
├── listings/           # Immobilienanzeigen
├── locations/          # Geodaten & Karten
├── reviews/            # Bewertungen
├── users/              # Benutzerverwaltung & Rollen
├── utils/              # Hilfsfunktionen
├── templates/          # Dashboard-Templates
├── static/             # Statische Dateien
├── media/              # Mediendateien
├── tests/              # Tests
├── docs/               # Dokumentation
├── docker-compose.yml  # Docker-Konfiguration
├── Dockerfile          # Docker-Image
├── requirements.txt    # Abhängigkeiten
└── manage.py           # Django-Manage-Skript
```

## 📦 Installation (lokal)

``` bash
# Repository klonen
git clone <repository-url>
cd MietSystem

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate     # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# MySQL-Datenbank einrichten und settings.py anpassen

# Migrationen anwenden
python manage.py migrate

# Superuser anlegen
python manage.py createsuperuser

# Server starten
python manage.py runserver 8001
```

## 📡 API-Dokumentation

### Endpoints

| Endpoint          | Beschreibung                |
| ----------------- | --------------------------- |
| `/api/users/`     | Benutzerverwaltung          |
| `/api/listings/`  | Immobilienanzeigen          |
| `/api/bookings/`  | Buchungssystem              |
| `/api/reviews/`   | Bewertungen                 |
| `/api/analytics/` | Analytik                    |
| `/api/docs/`      | Swagger/Redoc-Dokumentation |
| `/admin/`         | Django Admin Panel          |

### Beispielantwort 
``` 
json
// Erfolg
{
  "data": {
    "id": 42,
    "title": "Wohnung im Zentrum von Berlin",
    "price_per_night": 89.99
  },
  "meta": {
    "total_results": 127,
    "page": 1
  }
}

// Fehler
{
  "error": {
    "code": "INVALID_DATE",
    "message": "Buchungsdaten überschneiden sich mit bestehender Buchung",
    "status": 400
  }
}
```

## 🧪 Tests

### Ausführung

``` bash
pytest                         # Alle Tests
pytest --cov=.                 # Mit Coverage
locust -f tests/locustfile.py  # Lasttests
```

### Testabdeckung

* **Ziel:** ≥ 80 %
* **Unit-Tests:** Modelle, Serializer, Permissions
* **Integrationstests:** API-Endpunkte
* **Lasttests:** bis 1000 RPS (Locust)

## 🛡 Sicherheit

### Authentifizierung

* JWT (Access + Refresh Tokens)
* HttpOnly-Cookies + CSRF-Schutz
* 2FA (TOTP)
* Passwort-Reset per E-Mail

### Schutzmechanismen

* Rate Limiting (100 req/min)
* Brute-Force-Schutz mit django-axes
* Passwort-Hashing via Argon2
* Schutz vor XSS und CSRF

### Pre-Commit-Hooks

``` bash
pre-commit install
pre-commit run --all-files
```

## 📊 Monitoring & Logging

### Sentry

* Echtzeit-Fehlerüberwachung
* Request-Tracing
* Performance-Analyse

### Logging

* Detailliertes Aktionslogging
* Fehler- und Warnmeldungen
* Automatische Logrotation

## 👥 Benutzerrollen

| Rolle                 | Berechtigungen                                                              |
|-----------------------|-----------------------------------------------------------------------------|
| Mieter (Tenant)       | Anzeigen suchen, Buchungen erstellen, Bewertungen abgeben, Profil verwalten |
| Vermieter (Landlord)  | CRUD für eigene Anzeigen, Buchungsverwaltung, Antworten auf Bewertungen,    |
|                       |   Objektanalytik                                                            |
| Administrator (Admin) | Vollzugriff, Moderation, Benutzerverwaltung, Datenexporte                   |

## 🌍 Lokalisierung

* **Sprachen:** 🇩🇪 Deutsch, 🇬🇧 Englisch, 🇷🇺 Russisch
* **Währung:** EUR (erweiterbar)
* **Geografie:** Bundesländer, Städte, Bezirke
* **Adressformat:** Straße, PLZ, Ort

## 📈 Weiterentwicklung

### Kurzfristige Ziele

* Deployment auf **AWS** (Docker/Kubernetes)
* Kartenintegration (OpenStreetMap / Google Maps)
* Messenger zwischen Mieter und Vermieter
* Push- und SMS-Benachrichtigungen
* Mehrwährungsunterstützung

### Langfristige Ziele

* Internationale Expansion
* Empfehlungssystem auf Basis von Machine Learning
* Mobile App (iOS / Android)
* Integration von Zahlungsdiensten (Stripe, PayPal)

## 📞 Kontakt

**Entwickler:** Alex Sidorenko (mailto:alexgruening@icloud.com)
*Projekt entwickelt nach modernen Best Practices der Webentwicklung.*

