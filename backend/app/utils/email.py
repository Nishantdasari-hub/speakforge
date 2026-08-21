import os

from fastapi_mail import FastMail, MessageSchema

from app.email_id import conf, MAIL_ENABLED


async def send_verification_email(email: str, token: str):

    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    verification_link = f"{backend_url}/auth/verify-email?token={token}"

    if not MAIL_ENABLED:
        print(f"[SpeakForge] SMTP not configured. Verification link for {email}: {verification_link}")
        return

    message = MessageSchema(
        subject="Verify your SpeakForge account",
        recipients=[email],
        body=f"""
        <h2>Welcome to SpeakForge</h2>
        <p>Please click the button below to verify your email:</p>

        <a href="{verification_link}" 
        style="background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
        Verify Email
        </a>

        <p>If the button doesn't work, copy this link:</p>
        <p>{verification_link}</p>
        """,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
