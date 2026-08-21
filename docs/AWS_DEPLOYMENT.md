# SpeakForge on AWS EC2

This guide deploys the current SpeakForge repository on one AWS EC2 server using Docker Compose. It includes MySQL, the FastAPI backend, the React frontend, Alembic migrations, persistent uploads, and automatic HTTPS through Caddy.

## What you will create

- One Ubuntu EC2 instance.
- One Elastic IP address.
- Two DNS records: `app.your-domain.com` and `api.your-domain.com`.
- Docker containers for MySQL, backend, frontend, and HTTPS proxy.

This is a simple single-server deployment. It is suitable for a first production release. For high availability later, move MySQL to Amazon RDS and uploads to Amazon S3.

## Before starting

You need:

- An AWS account.
- A domain name that you control.
- The SpeakForge project pushed to GitHub, GitLab, or another Git server.
- SMTP credentials if registration verification and password reset emails must work.

## 1. Create the EC2 server

1. Open AWS Console and select the region you want.
2. Open **EC2**, choose **Launch instance**.
3. Use these values:
   - Name: `speakforge-production`
   - AMI: Ubuntu Server 24.04 LTS
   - Instance type: at least `t3.medium`; use a larger instance if Whisper AI is heavily used
   - Storage: at least 30 GB gp3; use more for AI models and uploads
   - Create or select an SSH key pair and download the `.pem` file
4. Create a security group with these inbound rules:
   - SSH TCP 22: **your own IP address only**
   - HTTP TCP 80: `0.0.0.0/0`
   - HTTPS TCP 443: `0.0.0.0/0`
5. Do not open ports `3306`, `8000`, or `8080` to the internet.
6. Launch the instance.
7. Allocate an **Elastic IP** and associate it with this instance. Use this IP in DNS.

## 2. Connect to Ubuntu

From PowerShell on your Windows computer, replace the key path and public IP:

```powershell
ssh -i C:\path\to\speakforge.pem ubuntu@YOUR_ELASTIC_IP
```

On the server, update packages and install Git and Docker:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
exit
```

Reconnect using the same SSH command so the Docker group takes effect.

## 3. Download the project

On the EC2 server:

```bash
git clone YOUR_REPOSITORY_URL speakforge
cd speakforge
```

Replace `YOUR_REPOSITORY_URL` with the repository URL. Do not upload your local `.env` to Git.

## 4. Configure DNS

In your domain provider or Route 53, create these **A records** pointing to `YOUR_ELASTIC_IP`:

```text
app.your-domain.com  -> YOUR_ELASTIC_IP
api.your-domain.com  -> YOUR_ELASTIC_IP
```

Wait until both records resolve. On your computer, you can check with:

```powershell
nslookup app.your-domain.com
nslookup api.your-domain.com
```

## 5. Configure production environment

On the EC2 server:

```bash
cp .env.example .env
nano .env
```

Set real values. Example:

```env
ENVIRONMENT=production
MYSQL_PASSWORD=CREATE_A_LONG_RANDOM_PASSWORD
MYSQL_ROOT_PASSWORD=CREATE_A_DIFFERENT_LONG_RANDOM_PASSWORD
VITE_API_URL=https://api.your-domain.com
DATABASE_URL=mysql+pymysql://speakforge:CREATE_A_LONG_RANDOM_PASSWORD@db:3306/speakforge
SECRET_KEY=CREATE_A_LONG_RANDOM_SECRET
ADMIN_SECRET_KEY=CREATE_A_DIFFERENT_ADMIN_SECRET
FRONTEND_URL=https://app.your-domain.com
BACKEND_URL=https://api.your-domain.com
ALLOWED_ORIGINS=https://app.your-domain.com
UPLOAD_DIR=/data/uploads
```

For passwords and secrets, generate values on the server:

```bash
openssl rand -hex 32
```

Set the SMTP values in the same file if email is required:

```env
MAIL_USERNAME=your-smtp-username
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=noreply@your-domain.com
MAIL_PORT=587
MAIL_SERVER=smtp.your-provider.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
```

Never use the sample values from `.env.example` in production. Never commit `.env`.

## 6. Configure HTTPS proxy domains

Edit the Caddy configuration:

```bash
nano Caddyfile
```

Replace the complete file with this, using your real domains and email:

```text
{
    email admin@your-domain.com
}

app.your-domain.com {
    reverse_proxy frontend:80
}

api.your-domain.com {
    reverse_proxy backend:8000
}
```

Caddy will request and renew Let's Encrypt certificates automatically. DNS records must already point to the EC2 Elastic IP, and ports 80 and 443 must be open.

## 7. Start SpeakForge

From the project directory:

```bash
docker compose config --quiet
docker compose up -d --build
```

The startup sequence is:

1. MySQL starts and passes its healthcheck.
2. The backend runs `alembic upgrade head`.
3. Gunicorn starts the FastAPI application.
4. The frontend is built and served by Nginx.
5. Caddy exposes the frontend and API over HTTPS.

Check the containers:

```bash
docker compose ps
docker compose logs -f backend
```

The four services should be running: `db`, `backend`, `frontend`, and `proxy`.

## 8. Test the live deployment

Open this URL in a browser:

```text
https://app.your-domain.com
```

Test the API from the server:

```bash
curl https://api.your-domain.com/health
```

Expected result:

```json
{"status":"ok","service":"SpeakForge API"}
```

Then test this workflow in the browser:

1. Register a user.
2. Confirm the verification email.
3. Log in.
4. Create a test as an admin.
5. Add questions.
6. Submit a text answer.
7. Submit an audio answer if Whisper and FFmpeg are available in the image.
8. Open the report page.
9. Test password reset.

## 9. Create the first admin

The registration endpoint supports admin registration only when `ADMIN_SECRET_KEY` is supplied. Use the application registration screen or API with the admin key configured in `.env`. Do not share this key with normal users.

## Updating the application

On the EC2 server:

```bash
cd ~/speakforge
git pull
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend
```

The backend applies new Alembic migrations before Gunicorn starts.

## Backups

At minimum, create regular MySQL dumps and copy them outside the EC2 instance. Example:

```bash
mkdir -p ~/backups
docker compose exec -T db mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" speakforge > ~/backups/speakforge-$(date +%F).sql
```

For a stronger production setup, use Amazon RDS for MySQL with automated backups and Amazon S3 for uploaded audio files.

## Troubleshooting

View all logs:

```bash
docker compose logs --tail=200
```

Restart one service:

```bash
docker compose restart backend
```

If HTTPS fails, verify DNS, security group ports 80/443, and the domain names in `Caddyfile`.

If the backend repeatedly restarts, inspect its logs. Common causes are incorrect `DATABASE_URL`, weak/missing `SECRET_KEY`, invalid SMTP settings, or insufficient memory while AI dependencies initialize.

If the database is empty after a redeploy, do not run `docker compose down -v`; that command deletes named volumes. Restore a backup or check that the `mysql_data` volume still exists.

## AWS production checklist

- [ ] Elastic IP attached to EC2
- [ ] SSH restricted to your IP
- [ ] Ports 3306 and 8000 not publicly exposed
- [ ] DNS A records configured
- [ ] Real `.env` secrets configured
- [ ] `Caddyfile` uses real domains
- [ ] HTTPS works
- [ ] `/health` returns success
- [ ] Email verification tested
- [ ] Text and audio submissions tested
- [ ] Database backup tested
- [ ] CloudWatch or another monitoring system configured
- [ ] Server updates and Docker image updates scheduled
