# SpeakForge

AI-powered speaking and writing assessment platform for structured practice, automated evaluation, and actionable feedback.

## Product overview

SpeakForge gives learners a complete assessment workflow:

- Create an account and verify email ownership
- Take structured tests with text or audio responses
- Transcribe audio with Whisper-based speech recognition
- Estimate grammar and fluency for English practice
- Review per-answer feedback and performance reports
- Track progress through user dashboards and result history

Administrators can create tests, manage questions, review analytics, and monitor platform activity through a protected dashboard.

## Why this project

SpeakForge combines a modern assessment experience with an AI-assisted evaluation pipeline. It is designed as a practical foundation for language-learning products, interview preparation platforms, and communication-skills programs.

## Technical architecture

- **Frontend:** React 18, React Router, Vite, Tailwind CSS, Framer Motion
- **Backend:** FastAPI, SQLAlchemy, Pydantic, Gunicorn
- **Database:** MySQL with Alembic migrations
- **AI pipeline:** Faster-Whisper transcription and LanguageTool grammar analysis
- **Authentication:** JWT access tokens, bcrypt password hashing, email verification, password reset
- **Operations:** Docker Compose, Nginx frontend, Caddy HTTPS reverse proxy

## Evaluation pipeline

```text
Audio response -> upload -> Whisper transcription -> grammar analysis
               -> fluency scoring -> final score -> detailed feedback

Text response  -> validation -> grammar analysis -> writing evaluation
               -> final score -> detailed feedback
```

## Core capabilities

### Learner experience

- Secure registration and login
- Email verification and password recovery
- Text and audio test answers
- AI-generated scoring and feedback
- Detailed test reports
- Dashboard statistics and attempt history

### Administration

- Test creation and editing
- Question management
- Audio and text question types
- Platform analytics
- Role-protected administration APIs

## Repository structure

```text
backend/       FastAPI application, services, database models, migrations
frontend/      React application and user/admin interfaces
Caddyfile      HTTPS reverse-proxy configuration
.env.example   Configuration template without real secrets
docker-compose.yml  Local and single-server deployment definition
```

## Local development

### Backend

```bash
cd backend
python3.12 -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
```

Use Python 3.12. Install FFmpeg, libsndfile, and Java 21 for audio decoding and
LanguageTool, or use the Docker image which includes them.

Copy `.env.example` to `.env` at the repository root. For local development set
`ENVIRONMENT=development`, a database URL reachable from your host,
`UPLOAD_DIR=uploads`, `FRONTEND_URL=http://localhost:5173`,
`BACKEND_URL=http://localhost:8000`, `ALLOWED_ORIGINS=http://localhost:5173`,
and `VITE_API_URL=http://localhost:8000`. Set secrets and SMTP values, then run
from `backend/`:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# In a second terminal with the same environment:
python -m app.worker
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Use Node 24. Vite reads the root `.env` file. `VITE_API_URL` defaults to the local
backend in development and is required for a production build. Only `VITE_`
variables are exposed to the browser; never prefix a secret with `VITE_`.

## Production deployment

The supported deployment is a Linux server running Docker Engine and Docker
Compose. The React frontend is static; the Python API needs a persistent service,
MySQL, upload storage, and CPU/memory for speech processing.

### Configure the server

1. Point two DNS names (for example `speakforge.example.com` and
   `api.speakforge.example.com`) at the server. Allow inbound TCP 80 and 443.
2. Copy `.env.example` to `.env` and restrict access with `chmod 600 .env`.
3. Generate a separate value for each of `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`,
   `SECRET_KEY`, and `ADMIN_SECRET_KEY` using `openssl rand -hex 32`. Use hex database
   passwords because Compose embeds them in the database URL. Keep these values
   stable across restarts. Changing the MySQL environment variables does not change
   passwords in an existing database volume.
4. Set `ACME_EMAIL` to your certificate contact email. Set `FRONTEND_URL` and
   `BACKEND_URL` to the two full HTTPS URLs, without trailing slashes or paths.
   Set `ALLOWED_ORIGINS` to the exact frontend URL. Caddy uses these URLs to obtain
   certificates and route requests. Compose builds the frontend with `BACKEND_URL`.
5. Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_FROM`, `MAIL_USERNAME`,
   `MAIL_PASSWORD`, and the matching TLS settings for your SMTP provider.
   Registration requires email verification before login, so working SMTP is
   required for a usable deployment. With the current mail configuration both
   username and password must be supplied when `USE_CREDENTIALS=True`. A local
   SMTP capture fixture can use `USE_CREDENTIALS=False`; this does not validate
   delivery through your production provider.

### Build and start

From the repository root:

```bash
docker compose config --quiet
docker compose build --pull
docker compose up -d --wait --wait-timeout 300
docker compose ps
curl --fail https://api.your-domain.com/health
```

Migrations run before Gunicorn starts. Database and API health checks gate the
frontend and proxy startup. Only Caddy exposes public ports; MySQL and the API
remain on the internal Docker network. Caddy manages HTTPS certificates.

Open the frontend, register an account, follow the verification email, and log in.
Then check a text assessment and an audio assessment. For an administrator account,
use the registration form's admin option with `ADMIN_SECRET_KEY`.

The worker processes one answer at a time. Measure memory use and queue latency
with your expected audio lengths before choosing server capacity or increasing traffic.

The first assessment may take longer: Faster-Whisper downloads its base model,
and LanguageTool downloads its pinned 6.6 Java distribution on first evaluation. Allow
outbound HTTPS for those downloads. Their cache persists in the `ai_cache` volume.
Scoring jobs persist in MySQL and run in the separate `worker` container. A failed
job is tried at most three times and then shown as failed with an explicit retry
button; dependency failures never produce fabricated scores. After an interrupted
worker, a processing lease becomes eligible for recovery after 10 minutes.
A stale worker cannot overwrite a recovered job. `/health` checks API/database
readiness; the worker has its own health check. Neither certifies SMTP delivery.
The supported API configuration uses one worker and per-process authentication
rate limits. Configure shared rate-limit storage before scaling API workers.
Caddy is the only public service; the API trusts its forwarded client address.
Do not publish the API port directly with this configuration.

### Updates and storage

Back up MySQL and uploaded audio before updating. Then rebuild and run
`docker compose up -d --wait --wait-timeout 300`; migrations apply automatically.
Inspect failures with `docker compose logs --tail=100 backend proxy`.
`docker compose down` stops the stack while preserving named volumes.
`docker compose down -v` deletes database, uploads, caches, and certificate state.

For a separate static frontend host, set its root directory to `frontend`, install
with `npm ci`, build with `npm run build`, publish `dist`, and configure an SPA
fallback to `index.html`. Supply `VITE_API_URL` as a build environment variable and
include the hosted frontend URL in the backend's `ALLOWED_ORIGINS` and
`FRONTEND_URL`. Rebuild the frontend whenever its API URL changes.

## Scoring and attempts

Scores are **practice estimates out of 10**, identified as `practice-v1`. They are
not calibrated IELTS/CEFR bands. Grammar starts at 10 and subtracts 20 times the LanguageTool error-to-word ratio,
clamped to 0–10 and rounded.
Speaking fluency estimates length and pace; writing fluency estimates length and
sentence structure. Short responses are capped; silence receives a completed zero
score. Relevance, factual correctness, pronunciation, and accent fairness are not
measured. Do not use these scores for high-stakes decisions without a validated
rubric and a representative speech evaluation dataset.

Each test start creates or resumes a draft attempt. Answer uploads are idempotent
within that attempt. Submit requires every question, queues scoring exactly once,
and freezes the attempt. Retakes create new reports. Report, dashboard and history
use the same average and count completed attempts, including zero scores. Test
content with existing attempts is immutable; create a new test to change it.
Audio uploads are capped at 10 MB and the question duration plus five seconds
(up to 300 seconds), and decoded before accepting them. Text is capped at 10,000
characters. The browser timer is a practice guide, not a secure exam timer.

Migration `0002_attempt_scoring` preserves old answer rows. Since historical
answers had no attempt identifiers, each old answer becomes a separate legacy
attempt; original test-attempt groupings cannot be reconstructed. Back up before
migrating. Previously issued access tokens need a fresh login, and old password
reset links should be requested again after upgrading token handling.

## Quality checks

```bash
cd frontend
npm run lint
npm run build # requires VITE_API_URL in root .env or the build environment
```

```bash
cd backend
python -m py_compile app/*.py app/routes/*.py app/services/*.py app/utils/*.py
python -m unittest discover -s tests -v
```

## API highlights

- `POST /auth/register` - Register a user
- `POST /auth/login` - Authenticate and receive a JWT
- `GET /tests/` - List available tests
- `GET /tests/{id}/questions` - Load test questions
- `POST /tests/{id}/start` - Create/resume a draft attempt
- `POST /tests/submit-answer/{question_id}` - Save an answer with multipart `attempt_id`
- `POST /tests/{id}/submit?attempt_id={attempt_id}` - Queue a completed attempt
- `GET /tests/report/{id}?attempt_id={attempt_id}` - Retrieve an attempt report
- `POST /tests/attempts/{attempt_id}/retry` - Retry failed evaluation
- `POST /auth/resend-verification` - Resend an account verification email
- `GET /health` - Check API and database readiness

## Security and privacy

Secrets are supplied through environment variables and are excluded from version control. Production deployments should use HTTPS, restricted firewall rules, managed secrets, database backups, and durable storage for uploaded audio.

## Project status

SpeakForge is an actively developed portfolio and product prototype demonstrating full-stack application design, AI-assisted evaluation, role-based workflows, and production-oriented deployment practices.

## License

This project is licensed under the MIT License.
