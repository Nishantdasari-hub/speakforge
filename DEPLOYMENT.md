# Production Deployment

For AWS EC2, follow the complete [AWS deployment guide](docs/AWS_DEPLOYMENT.md).

## Required secrets

Copy `.env.example` to `.env`, set strong unique values for `SECRET_KEY`, `ADMIN_SECRET_KEY`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD`, then set the public frontend and backend URLs. Do not commit `.env`.

## New installation

```powershell
docker compose up -d --build
```

The backend container waits for MySQL, applies the Alembic migrations, and starts Gunicorn with Uvicorn workers. The frontend is served by Nginx and uses the build-time `VITE_API_URL` value.

## Existing database

Back up the database first. If the existing schema already matches the initial migration, mark it as managed before starting the Compose backend:

```powershell
docker compose run --rm backend alembic stamp 0001_initial
docker compose up -d --build
```

For a new database, use the normal `docker compose up -d --build` command.

## Operations

- API readiness: `GET /health` checks both application and database availability.
- Logs: `docker compose logs -f backend`.
- Stop services: `docker compose down`.
- Persistent data is stored in the `mysql_data` and `uploads` volumes.
- Put TLS termination and a domain certificate in front of the frontend and API in the hosting environment.

## Important production requirements

- Provide SMTP variables or email verification and password reset delivery will not work.
- Store uploads in durable/object storage for multi-instance deployments; the included volume is suitable for a single host.
- Configure backups, monitoring, TLS, firewall rules, and secret storage through the hosting provider.