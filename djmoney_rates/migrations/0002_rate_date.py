# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djmoney_rates.models


class Migration(migrations.Migration):

    dependencies = [
        ('djmoney_rates', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rate',
            name='date',
            field=models.DateField(default=djmoney_rates.models._get_default_date, null=True, blank=True),
        ),
    ]
