import os

from fastapi_mail import ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

MAIL_ENABLED = bool(os.getenv("MAIL_USERNAME") and os.getenv("MAIL_SERVER"))

conf = None

if MAIL_ENABLED:
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", "noreply@example.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
        USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True").lower() == "true"
    )
