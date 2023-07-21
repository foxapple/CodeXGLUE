# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import djangobmf.fields

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BMF_CONTRIB_ADDRESS),
        migrations.swappable_dependency(settings.BMF_CONTRIB_INVOICE),
        migrations.swappable_dependency(settings.BMF_CONTRIB_PRODUCT),
    ]

    operations = [
        migrations.CreateModel(
            name='Quotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created', null=True)),
                ('uuid', models.CharField(editable=False, max_length=100, blank=True, null=True, verbose_name='UUID', db_index=True)),
                ('state', djangobmf.fields.OLDWorkflowField(db_index=True, max_length=32, null=True, editable=False, blank=True)),
                ('quotation_number', models.CharField(max_length=255, null=True, verbose_name='Quotation number')),
                ('net', models.FloatField(null=True, editable=False, blank=True)),
                ('date', models.DateField(null=True, verbose_name='Date')),
                ('valid_until', models.DateField(null=True, verbose_name='Valid until', blank=True)),
                ('notes', models.TextField(null=True, verbose_name='Notes', blank=True)),
                ('term_of_payment', models.TextField(null=True, verbose_name='Term of payment', blank=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, related_name="+")),
                ('invoice', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, null=True, blank=True, editable=False, to=settings.BMF_CONTRIB_INVOICE, related_name="quotation")),
                ('invoice_address', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.BMF_CONTRIB_ADDRESS, null=True, related_name="invoice_quotation")),
                ('modified_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, related_name="+")),
                ('shipping_address', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.BMF_CONTRIB_ADDRESS, null=True, related_name="shipping_quotation")),
            ],
            options={
                'ordering': ['-pk'],
                'abstract': False,
                'verbose_name': 'Quotation',
                'verbose_name_plural': 'Quotations',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuotationProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name')),
                ('price', djangobmf.fields.MoneyField(verbose_name='Price', max_digits=27, decimal_places=9)),
                ('price_currency', djangobmf.fields.CurrencyField(default=djangobmf.fields.get_default_currency, max_length=4, null=True, editable=False)),
                ('price_precision', models.PositiveSmallIntegerField(default=0, null=True, editable=False, blank=True)),
                ('amount', models.FloatField(default=1.0, null=True, verbose_name='Amount')),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.BMF_CONTRIB_PRODUCT, null=True, related_name="quotation_products")),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='quotation',
            name='products',
            field=models.ManyToManyField(to=settings.BMF_CONTRIB_PRODUCT, through='djangobmf_quotation.QuotationProduct'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='quotationproduct',
            name='quotation',
            field=models.ForeignKey(blank=True, to='djangobmf_quotation.Quotation', null=True, related_name="quotation_products"),
            preserve_default=True,
        ),
    ]
