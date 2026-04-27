from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_table_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="otp_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
