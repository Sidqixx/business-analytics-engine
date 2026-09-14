"""
Email Delivery
--------------
Sends business analytics notifications via SMTP.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================

ENV_FILE = (
    Path(__file__).resolve().parents[2]
    / ".env"
)

load_dotenv(ENV_FILE)

ENABLE_EMAIL = (
    os.getenv("ENABLE_EMAIL", "true").lower()
    == "true"
)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    subject: str,
    body: str,
    recipient: str,
    attachment_path: str | Path | None = None,
) -> None:
    """
    Send a plain-text email through SMTP,
    optionally with a file attachment.
    """

    if not SMTP_USERNAME:
        raise ValueError(
            "SMTP_USERNAME environment variable is not set."
        )

    if not SMTP_PASSWORD:
        raise ValueError(
            "SMTP_PASSWORD environment variable is not set."
        )

    target_recipient = recipient

    if not recipient:
        raise ValueError(
            "Recipient email address is required."
        )

    message = EmailMessage()

    message["From"] = SMTP_USERNAME
    message["To"] = target_recipient
    message["Subject"] = subject

    message.set_content(body)

    # --------------------------------------------------------
    # ATTACHMENT
    # --------------------------------------------------------

    if attachment_path is not None:

        attachment = Path(attachment_path)

        if not attachment.exists():
            raise FileNotFoundError(
                f"Attachment not found: {attachment}"
            )

        with open(attachment, "rb") as file:
            file_data = file.read()

        message.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=attachment.name,
        )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
    ) as server:

        server.starttls()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )

        server.send_message(message)

# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    report_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "generated"
        / "business_report.md"
    )

    send_email(
        subject="Business Analytics Automation - Report Test",
        body=(
            "This is a test email from the "
            "Business Analytics Automation project.\n\n"
            "The business report is attached."
        ),
        attachment_path=report_path,
    )

    print(
        "Test email with attachment sent successfully."
    )