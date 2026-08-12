# 🔐 Phishing Simulation & Security Awareness Platform

A web-based platform for running internal phishing simulations to measure and improve employee cybersecurity awareness. Generate campaigns, track click rates, and produce management-ready PDF/Word reports.

---

## ✨ Features

- **Campaign Management** — Create and schedule phishing simulation campaigns
- **Automated Scheduling** — APScheduler sends simulated emails at defined intervals
- **Target Management** — Import recipient lists via CSV upload
- **Analytics** — Track open rates, click rates, and awareness trends
- **PDF Reports** — One-click professional PDF reports via ReportLab
- **Word Reports** — Export DOCX reports for management presentations
- **Modern Admin UI** — Clean dashboard powered by django-unfold

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Django 5, Django REST Framework |
| Scheduler | APScheduler 3.x |
| PDF Reports | ReportLab |
| Word Reports | python-docx |
| Admin UI | django-unfold |
| Database | SQLite (dev) → PostgreSQL (prod) |

---

## 🚀 Quick Start

```bash
git clone https://github.com/ahmed-atiah/phishing-simulation-platform.git
cd phishing-simulation-platform/core

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in your own values
cp .env.example .env

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Open → `http://localhost:8000/admin/`

---

## 📋 Usage

1. Login to the admin dashboard
2. **Create targets** — manually or import via CSV
3. **Create a campaign** — set name, template, schedule, and target list
4. **Monitor results** — view click rates and awareness metrics in real time
5. **Generate report** — export PDF or DOCX for management

---

## ⚠️ Legal Notice

This tool is designed for **authorized internal security testing only**. Always obtain written permission before running phishing simulations. Unauthorized use is illegal and unethical.

---

Built by [Ahmed Atiah](https://github.com/ahmed-atiah)
