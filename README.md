
# MEDORICA-ERP-BACKEND

## Project Overview

**Medorica ERP Backend** is a robust backend system for Medorica ERP, built with FastAPI and PostgreSQL. It powers the ERP platform for medical representatives, area sales managers, and other stakeholders.

## Tech Stack

- **Python 3.10+**
- **FastAPI** (API framework)
- **PostgreSQL** (Database)
- **SQLAlchemy** (ORM)
- **Uvicorn** (ASGI server)
- **psycopg2-binary** (PostgreSQL driver)
- **python-dotenv** (Environment management)
- **python-multipart**, **Pillow**, **pypdf** (File handling)

## Features

- User authentication & onboarding
- Appointment scheduling
- Attendance tracking
- Chemist shop & doctor network management
- Gift inventory & application
- Monthly planning & target tracking
- Order management
- Salary slip generation
- Team management
- Visual ads management
- App update notifications

## Project Structure

```mermaid
graph TD
	A[MEDORICA-ERP-BACKEND]
	A --> B[db.py]
	A --> C[main.py]
	A --> D[README.md]
	A --> E[requirements.txt]
	A --> F[models]
	F --> F1[about_us]
	F --> F2[appointment]
	F --> F3[attendance]
	F --> F4[chemist_shop]
	F --> F5[distributor]
	F --> F6[doctor_network]
	F --> F7[gift]
	F --> F8[monthly_plan]
	F --> F9[monthly_target]
	F --> F10[notification]
	F --> F11[onboarding]
	F --> F12[order]
	F --> F13[salary_slip]
	F --> F14[team]
	F --> F15[visual_ads]
	A --> G[routes]
	G --> G1[about_us]
	G --> G2[app_updates]
	G --> G3[appointment]
	G --> G4[attendance]
	G --> G5[chemist_shop]
	G --> G6[distributor]
	G --> G7[doctor_network]
	G --> G8[gift]
	G --> G9[monthly_plan]
	G --> G10[monthly_target]
	G --> G11[notification]
	G --> G12[onboarding]
	G --> G13[order]
	G --> G14[salary_slip]
	G --> G15[team]
	G --> G16[visual_ads]
	A --> H[services]
	H --> H1[appointment]
	H --> H2[chemist_shop]
	H --> H3[distributor]
	H --> H4[doctor_network]
	H --> H5[onboarding]
	H --> H6[order]
	H --> H7[salary_slip]
	H --> H8[visual_ads]
	A --> I[uploads]
	I --> I1[chemist_shops]
	A --> J[apk-builds]
	J --> J1[asm-app]
	J --> J2[mr-app]
	A --> K[venv]
	A --> L[__pycache__]
```

## Setup & Run Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd MEDORICA-ERP-BACKEND
```

### 2. Create virtual environment

```bash
python3 -m venv venv
```

### 3. Activate virtual environment

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create `.env` file

Create a `.env` file in the project root with the following content:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medorica_db
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
CORS_ORIGINS=*
PORT=8000
# Optional:
DATABASE_URL=postgresql+psycopg2://your_postgres_user:your_postgres_password@localhost:5432/medorica_db
```

### 6. Run backend server

Option A: Run with Python

```bash
python main.py
```

Option B: Run with Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Verify server

- Healthcheck: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 8. Stop & deactivate

- Stop server: `Ctrl + C`
- Deactivate venv:

```bash
deactivate
```

## Developer Contact

- **Name:** Rajdeep Dey
- **Email:** rajdeepdey@gmail.com
- **LinkedIn:** [linkedin.com/in/rajdeepdey](https://linkedin.com/in/rajdeepdey)
- **GitHub:** [github.com/rajdeepdey](https://github.com/rajdeepdey)

