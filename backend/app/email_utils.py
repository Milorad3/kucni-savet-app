import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER or "noreply@kucnisavet.rs")

EMAIL_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_email(to_email: str, subject: str, body_text: str) -> bool:
    """
    Salje email preko SMTP-a. Ako SMTP nije podesen (nema env varijabli),
    NE baca gresku - samo preskace i loguje, da ne bi srusio ostatak aplikacije
    (npr. otvaranje glasanja mora da uspe i ako slanje email-a ne uspe).
    """
    if not EMAIL_ENABLED:
        logger.info(f"[EMAIL PRESKOCEN - SMTP nije podesen] Za: {to_email}, Naslov: {subject}")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Slanje email-a nije uspelo za {to_email}: {e}")
        return False


def notify_meeting_activated(db, meeting, building):
    """Obavestava sve vlasnike stanova u zgradi da je glasanje otvoreno."""
    from . import models  # lokalni import da izbegnemo kruzne zavisnosti

    apartments = db.query(models.Apartment).filter(
        models.Apartment.building_id == building.id, models.Apartment.owner_id.isnot(None)
    ).all()

    frontend_url = os.getenv("FRONTEND_URL", "")
    link_line = f"\n\nOtvorite aplikaciju da glasate: {frontend_url}/meetings/{meeting.id}" if frontend_url else ""

    for apt in apartments:
        owner = apt.owner
        if not owner:
            continue
        subject = f"Otvoreno glasanje: {meeting.title}"
        body = (
            f"Postovani/a {owner.full_name},\n\n"
            f"Glasanje za sastanak '{meeting.title}' u zgradi '{building.name}' je sada OTVORENO.\n"
            f"Datum sastanka: {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}"
            f"{link_line}\n\n"
            f"Kucni Savet Aplikacija"
        )
        send_email(owner.email, subject, body)
