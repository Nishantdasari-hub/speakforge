from fastapi_mail import FastMail, MessageSchema
from pydantic import EmailStr
from app.email_id import conf
from app.config import BACKEND_URL


# ===============================
# EMAIL VERIFICATION
# ===============================

async def send_verification_email(email: EmailStr, token: str):
    if not conf:
        print("Email not configured - skipping verification email")
        return

    verification_link = f"{BACKEND_URL}/auth/verify-email?token={token}"

    message = MessageSchema(
        subject="Verify your SpeakForge account",
        recipients=[email],
        body=f"""
Welcome to SpeakForge!

Please verify your email by clicking the link below:

{verification_link}

If you did not create this account, please ignore this email.

SpeakForge Team
""",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# ===============================
# RESET PASSWORD EMAIL
# ===============================

async def send_reset_password_email(email: EmailStr, reset_link: str):
    if not conf:
        print("Email not configured - skipping password reset email")
        return

    message = MessageSchema(
        subject="SpeakForge Password Reset",
        recipients=[email],
        body=f"""
Hello,

You requested to reset your password.

Click the link below to reset it:

{reset_link}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

SpeakForge Team
""",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)