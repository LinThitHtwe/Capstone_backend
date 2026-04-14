"""
Wipe the Django database, recreate the env-based admin, then load demo rows
that match the Next.js frontend (``SINGLE``, ``CIRCULAR``, ``FOUR_SEATS`` and
the same scatter layout as ``capstone-frontend/lib/data/admin-tables-mock.ts``).

Run (from ``capstone-backend``):

    python manage.py reload_frontend_demo

Requires ``ADMIN_EMAIL`` and ``ADMIN_PASSWORD`` in ``.env`` (same as
``ensure_capstone_admin``) so you can log into the admin UI after the wipe.
"""

import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from api.constants import (
    ROLE_LECTURER,
    ROLE_STAFF,
    ROLE_STUDENT,
    ROLE_VISITOR,
    TABLE_STATUS_FREE,
    TABLE_STATUS_OCCUPIED,
    TABLE_STATUS_RESERVED,
)
from api.models import LCDDisplay, OccupancyEvent, Reservation, Table, WeightSensor

User = get_user_model()

# Must match ``capstone-frontend/lib/data/admin-tables-mock.ts`` (tableType values).
TABLE_TYPES = ("SINGLE", "CIRCULAR", "FOUR_SEATS")

SCATTER_FLOOR_1 = (
    (40, 45),
    (200, 38),
    (380, 62),
    (560, 44),
    (740, 58),
    (90, 160),
    (320, 140),
    (520, 175),
    (720, 155),
    (55, 300),
    (280, 285),
    (510, 320),
    (700, 295),
)

SCATTER_FLOOR_2 = (
    (30, 50),
    (175, 42),
    (340, 68),
    (500, 48),
    (680, 62),
    (765, 88),
    (85, 175),
    (290, 155),
    (480, 195),
    (640, 168),
    (800, 210),
    (120, 340),
    (380, 315),
    (600, 355),
)


def _iter_mock_layout():
    """Yields (table_number, floor, position_x, position_y, table_type, is_reservable, is_available)."""
    tnum = 1
    for floor, coords in ((1, SCATTER_FLOOR_1), (2, SCATTER_FLOOR_2)):
        for i, (px, py) in enumerate(coords):
            table_type = TABLE_TYPES[(i + floor * 3) % 3]
            is_reservable = (i + floor) % 4 != 0
            is_available = (i + floor + tnum) % 13 != 0
            yield tnum, floor, px, py, table_type, bool(is_reservable), bool(is_available)
            tnum += 1


def _clear_api_tables_keep_superusers():
    """FK-safe wipe of app data (handles partial runs / flaky flush). Keeps Django superusers."""
    OccupancyEvent.objects.all().delete()
    Reservation.objects.all().delete()
    LCDDisplay.objects.all().delete()
    Table.objects.all().delete()
    WeightSensor.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()


class Command(BaseCommand):
    help = (
        "Flush ALL data, recreate admin from ADMIN_EMAIL/ADMIN_PASSWORD, then insert "
        "frontend-aligned demo tables (SINGLE/CIRCULAR/FOUR_SEATS), sensors, LCDs, "
        "occupancy events, reservations, and sample users."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-flush",
            action="store_true",
            help="Skip Django flush (still clears api rows + non-super users before seed).",
        )

    def handle(self, *args, **options):
        if not options["no_flush"]:
            self.stdout.write("Flushing all tables (Django flush)...")
            call_command("flush", interactive=False, verbosity=0)
            self.stdout.write(self.style.WARNING("All rows removed."))

        try:
            call_command("ensure_capstone_admin")
        except CommandError as exc:
            self.stdout.write(
                self.style.ERROR(
                    "Admin not created: {}. Set ADMIN_EMAIL and ADMIN_PASSWORD in .env.".format(
                        exc
                    )
                )
            )

        now = timezone.now()
        demo_password = os.environ.get("DEMO_USER_PASSWORD", "DemoUser2026!")

        role_cycle = (
            ROLE_STUDENT,
            ROLE_STUDENT,
            ROLE_LECTURER,
            ROLE_STAFF,
            ROLE_VISITOR,
        )
        first_names = (
            "Aisha",
            "Chen",
            "Priya",
            "Omar",
            "Emma",
            "Lucas",
            "Yuki",
            "Diego",
            "Fatima",
            "Noah",
            "Hana",
            "Vikram",
            "Sofia",
            "James",
            "Nurul",
            "Alex",
            "Mei",
            "Sam",
            "Zara",
            "Ryan",
            "Jordan",
            "Taylor",
            "Casey",
            "Riley",
            "Morgan",
            "Jamie",
            "Quinn",
            "Reese",
            "Blake",
            "Avery",
            "Skyler",
        )

        with transaction.atomic():
            _clear_api_tables_keep_superusers()

            demo_users = []
            for idx, name in enumerate(first_names):
                role = role_cycle[idx % len(role_cycle)]
                email_num = idx + 1
                email = "demo.user{:02d}@library.demo".format(email_num)
                u = User.objects.create_user(
                    email=email,
                    password=demo_password,
                    name="{} (Demo)".format(name),
                    role=role,
                    id_number="DEMO-{:04d}".format(email_num),
                )
                demo_users.append(u)

            sensors = []
            tables_by_number = {}
            layout_rows = list(_iter_mock_layout())
            for tnum, floor, px, py, table_type, is_reservable, is_available in layout_rows:
                status_cycle = (
                    TABLE_STATUS_FREE,
                    TABLE_STATUS_FREE,
                    TABLE_STATUS_OCCUPIED,
                    TABLE_STATUS_RESERVED,
                )
                status = status_cycle[tnum % len(status_cycle)]
                ws = WeightSensor.objects.create(
                    name="Seat sensor T{:03d}".format(tnum),
                    is_available=(tnum % 5 != 0),
                    last_reading_at=now - timedelta(minutes=tnum % 90),
                )
                sensors.append(ws)
                tables_by_number[tnum] = Table.objects.create(
                    table_number=tnum,
                    weight_sensor=ws,
                    library_floor=floor,
                    position_x=px,
                    position_y=py,
                    table_type=table_type,
                    status=status,
                    is_reservable=is_reservable,
                    is_available=is_available,
                )

            lcd_types = ("SSD1306", "ST7789")
            for tn in range(1, min(22, len(tables_by_number) + 1)):
                LCDDisplay.objects.create(
                    lcd_type=lcd_types[tn % 2],
                    table=tables_by_number[tn],
                    recorded_at=now - timedelta(minutes=tn * 3),
                    is_available=True,
                )

            n_tables = len(tables_by_number)
            for j in range(48):
                user = demo_users[j % len(demo_users)]
                tnum = (j % n_tables) + 1
                if j % 5 == 0:
                    start = now - timedelta(minutes=25 + j * 2)
                    end = now + timedelta(hours=2, minutes=j * 11)
                elif j % 5 == 1:
                    start = now + timedelta(hours=2, minutes=j * 7)
                    end = start + timedelta(hours=2, minutes=30)
                elif j % 5 == 2:
                    start = now + timedelta(hours=8, minutes=j * 5)
                    end = start + timedelta(hours=3)
                elif j % 5 == 3:
                    start = now + timedelta(hours=22, minutes=j * 3)
                    end = start + timedelta(hours=2, minutes=45)
                else:
                    start = now + timedelta(hours=36, minutes=j * 4)
                    end = start + timedelta(hours=4)
                mins = max(1, int((end - start).total_seconds() // 60))
                Reservation.objects.create(
                    user=user,
                    table=tables_by_number[tnum],
                    start_time=start,
                    end_time=end,
                    duration_minutes=mins,
                    is_available=True,
                    otp="",
                )

            for ws in sensors:
                for k in range(5):
                    OccupancyEvent.objects.create(
                        weight_sensor=ws,
                        weight=Decimal("35.00") + Decimal(k * 11) + Decimal(ws.pk % 7),
                        recorded_at=now - timedelta(minutes=ws.pk * 2 + k * 11),
                        event_type="demo_sample",
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Frontend demo load complete: {} tables (SINGLE/CIRCULAR/FOUR_SEATS), "
                "{} sensors, 48 reservations, 21 LCDs, {} occupancy events, {} demo users "
                "(password: {}).".format(
                    n_tables,
                    len(sensors),
                    len(sensors) * 5,
                    len(demo_users),
                    demo_password,
                )
            )
        )
        admin_email = (os.environ.get("ADMIN_EMAIL") or "").strip()
        if admin_email:
            self.stdout.write("Admin login: {}".format(admin_email))
        self.stdout.write(
            "Demo users: demo.user01@library.demo … demo.user{:02d}@library.demo".format(
                len(demo_users)
            )
        )
