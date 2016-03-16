# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djmoney_rates.models


class Migration(migrations.Migration):

    dependencies = [
        ('djmoney_rates', '0002_rate_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rate',
            options={'ordering': ('-date', 'currency')},
        ),
        migrations.AlterField(
            model_name='rate',
            name='currency',
            field=models.CharField(max_length=3, db_index=True),
        ),
        migrations.AlterField(
            model_name='rate',
            name='date',
            field=models.DateField(default=djmoney_rates.models._get_default_date, null=True, db_index=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='rate',
            unique_together=set([('source', 'currency', 'date')]),
        ),
    ]
