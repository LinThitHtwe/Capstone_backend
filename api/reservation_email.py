"""Send reservation confirmation OTP by email."""

import logging
import secrets
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .constants import LIBRARY_RESERVATION_TZ

logger = logging.getLogger(__name__)

# Exclude 0, 2, 5, 8 for demo keypads / unreliable keys on those digits.
_OTP_DIGITS = "134679"


def generate_reservation_otp() -> str:
    """Return a 6-digit numeric string using only ``1``, ``3``, ``4``, ``6``, ``7``, ``9``."""
    return "".join(secrets.choice(_OTP_DIGITS) for _ in range(6))


def send_reservation_otp_email(user, reservation, otp: str) -> None:
    """
    Email the user their table reservation OTP. Raises on mail backend failure.
    """
    tz = ZoneInfo(LIBRARY_RESERVATION_TZ)
    start_local = reservation.start_time.astimezone(tz)
    end_local = reservation.end_time.astimezone(tz)
    table = reservation.table
    table_num = table.table_number
    subject = f"Your library reservation code for table {table_num}"
    _fmt = "%Y-%m-%d %H:%M"
    time_range = (
        f"{start_local.strftime(_fmt)} to {end_local.strftime('%H:%M')}"
    )
    plain_body = (
        f"Your confirmation code (OTP) is: {otp}\n\n"
        f"Table: {table_num}\n"
        f"Time: {time_range}\n"
    )
    html_body = render_to_string(
        "emails/reservation_otp.html",
        {
            "otp": otp,
            "table_number": table_num,
            "time_range": time_range,
        },
    )
    # EmailMultiAlternatives ensures a proper multipart/alternative message with
    # text/plain + text/html; many clients (Gmail, Outlook) render the HTML part.
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send reservation OTP email to %s", user.email)
        raise
    if "console" in (settings.EMAIL_BACKEND or "").lower():
        logger.info(
            "Reservation OTP: console email backend in use; the full message (including the OTP) "
            "was printed in this server process output (e.g. runserver terminal), not to an inbox. "
            "Recipient: %s",
            user.email,
        )
    else:
        logger.info("Reservation OTP email sent to %s", user.email)
