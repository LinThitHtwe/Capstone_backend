import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from api.constants import ROLE_ADMIN

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create or update the single capstone admin from ADMIN_EMAIL and "
        "ADMIN_PASSWORD environment variables (staff + Django superuser + role=admin)."
    )

    def handle(self, *args, **options):
        email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD") or ""
        if not email or not password:
            raise CommandError(
                "Set ADMIN_EMAIL and ADMIN_PASSWORD in the environment, then run again."
            )

        existing_other_admin = User.objects.filter(role=ROLE_ADMIN).exclude(
            email__iexact=email
        )
        if existing_other_admin.exists():
            raise CommandError(
                "Another admin user already exists. There can only be one admin; "
                "remove or demote the existing admin first."
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": "Administrator",
                "role": ROLE_ADMIN,
                "id_number": "admin",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if not created:
            user.name = user.name or "Administrator"
            user.role = ROLE_ADMIN
            user.id_number = user.id_number or "admin"
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                "Capstone admin ready: {} ({})".format(
                    email, "created" if created else "updated"
                )
            )
        )
