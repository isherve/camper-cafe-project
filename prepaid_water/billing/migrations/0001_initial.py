# Generated manually for initial prepaid billing schema.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=20)),
                ("address", models.TextField()),
                ("meter_id", models.CharField(max_length=60, unique=True)),
                ("rfid_card", models.CharField(max_length=100, unique=True)),
                (
                    "is_water_enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Flag used to disable supply automatically when balance is depleted.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        help_text="Optional login account for customer portal access.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Tariff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price_per_liter", models.DecimalField(decimal_places=4, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("effective_from", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-effective_from"]},
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account",
                        to="billing.customer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("type", models.CharField(choices=[("topup", "Top Up"), ("deduction", "Deduction")], max_length=20)),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("reference", models.CharField(blank=True, max_length=120)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="billing.customer",
                    ),
                ),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.CreateModel(
            name="WaterUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("liters", models.DecimalField(decimal_places=3, max_digits=12)),
                ("cost", models.DecimalField(decimal_places=2, max_digits=12)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "meter_payload_id",
                    models.CharField(
                        blank=True,
                        help_text="Optional reading identifier for idempotency from IoT payload.",
                        max_length=120,
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="water_usages",
                        to="billing.customer",
                    ),
                ),
            ],
            options={"ordering": ["-timestamp"]},
        ),
    ]
