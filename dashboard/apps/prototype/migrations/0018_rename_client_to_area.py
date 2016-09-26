# -*- coding: utf-8 -*-
# Hand crafted on 23/09/16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0017_rename_project_to_product'),
    ]

    operations = [
        migrations.RenameModel('Client', 'Area'),

        migrations.RenameField('Product', 'client', 'area')
    ]
