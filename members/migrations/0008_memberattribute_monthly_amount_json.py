# Stellt monthly_amount von einem Postgres-ArrayField auf ein JSONField um,
# damit die App auch mit SQLite laeuft. Vorhandene Daten werden uebernommen.

from decimal import Decimal

import django.core.serializers.json
from django.db import migrations, models


def forwards(apps, schema_editor):
    MemberAttribute = apps.get_model("members", "MemberAttribute")
    for attribute in MemberAttribute.objects.all():
        entries = attribute.monthly_amount or []
        attribute.monthly_amount_json = [
            [str(e[0]), int(e[1]), int(e[2])] for e in entries if e and len(e) >= 3
        ]
        attribute.save(update_fields=["monthly_amount_json"])


def backwards(apps, schema_editor):
    MemberAttribute = apps.get_model("members", "MemberAttribute")
    for attribute in MemberAttribute.objects.all():
        attribute.monthly_amount = [
            [Decimal(str(e[0])), Decimal(e[1]), Decimal(e[2])]
            for e in (attribute.monthly_amount_json or [])
        ]
        attribute.save(update_fields=["monthly_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0007_member_monthly_salary_transaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberattribute",
            name="monthly_amount_json",
            field=models.JSONField(
                blank=True, default=list, encoder=django.core.serializers.json.DjangoJSONEncoder
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name="memberattribute",
            name="monthly_amount",
        ),
        migrations.RenameField(
            model_name="memberattribute",
            old_name="monthly_amount_json",
            new_name="monthly_amount",
        ),
        migrations.AlterModelOptions(
            name="memberattribute",
            options={"ordering": ["id"]},
        ),
        migrations.AlterModelOptions(
            name="transaction",
            options={"ordering": ["-created", "-id"]},
        ),
    ]
