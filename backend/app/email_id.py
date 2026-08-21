from fastapi_mail import ConnectionConfig
import os
from app.config import FRONTEND_URL

# Only configure email if environment variables are provided
if os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"):
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM", "noreply@localhost"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
        USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True").lower() == "true",
    )
else:
    conf = None