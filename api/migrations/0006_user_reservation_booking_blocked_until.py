from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_reservation_otp_verified_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="reservation_booking_blocked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
