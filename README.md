# SpeakForge

AI-powered speaking and writing assessment platform for structured practice, automated evaluation, and actionable feedback.

## Product overview

SpeakForge gives learners a complete assessment workflow:

- Create an account and verify email ownership
- Take structured tests with text or audio responses
- Transcribe audio with Whisper-based speech recognition
- Evaluate grammar, fluency, vocabulary, and response quality
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
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the repository root and set local values. Then run:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend API URL is configured with `VITE_API_URL`. It defaults to the local backend for development.

## Production deployment

The repository includes Docker-based deployment assets for AWS EC2 and other Linux servers:

```bash
docker compose up -d --build
```

Set real secrets, domains, SMTP credentials, and `VITE_API_URL` before deployment. See the deployment configuration files in the repository for the operational setup.

## Quality checks

```bash
cd frontend
npm run lint
npm run build
```

```bash
cd backend
python -m py_compile app/*.py app/routes/*.py app/services/*.py app/utils/*.py
```

## API highlights

- `POST /auth/register` - Register a user
- `POST /auth/login` - Authenticate and receive a JWT
- `GET /tests/` - List available tests
- `GET /tests/{id}/questions` - Load test questions
- `POST /tests/submit-answer/{question_id}` - Submit an answer
- `POST /tests/{id}/submit` - Submit a completed test
- `GET /tests/report/{id}` - Retrieve an evaluation report
- `GET /health` - Check API and database readiness

## Security and privacy

Secrets are supplied through environment variables and are excluded from version control. Production deployments should use HTTPS, restricted firewall rules, managed secrets, database backups, and durable storage for uploaded audio.

## Project status

SpeakForge is an actively developed portfolio and product prototype demonstrating full-stack application design, AI-assisted evaluation, role-based workflows, and production-oriented deployment practices.

## License

This project is licensed under the MIT License.
