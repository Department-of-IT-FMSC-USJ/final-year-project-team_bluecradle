[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/n73txmTf)

---

# 🍼 BlueCradle

### A Web-Based Infant and Child Health Monitoring System for Public Healthcare Settings in Sri Lanka

> **ITC 4671 — Information Systems Development Research Project**  
> Minoli Perera (CPM 24375) · Praveen Fernando (CPM 24388)  
> Department of Information Technology, Faculty of Management Studies and Commerce  
> University of Sri Jayewardenepura · May 2026  
> Supervisor: Dr. C R Peiris

---

## 🔗 Repositories

| Repository                                                                                                 | Description                                                           |
| ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **This repo**                                                                                              | Django web application — PHM, Parent, MOH portals                     |
| [bluecradle-ml-system](https://github.com/MinoliPerera021126/final-year-project-team_bluecradle-ml-system) | ML pipeline — data preparation, model training, evaluation and export |

---

## 📄 Abstract

The administrative workflow of Sri Lanka's frontline Public Health Midwives (PHMs) is structurally inefficient: a single clinical measurement entered during a Maternal and Child Health clinic visit must be manually transcribed into four to five separate paper registers and state-mandated reporting forms. This duplication consumes between one and two hours of clinical time per reporting period — time that would otherwise be directed towards domiciliary care and preventative health monitoring. Existing digital health systems do not address this problem within the Sri Lankan public health context, and no purpose-built, offline-capable system exists for the PHM workflow.

This research presents BlueCradle, an offline-first Infant and Child Health Monitoring System developed using the Design Science Research (DSR) methodology. The system's primary technical contribution is the **FHBAtomicEvent architecture**: a design pattern in which each clinical action is recorded as an immutable, FHB-coded atomic event, from which Form H 523 (PHM Daily Statement) is automatically derived in under three seconds. An AI/ML malnutrition risk predictor — an LSTM and Feedforward hybrid model — analyses longitudinal infant growth sequences to classify risk as Normal, MAM, or SAM. A dual-role RAG chatbot, powered by the Google Gemini API and grounded in a ChromaDB vector store, delivers clinical decision support in English for PHMs and localized health literacy guidance in Sinhala and Tamil for parents.

**Keywords:** Public Health Midwife, Progressive Web Application, Offline-First Architecture, Design Science Research, Malnutrition Prediction, LSTM, Retrieval-Augmented Generation, Family Health Bureau, Sri Lanka

---

## 🔬 Research Problem

The core problem this research addresses is not simply the absence of a digital system, but the **structural inefficiency created by the manual separation of clinical data entry from administrative reporting**. A PHM entering a single weight measurement into the CHDR must subsequently reproduce that data point in four to five different physical registers before the working day is complete.

This primary inefficiency is compounded by three further constraints:

1. **Infrastructure** — Field operations in divisions such as Deraniyagala experience persistent mobile network failures, making conventional cloud-dependent digital systems unworkable.
2. **Household exclusion** — The clinical communication loop excludes fathers almost entirely. In households where fathers exercise significant decision-making authority over nutrition and healthcare, this exclusion directly undermines the effectiveness of clinical interventions.
3. **Non-compliance** — Informal use of messaging platforms for appointment reminders has created a pattern of non-compliance, with parents exploiting the informal nature of the channel to avoid accountability for missed vaccination appointments.
   These constraints were identified through multi-modal stakeholder interviews with Medical Officers of Health, PHMs, and parents across six MOH divisions: Avissawella, Deraniyagala, Kurunegala, Thalathuoya, Bowatta, and Anuradhapura.

---

## 🎯 Research Objectives

1. **To develop an offline-first clinic management and automated reporting platform** that enables PHMs to conduct clinic sessions without network connectivity and automatically generates Form H 523 from logged clinical data, eliminating manual transcription.
2. **To engineer an AI/ML-powered malnutrition risk predictor** that analyses infant growth trajectories to provide PHMs with early-warning risk classification for Severe and Moderate Acute Malnutrition (SAM/MAM).
3. **To design a shared-access parental engagement portal** that provides both parents with access to their infant's growth data, automated in-app vaccination reminders, and a localized health literacy chatbot in Sinhala and Tamil.

---

## 🏗️ Research Design

This study adopts the **Design Science Research (DSR)** paradigm as formalized by Hevner et al. (2004) and operationalized through the six-phase process model proposed by Peffers et al. (2007).

| DSR Phase              | BlueCradle Application                                               |
| ---------------------- | -------------------------------------------------------------------- |
| Problem Identification | Stakeholder interviews, document review of FHB H-Series forms        |
| Objectives Definition  | Functional and non-functional requirement derivation                 |
| Design and Development | Modular Django system, PWA offline layer, ML pipeline, RAG chatbot   |
| Demonstration          | End-to-end scenario walkthroughs with simulated PHM and parent users |
| Evaluation             | FR coverage matrix, ML model metrics, NFR compliance testing         |
| Communication          | Design principles abstracted in Chapter 7 of the report              |

The research contributes two generalizable design principles to the IS literature:

- **Event-sourced administrative automation** for national public health reporting hierarchies
- **Role-aware, language-partitioned RAG architectures** for multilingual LMIC health systems

---

## ✨ System Features

### PHM Portal

- **Offline-first clinic management** — full functionality without network via Service Worker + IndexedDB
- **Infant registration** with automatic 20-vaccine national immunization schedule generation
- **Growth record entry** with automatic Z-score calculation (WHZ, WAZ, HAZ)
- **Immunization recording** with grace period logic (14-day for infants under 12 months, 30-day for 12 months and above) and defaulter flagging
- **H 523 report generation** — one-click PDF from FHBAtomicEvent aggregation
- **ML risk stratification** — LSTM-based SAM/MAM prediction via Celery async pipeline
- **Priority-based sync queue** — SAM/MAM alerts and vaccination records sync before routine data
- **Prepare Offline button** — caches all infant pages before clinic day

### Parent Portal

- **Read-only infant dashboard** — growth chart, vaccination timeline, clinic sessions
- **Digital CHDR** — downloadable PDF replica of the paper health booklet
- **Trilingual chatbot** — clinical guidance in English, Sinhala, and Tamil via ChromaDB RAG + Gemini 2.5 Flash
- **Push notifications** — vaccination reminders and ML risk alerts

### MOH Portal

- **Divisional dashboard** — SAM/MAM counts, vaccination coverage, PHM activity
- **Summarized PDF reports** — Division Summary, Nutritional Status, Vaccination Coverage, PHM Activity

### System-wide

- **Append-only audit trail** via Django signals — tamper-evident, cryptographically timestamped
- **Docker Compose deployment** — Nginx + Gunicorn + PostgreSQL + Redis + Celery

---

## 🏗️ System Architecture

```
Browser (PWA)                Backend                    Data & Async
─────────────               ─────────────              ──────────────
Service Worker         →    Django 6 + DRF        →    PostgreSQL 15
IndexedDB              →    Gunicorn               →    Redis 7
sync.js (priority      →    Celery Worker          →    ChromaDB
  sync queue)               Celery Beat                 ML Models
Chart.js                    Gemini 2.5 Flash
zscore.js

                    Docker Compose wraps everything
         nginx → web (gunicorn) → celery → celery-beat → db → redis
```

### Offline-First Flow

```
PHM Login (online)
    ↓
Prepare Offline → Service Worker caches all infant pages
    ↓
WiFi Off — Clinic Starts
    ↓
Growth / Immunization entry → FHBAtomicEvent queued in IndexedDB
    ↓
WiFi On — Sync fires automatically (online event listener)
    ↓
POST /api/clinic/events/ → GrowthRecord + ImmunizationEvent saved to PostgreSQL
    ↓
Celery ML task → LSTM inference → SAM/MAM/Normal → Push notification
    ↓
H 523 PDF generated from FHBAtomicEvent aggregation
```

---

## 🛠️ Tech Stack

| Layer          | Technology                                        |
| -------------- | ------------------------------------------------- |
| Backend        | Django 6.0.5, Django REST Framework               |
| Database       | PostgreSQL 15                                     |
| Async          | Celery 5.6, Redis 7                               |
| ML             | TensorFlow/Keras, scikit-learn, joblib            |
| RAG Chatbot    | ChromaDB, sentence-transformers, Gemini 2.5 Flash |
| PDF Generation | ReportLab                                         |
| Frontend       | Vanilla JavaScript, Tailwind CSS, Chart.js, idb   |
| PWA            | Service Worker, IndexedDB, Web Push API           |
| Deployment     | Docker Compose, Gunicorn, Nginx                   |

---

## ⚙️ Prerequisites

### Local Development

- Python 3.13+
- PostgreSQL 15+
- Redis (via WSL2 on Windows, or native on Linux/macOS)

### Docker Deployment

- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Docker Compose v2+

---

## 🚀 Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/final-year-project-team_bluecradle.git
cd final-year-project-team_bluecradle
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `ihms/.env` and fill in your values:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=bluecradle
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
GEMINI_API_KEY=your-gemini-api-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_ADMIN_EMAIL=admin@bluecradle.lk
TIME_ZONE=Asia/Colombo
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run database migrations

```bash
cd ihms
python manage.py migrate
```

### 6. Populate test data

```bash
python manage.py populate_db
```

### 7. Place ML model files

Copy the following files to `ihms/ml_module/models/`:

- `bluecradle_lstm_v1.keras`
- `bluecradle_scaler.pkl`
- `bluecradle_imputer.pkl`
  > These are generated by the [ML repository](https://github.com/MinoliPerera021126/final-year-project-team_bluecradle-ml-system). See the ML Model Setup section below.

### 8. Start Redis (WSL2 on Windows)

```bash
# In Ubuntu WSL2 terminal
sudo service redis-server start
```

### 9. Start all services

Open four terminals:

```bash
# Terminal 1 — Django
cd ihms && python manage.py runserver

# Terminal 2 — Celery Worker
cd ihms && celery -A ihms worker --loglevel=info -P solo

# Terminal 3 — Celery Beat
cd ihms && celery -A ihms beat --loglevel=info

# Terminal 4 — Redis (WSL2 Ubuntu)
sudo service redis-server start
```

Access the app at `http://localhost:8000`

---

## 🐳 Running with Docker

### 1. Configure Docker environment

Copy `.env.docker.example` to `.env.docker` at the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=bluecradle
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
GEMINI_API_KEY=your-gemini-api-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_ADMIN_EMAIL=admin@bluecradle.lk
TIME_ZONE=Asia/Colombo
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Build and start containers

```bash
docker compose build
docker compose up
```

### 3. Run migrations and populate data

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py populate_db
```

Access the app at `http://localhost` (served by Nginx on port 80)

### Docker Services

| Service       | Description                 | Port            |
| ------------- | --------------------------- | --------------- |
| `nginx`       | Reverse proxy, static files | 80              |
| `web`         | Django + Gunicorn           | 8000 (internal) |
| `celery`      | Async task worker           | —               |
| `celery-beat` | Scheduled tasks             | —               |
| `db`          | PostgreSQL 15               | 5432 (internal) |
| `redis`       | Message broker              | 6379 (internal) |

---

## 🤖 ML Model Setup

The ML models are maintained in a separate repository:

**[bluecradle-ml-system](https://github.com/MinoliPerera021126/final-year-project-team_bluecradle-ml-system)**

### Model Architecture

The system uses an **LSTM + Feedforward hybrid model**:

- **LSTM branch** — reads a sequence of up to 6 clinic visits (age, weight, height, MUAC, WHZ, WHZ velocity, weight delta, days since last visit)
- **Feedforward branch** — reads static infant profile (sex, birth weight, birth length)
- **Output** — Softmax over 3 classes: Normal, MAM (Moderate Acute Malnutrition), SAM (Severe Acute Malnutrition)

### Model Evaluation

| Metric           | Score |
| ---------------- | ----- |
| SAM Recall       | 0.82  |
| MAM Recall       | 0.96  |
| Weighted F1      | 0.90  |
| Overall Accuracy | 0.89  |

> SAM Recall is the primary metric — a false negative in the SAM class means a severely malnourished infant is missed, which carries direct patient safety consequences.

### Generating model artifacts

```bash
# Clone the ML repository
git clone https://github.com/MinoliPerera021126/final-year-project-team_bluecradle-ml-system.git

# Run notebooks in order
1_data_preparation.ipynb
2_model_training.ipynb
3_evaluation_and_export.ipynb

# Refit the scaler and imputer on the correct 8 sequence features
# (required to match the LSTM model input shape)
python fit_scaler.py
python fit_imputer_8.py

# Copy outputs to Django project
cp models/bluecradle_lstm_v1.keras ../ihms/ml_module/models/
cp models/bluecradle_scaler.pkl ../ihms/ml_module/models/
cp models/bluecradle_imputer.pkl ../ihms/ml_module/models/
```

> `fit_scaler.py` and `fit_imputer_8.py` refit the StandardScaler and SimpleImputer on the MAL-ED 8 sequence features to match the LSTM model's expected input shape `(None, 6, 8)`. Run these after the notebooks before copying the model artifacts.

---

## 🔑 Test Credentials

| Role            | Email                | Password        |
| --------------- | -------------------- | --------------- |
| MOH Officer     | moh@bluecradle.lk    | Bluecradle@2024 |
| PHM (Agatha)    | agatha@bluecradle.lk | Bluecradle@2024 |
| PHM (Sandya)    | sandya@bluecradle.lk | Bluecradle@2024 |
| Parent (Kumari) | kumari@bluecradle.lk | Bluecradle@2024 |
| Parent (Priya)  | priya@bluecradle.lk  | Bluecradle@2024 |

> New accounts require admin verification. Go to `/admin` and set `is_verified=True` on the PHM/MOH profile.

---

## 📁 Project Structure

```
final-year-project-team_bluecradle/
├── ihms/                          # Django project root
│   ├── ihms/                      # Project settings and URLs
│   ├── accounts_module/           # User auth, roles (PHM, Parent, MOH)
│   ├── infants_module/            # Infant model, central entity
│   ├── clinic_module/             # Core clinical module
│   │   ├── models.py              # GrowthRecord, ImmunizationEvent, FHBAtomicEvent
│   │   ├── views.py               # PHM views + API endpoints
│   │   ├── vaccination_schedule.py # National immunization schedule constants
│   │   └── reporting_utils.py     # H 523 aggregation logic
│   ├── ml_module/                 # ML inference pipeline
│   │   ├── inference.py           # LSTM feature assembly + prediction
│   │   ├── tasks.py               # Celery async task
│   │   └── models/                # Model artifacts (gitignored)
│   ├── notifications_module/      # Web Push + NotificationLog
│   ├── audit_module/              # Append-only AuditLog via signals
│   ├── chatbot_module/            # ChromaDB RAG + Gemini integration
│   ├── parent_module/             # Parent/Guardian portal
│   ├── moh_module/                # MOH Officer portal
│   ├── core_module/               # Base templates, error handlers, sw.js view
│   └── static/
│       ├── js/
│       │   ├── app.js             # Service Worker registration + push subscription
│       │   ├── db.js              # IndexedDB schema + helpers
│       │   ├── sync.js            # Priority sync queue
│       │   └── zscore.js          # WHO LMS Z-score calculator
│       └── sw/
│           └── service-worker.js  # Offline caching + background sync
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── .env.docker                    # Docker environment (gitignored)
└── requirements.txt
```

---

## 🌐 API Overview

| Endpoint                                  | Method    | Description                            |
| ----------------------------------------- | --------- | -------------------------------------- |
| `/api/infants/list/`                      | GET       | List all infants for logged-in PHM     |
| `/api/clinic/events/`                     | POST      | Sync FHBAtomicEvent from offline queue |
| `/api/clinic/infants/<phn>/growth/`       | GET, POST | Growth records                         |
| `/api/clinic/infants/<phn>/immunization/` | GET, POST | Immunization events                    |
| `/api/clinic/infants/<phn>/vaccinations/` | GET       | Scheduled vaccinations                 |
| `/api/clinic/h523/`                       | GET       | H 523 report data                      |
| `/api/notifications/`                     | GET       | Notification list                      |
| `/api/notifications/subscribe/`           | POST      | Register push subscription             |
| `/api/chatbot/phm/`                       | POST      | PHM chatbot endpoint                   |
| `/api/chatbot/parent/`                    | POST      | Parent chatbot (multilingual)          |

---

## 📄 License

This project was developed as part of ITC 4671 — Information Systems Development Research Project at the Department of Information Technology, Faculty of Management Studies and Commerce, University of Sri Jayewardenepura
