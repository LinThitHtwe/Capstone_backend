"""Send reservation confirmation OTP by email."""

import logging
import secrets
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .constants import (
    LIBRARY_RESERVATION_TZ,
    NOSHOW_BOOKING_COOLDOWN_SECONDS,
    WEIGHT_TABLE_OTP_GRACE_SECONDS,
)

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


def send_reservation_noshow_timeout_email(user, reservation) -> None:
    """
    Notify the user that their sensor-table booking was voided after no OTP
    within ``WEIGHT_TABLE_OTP_GRACE_SECONDS`` of ``created_at``.

    Does not raise on send failure (booking is already cancelled in the DB);
    logs the error instead.
    """
    to_addr = (getattr(user, "email", None) or "").strip()
    if not to_addr:
        logger.warning(
            "Skipping noshow-timeout email: user id=%s has no email (reservation id=%s)",
            getattr(user, "pk", None),
            getattr(reservation, "pk", None),
        )
        return

    tz = ZoneInfo(LIBRARY_RESERVATION_TZ)
    start_local = reservation.start_time.astimezone(tz)
    end_local = reservation.end_time.astimezone(tz)
    table = reservation.table
    table_num = table.table_number
    grace = WEIGHT_TABLE_OTP_GRACE_SECONDS
    # ASCII subject avoids rare SMTP issues with Unicode punctuation.
    subject = f"Reservation cancelled - table #{table_num} (no check-in within {grace}s)"
    _fmt = "%Y-%m-%d %H:%M"
    time_range = (
        f"{start_local.strftime(_fmt)} to {end_local.strftime('%H:%M')}"
    )
    cool = NOSHOW_BOOKING_COOLDOWN_SECONDS
    ctx = {
        "table_number": table_num,
        "time_range": time_range,
        "grace_seconds": grace,
        "booking_cooldown_seconds": cool,
    }
    plain_body = (
        f"Your library table reservation was cancelled.\n\n"
        f"We did not receive your OTP at the sensor table within {grace} seconds "
        f"of confirming this booking. The table is released for other users.\n\n"
        f"No-show penalty: you cannot make a new reservation for {cool} seconds from "
        f"the time of this cancellation.\n\n"
        f"Table: {table_num}\n"
        f"Scheduled time: {time_range}\n\n"
        f"After the cool-down you may book again if slots are available.\n"
    )
    html_body = render_to_string("emails/reservation_noshow_cancelled.html", ctx)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_addr],
    )
    msg.attach_alternative(html_body, "text/html")
    logger.info(
        "Sending noshow-timeout cancellation email (backend=%s) to=%s reservation id=%s",
        getattr(settings, "EMAIL_BACKEND", ""),
        to_addr,
        getattr(reservation, "pk", None),
    )
    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send noshow-timeout cancellation email to %s (reservation id=%s). "
            "Check EMAIL_BACKEND / SMTP settings in .env.",
            to_addr,
            getattr(reservation, "pk", None),
        )
        return
    if "console" in (settings.EMAIL_BACKEND or "").lower():
        logger.info(
            "Noshow cancellation email: console backend; the full message was printed "
            "in the server terminal. Recipient: %s",
            to_addr,
        )
    else:
        logger.info(
            "Noshow-timeout cancellation email sent to %s (reservation id=%s)",
            to_addr,
            getattr(reservation, "pk", None),
        )
