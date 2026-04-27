"""Library reservation window and per-user daily cap (library-local clock)."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone as dj_tz

logger = logging.getLogger(__name__)

from .constants import (
    LIBRARY_RESERVATION_TZ,
    RESERVATION_DAY_END_HOUR,
    RESERVATION_DAY_START_HOUR,
    RESERVATION_MAX_MINUTES_PER_USER_PER_DAY,
    RESERVATION_SLOT_MINUTES,
)

UTC = ZoneInfo("UTC")
_lib_tz = ZoneInfo(LIBRARY_RESERVATION_TZ)


def library_tz():
    return _lib_tz


def library_open_close(local_day: date) -> tuple[datetime, datetime]:
    """Naive clock times 9:00–18:00 on ``local_day``, tagged with library TZ."""
    start = datetime.combine(
        local_day, time(RESERVATION_DAY_START_HOUR, 0, 0), tzinfo=_lib_tz
    )
    end = datetime.combine(
        local_day, time(RESERVATION_DAY_END_HOUR, 0, 0), tzinfo=_lib_tz
    )
    return start, end


def parse_date(s: str) -> date | None:
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def parse_hhmm(s: str) -> time | None:
    raw = (s or "").strip()
    parts = raw.split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if h < 0 or h > 23 or m < 0 or m > 59:
        return None
    return time(h, m, 0)


def combine_local(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=_lib_tz)


def is_slot_aligned(t: time) -> bool:
    return t.second == 0 and t.microsecond == 0 and t.minute % RESERVATION_SLOT_MINUTES == 0


def duration_minutes(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def local_day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """UTC range [lo, hi) covering the library calendar day ``d``."""
    lo_local = datetime.combine(d, time.min, tzinfo=_lib_tz)
    hi_local = lo_local + timedelta(days=1)
    return lo_local.astimezone(UTC), hi_local.astimezone(UTC)


def today_in_library() -> date:
    return dj_tz.now().astimezone(_lib_tz).date()


def minutes_already_booked(user_id: int, local_day: date) -> int:
    """Sum ``duration_minutes`` for active reservations whose *start* falls on that library day."""
    from .models import Reservation

    utc_lo, utc_hi = local_day_bounds_utc(local_day)
    qs = Reservation.objects.filter(
        user_id=user_id,
        is_available=True,
        start_time__gte=utc_lo,
        start_time__lt=utc_hi,
    )
    total = 0
    for row in qs.only("duration_minutes"):
        total += row.duration_minutes
    return total


def table_has_overlap(table_id: int, start: datetime, end: datetime, exclude_pk=None) -> bool:
    from .models import Reservation

    qs = Reservation.objects.filter(
        table_id=table_id,
        is_available=True,
        start_time__lt=end,
        end_time__gt=start,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def _send_noshow_timeout_emails_for_reservations(reservation_ids: list[int]) -> None:
    """
    After the voiding transaction commits: refetch rows and email each booker.
    Must not run inside the same atomic block as the updates (use on_commit).
    """
    from .models import Reservation
    from .reservation_email import send_reservation_noshow_timeout_email

    if not reservation_ids:
        return
    logger.info(
        "Noshow-timeout: sending cancellation emails for reservation id(s) %s",
        reservation_ids,
    )
    for pk in reservation_ids:
        try:
            row = Reservation.objects.select_related("user", "table").get(pk=pk)
        except Reservation.DoesNotExist:
            logger.warning(
                "Noshow-timeout email skipped: reservation id=%s not found after commit",
                pk,
            )
            continue
        addr = (row.user.email or "").strip()
        if not addr:
            logger.warning(
                "Noshow-timeout email skipped: reservation id=%s user id=%s has no email",
                pk,
                row.user_id,
            )
            continue
        send_reservation_noshow_timeout_email(row.user, row)


def expire_weight_sensor_reservations_pending_otp(now: datetime | None = None) -> int:
    """
    For tables with a weight sensor: if a reservation was created but OTP was never
    verified within ``WEIGHT_TABLE_OTP_GRACE_SECONDS`` of ``created_at``, mark the row
    inactive (``is_available=False``) and set the table back to FREE when it was RESERVED.

    Returns the number of reservations voided.
    """
    from django.db import transaction

    from .constants import (
        NOSHOW_BOOKING_COOLDOWN_SECONDS,
        TABLE_STATUS_FREE,
        TABLE_STATUS_RESERVED,
        WEIGHT_TABLE_OTP_GRACE_SECONDS,
    )
    from .models import Reservation, Table, User

    now = now or dj_tz.now()
    cutoff = now - timedelta(seconds=WEIGHT_TABLE_OTP_GRACE_SECONDS)

    with transaction.atomic():
        rows = list(
            Reservation.objects.select_related("table", "user")
            .filter(
                is_available=True,
                otp_verified_at__isnull=True,
                table__weight_sensor__isnull=False,
                created_at__lte=cutoff,
            )
        )
        if not rows:
            return 0
        table_pks = {
            r.table_id
            for r in rows
            if r.table.weight_sensor_id and r.table.status == TABLE_STATUS_RESERVED
        }
        res_pks = [r.pk for r in rows]
        Reservation.objects.filter(pk__in=res_pks).update(is_available=False)
        if table_pks:
            Table.objects.filter(
                pk__in=table_pks,
                status=TABLE_STATUS_RESERVED,
            ).update(status=TABLE_STATUS_FREE)
        block_until = now + timedelta(seconds=NOSHOW_BOOKING_COOLDOWN_SECONDS)
        for uid in {r.user_id for r in rows}:
            User.objects.filter(pk=uid).update(
                reservation_booking_blocked_until=block_until
            )
        # Send only after this transaction commits (avoids rollback/silent drops and
        # matches Django mail expectations when nested in outer atomic blocks).
        pks_for_email = list(res_pks)
        transaction.on_commit(
            lambda ids=pks_for_email: _send_noshow_timeout_emails_for_reservations(ids)
        )

    return len(res_pks)
