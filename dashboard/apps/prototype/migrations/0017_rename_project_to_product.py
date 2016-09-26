# -*- coding: utf-8 -*-
# Hand crafted on 22/09/16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0016_auto_20160919_1538'),
    ]

    operations = [
        migrations.RenameModel('Project', 'Product'),
        migrations.RenameModel('ProjectStatus', 'ProductStatus'),
        migrations.RenameModel('ProjectGroup', 'ProductGroup'),
        migrations.RenameModel('ProjectGroupStatus', 'ProductGroupStatus'),

        migrations.RenameField('Task', 'project', 'product'),
        migrations.RenameField('Cost', 'project', 'product'),
        migrations.RenameField('ProductStatus', 'project', 'product'),
        migrations.RenameField('Saving', 'project', 'product'),
        migrations.RenameField('Link', 'project', 'product'),
        migrations.RenameField('Budget', 'project', 'product'),

        migrations.RenameField('ProductGroup', 'projects', 'products'),
        migrations.RenameField('ProductGroupStatus', 'project_group', 'product_group'),
    ]
