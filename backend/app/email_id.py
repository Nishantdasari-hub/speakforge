import os
from fastapi_mail import ConnectionConfig
from app import config  # Load the root .env before reading SMTP settings.

use_credentials = os.getenv("USE_CREDENTIALS", "True").lower() == "true"
configured = bool(os.getenv("MAIL_SERVER") and os.getenv("MAIL_FROM"))
if use_credentials:
    configured = configured and bool(os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"))
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=use_credentials,
    TIMEOUT=15,
) if configured else None
