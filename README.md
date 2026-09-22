# RemindGrid

RemindGrid is a subscription tracking web app. It solves one specific problem: most people don't actually know what they're paying for every month across all their subscriptions, and they get blindsided by renewals they forgot about.

Unlike a generic reminder app, RemindGrid holds structured data on every subscription (cost, billing cycle, category, renewal date), so it can show a real dashboard: total monthly spend, total yearly spend, spend broken down by category, and upcoming renewals sorted soonest-first. Renewal dates roll themselves forward automatically once they pass.

**Live app:** https://remind-grid.vercel.app

## Tech stack

**Backend**
- Django + Django REST Framework
- PostgreSQL
- JWT authentication (`rest_framework_simplejwt`), email as the login identifier
- Celery + Redis for background jobs (renewal rollover, reminder emails, monthly summaries)
- Celery Beat for scheduling
- Brevo (SMTP) for transactional email
- drf-spectacular for API docs

**Frontend**
- Next.js (App Router) + React
- Tailwind CSS + shadcn/ui
- JWT-based auth with automatic token refresh

## Features

- Email/password registration with email verification
- Login with JWT access + refresh tokens, automatic refresh on expiry
- Password reset via one-time code sent by email
- Account lockout after repeated failed logins
- Profile view/edit (display name)
- Add, edit, and delete subscriptions (name, cost, currency, category, billing cycle, renewal date)
- Dashboard: monthly/yearly spend totals, spend by category, upcoming renewals, trend vs. last month
- Automated emails: renewal reminders, monthly spend summaries, login notifications, account lock alerts — all branded HTML templates

## API endpoints

Interactive docs: `/api/docs/` (Swagger) and `/api/redoc/`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create an account |
| POST | `/api/verify-email/` | Verify email via emailed token |
| POST | `/api/resend-verification/` | Resend verification email |
| POST | `/api/login/` | Log in, returns access + refresh tokens |
| POST | `/api/logout/` | Log out (blacklists refresh token) |
| POST | `/api/forgot-password/` | Request a password reset code |
| POST | `/api/reset-password/` | Confirm reset with code + new password |
| POST | `/api/token/refresh/` | Exchange a refresh token for a new access token |
| GET / PUT | `/api/profile/` | View / update the logged-in user's profile |

### Subscriptions
| Method | Endpoint | Description |
|---|---|---|
| GET / POST | `/api/subscriptions/` | List or create subscriptions (scoped to the logged-in user) |
| GET / PATCH / DELETE | `/api/subscriptions/<id>/` | Retrieve, update, or delete a single subscription |
| GET | `/api/dashboard/` | Spend summary: totals, category breakdown, upcoming renewals, trend |

All endpoints except registration, login, and password reset require a JWT `Authorization: Bearer <token>` header.

## Local development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # fill in your own values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Or with Docker (runs Django, Postgres, Redis, Celery worker, and Celery Beat together):
```bash
docker compose up --build
docker compose exec web python manage.py migrate
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL
npm run dev
```

## Environment variables

See `.env.example` in each folder for the full list. Key ones:

**Backend:** `SECRET_KEY`, `DEBUG`, `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`, `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`, `CELERY_BROKER_URL`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`

**Frontend:** `NEXT_PUBLIC_API_URL`

## License

Personal project, built as a learning exercise in Django, Celery, Docker, and full-stack deployment.
