from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_table_weight_sensor_nullable"),
    ]

    operations = [
        migrations.RenameField(
            model_name="weightsensor",
            old_name="location",
            new_name="name",
        ),
    ]
