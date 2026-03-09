from fastapi_mail import FastMail, MessageSchema
from app.email_id import conf

async def send_verification_email(email: str, token: str):

    verification_link = f"http://127.0.0.1:8000/verify-email?token={token}"

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