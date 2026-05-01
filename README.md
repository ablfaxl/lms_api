
# LMS App Server

[![Django](https://img.shields.io/badge/Django-5.2-092e20?logo=django)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-a30000?logo=django)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-6ba539?logo=openapi-initiative)](openapi.yaml)
[![GitHub Repo](https://img.shields.io/badge/GitHub-PsymoNiko%2Flms_api-181717?logo=github)](https://github.com/PsymoNiko/lms_api)

Backend for the LMS platform built with **Django 5.2** + **Django REST Framework** + **JWT** + **WebSockets** (Django Channels).  
Handles user management, course enrolment, messaging, notifications, and live chat.

---

## 🧱 Tech Stack

- **Django 5.2** & **Django REST Framework**
- **JWT** (`djangorestframework-simplejwt`)
- **Django Channels** (WebSocket chat + notifications)
- **PostgreSQL** (primary database)
- **S3‑compatible storage** (`django-storages` + `boto3`)
- **Docker Compose** (for local Postgres + RustFS)

---

## 🚀 Quick Start

### 1. Clone & environment
```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Start services with Docker

```bash
docker compose up -d
```

3. Run migrations

```bash
python manage.py migrate
```

4. Run the server

```bash
python manage.py runserver
```

Server will be available at http://127.0.0.1:8000

---

🧪 Seed demo data

Populate the database with rich demo users, courses, messages, grades, and newsletter entries:

```bash
python manage.py seed_lms
```

Reset and re‑seed:

```bash
python manage.py seed_lms --clear
```

All seeded users have the password: seedpass123

---

📚 API Documentation

The full REST API is described in openapi.yaml (OpenAPI 3.0).
All routes are prefixed with /api/v1/.

🔓 Public endpoints

· GET    /courses/ – list courses
· GET    /courses/{id}/ – course outline (anonymous access)
· GET    /stats/ – platform statistics
· POST   /newsletter/ – subscribe to newsletter
· POST   /login/ – obtain JWT pair
· POST   /register/ – new user registration
· POST   /auth/register/ (alias)
· POST   /refresh-token/ – refresh access token

🔐 Authenticated endpoints

· GET    /me/ – current user profile + role flags
· GET    /admin/overview/ – platform admin overview
· GET    /enrollments/ – my enrolled courses
· POST   /courses/{id}/enroll/ – enrol into a course
· GET    /messages/conversations/ – list my conversations
· GET    /notifications/ – unread notifications

💬 WebSocket chat

Endpoint: ws://127.0.0.1:8000/ws/chat/?token=<your_jwt_access_token>

Supports:

· sending / receiving messages
· typing indicators
· read receipts
· real‑time notification pushes

---

👥 Roles

· student – can browse courses, enrol, participate in chat
· instructor – can manage their courses (admin UI / future endpoints)
· admin – full platform oversight (e.g. /admin/overview/)

Check GET /api/v1/me/ for frontend feature gating.

---

⚠️ Important notes

· core/settings.py currently uses development defaults (DEBUG=True, hardcoded DB credentials).
    Switch to environment variables before production!
· Channel layer is in‑memory. Use Redis for production.
· Browsable API is enabled only when DEBUG=True.

---

📁 Documentation

Detailed contracts and checklists are in the docs/ folder:

· backend-api-contract-fa.md
· lms-api-contract.md
· frontend-websocket-chat-fa.md
· server-api-checklist.md



!