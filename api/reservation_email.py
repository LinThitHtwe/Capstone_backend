"""Send reservation confirmation OTP by email."""

import logging
import secrets
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .constants import LIBRARY_RESERVATION_TZ

logger = logging.getLogger(__name__)


def generate_reservation_otp() -> str:
    """Return a 6-digit numeric string (e.g. ``042891``)."""
    return f"{secrets.randbelow(1_000_000):06d}"


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
        f"Time: {time_range} ({LIBRARY_RESERVATION_TZ})\n"
    )
    html_body = render_to_string(
        "emails/reservation_otp.html",
        {
            "otp": otp,
            "table_number": table_num,
            "time_range": time_range,
            "tz_label": LIBRARY_RESERVATION_TZ,
        },
    )
    try:
        send_mail(
            subject,
            plain_body,
            None,
            [user.email],
            fail_silently=False,
            html_message=html_body,
        )
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
