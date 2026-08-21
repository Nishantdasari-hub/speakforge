# Production Deployment

SpeakForge is packaged for a single-server Docker deployment on AWS EC2 or another Linux host.

## Quick start

```powershell
cp .env.example .env
# Set real production secrets and domains in .env
docker compose up -d --build
```

The stack starts MySQL, applies Alembic migrations, runs FastAPI with Gunicorn, serves React with Nginx, and provides HTTPS through Caddy.

## Verification

```bash
docker compose ps
curl https://api.your-domain.com/health
```

Do not expose MySQL or the backend port directly to the public internet.

## Important production requirements

- Provide SMTP variables or email verification and password reset delivery will not work.
- Store uploads in durable/object storage for multi-instance deployments; the included volume is suitable for a single host.
- Configure backups, monitoring, TLS, firewall rules, and secret storage through the hosting provider.