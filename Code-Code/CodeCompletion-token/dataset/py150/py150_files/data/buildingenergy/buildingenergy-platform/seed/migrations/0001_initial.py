"""
:copyright: (c) 2014 Building Energy Inc
:license: see LICENSE for more details.
"""
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Project'
        db.create_table(u'seed_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from='name', unique_with=())),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['landing.SEEDUser'], null=True, blank=True)),
            ('last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_modified_user', null=True, to=orm['landing.SEEDUser'])),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organizations.Organization'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'seed', ['Project'])

        # Adding model 'ProjectBuilding'
        db.create_table(u'seed_projectbuilding', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('building_snapshot', self.gf('django.db.models.fields.related.ForeignKey')(related_name='project_building_snapshots', to=orm['seed.BuildingSnapshot'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='project_building_snapshots', to=orm['seed.Project'])),
            ('compliant', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('approved_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('approver', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['landing.SEEDUser'], null=True, blank=True)),
            ('status_label', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seed.StatusLabel'], null=True, blank=True)),
        ))
        db.send_create_signal(u'seed', ['ProjectBuilding'])

        # Adding unique constraint on 'ProjectBuilding', fields ['building_snapshot', 'project']
        db.create_unique(u'seed_projectbuilding', ['building_snapshot_id', 'project_id'])

        # Adding model 'StatusLabel'
        db.create_table(u'seed_statuslabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('color', self.gf('django.db.models.fields.CharField')(default='green', max_length=30)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organizations.Organization'], null=True, blank=True)),
        ))
        db.send_create_signal(u'seed', ['StatusLabel'])

        # Adding unique constraint on 'StatusLabel', fields ['name', 'organization']
        db.create_unique(u'seed_statuslabel', ['name', 'organization_id'])

        # Adding model 'Compliance'
        db.create_table(u'seed_compliance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('compliance_type', self.gf('django.db.models.fields.CharField')(default='Benchmarking', max_length=30)),
            ('start_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('deadline_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seed.Project'])),
        ))
        db.send_create_signal(u'seed', ['Compliance'])

        # Adding model 'CustomBuildingHeaders'
        db.create_table(u'seed_custombuildingheaders', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organizations.Organization'])),
            ('building_headers', self.gf('djorm_pgjson.fields.JSONField')(default={})),
        ))
        db.send_create_signal(u'seed', ['CustomBuildingHeaders'])

        # Adding model 'ColumnMapping'
        db.create_table(u'seed_columnmapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['landing.SEEDUser'], null=True, blank=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organizations.Organization'], null=True, blank=True)),
            ('source_type', self.gf('django.db.models.fields.IntegerField')()),
            ('column_raw', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('column_mapped', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'seed', ['ColumnMapping'])

        # Adding unique constraint on 'ColumnMapping', fields ['organization', 'column_raw']
        db.create_unique(u'seed_columnmapping', ['organization_id', 'column_raw'])

        # Adding model 'CanonicalBuilding'
        db.create_table(u'seed_canonicalbuilding', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('canonical_snapshot', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seed.BuildingSnapshot'], null=True, blank=True)),
        ))
        db.send_create_signal(u'seed', ['CanonicalBuilding'])

        # Adding model 'BuildingSnapshot'
        db.create_table(u'seed_buildingsnapshot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('import_record', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data_importer.ImportRecord'], null=True, blank=True)),
            ('import_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data_importer.ImportFile'], null=True, blank=True)),
            ('canonical_building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['seed.CanonicalBuilding'], null=True, blank=True)),
            ('tax_lot_id', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('tax_id_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('pm_property_id', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('pm_property_id_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('custom_id_1', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('custom_id_1_id_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('property_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('property_notes_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('year_ending', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('year_ending_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('district', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('district_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('owner', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('owner_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('owner_email', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('owner_email_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('owner_telephone', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('owner_telephone_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('property_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('property_name_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('building_count', self.gf('django.db.models.fields.IntegerField')(max_length=3, null=True, blank=True)),
            ('building_count_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('gross_floor_area', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('gross_floor_area_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('address_line_1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('address_line_1_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('address_line_2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('address_line_2_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('city_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('postal_code_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('year_built', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('year_built_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('recent_sale_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('recent_sale_date_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('energy_score', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('energy_score_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('site_eui', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('site_eui_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('generation_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('generation_date_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('release_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('release_date_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('state_province', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('state_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('site_eui_weather_normalized', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('site_eui_weather_normalized_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('source_eui', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('source_eui_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('source_eui_weather_normalized', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('source_eui_weather_normalized_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('energy_alerts', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('energy_alerts_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('space_alerts', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('space_alerts_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('building_certification', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('building_certification_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('conditioned_floor_area', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('conditioned_floor_area_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('occupied_floor_area', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('occupied_floor_area_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['seed.BuildingSnapshot'])),
            ('best_guess_confidence', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('best_guess_canonical_building', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='best_guess', null=True, to=orm['seed.CanonicalBuilding'])),
            ('match_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('confidence', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['landing.SEEDUser'], null=True, blank=True)),
            ('source_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('canonical_for_ds', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['data_importer.ImportRecord'])),
            ('extra_data', self.gf('djorm_pgjson.fields.JSONField')(default={})),
            ('extra_data_sources', self.gf('djorm_pgjson.fields.JSONField')(default={})),
        ))
        db.send_create_signal(u'seed', ['BuildingSnapshot'])

        # Adding M2M table for field children on 'BuildingSnapshot'
        m2m_table_name = db.shorten_name(u'seed_buildingsnapshot_children')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_buildingsnapshot', models.ForeignKey(orm[u'seed.buildingsnapshot'], null=False)),
            ('to_buildingsnapshot', models.ForeignKey(orm[u'seed.buildingsnapshot'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_buildingsnapshot_id', 'to_buildingsnapshot_id'])

        # Adding model 'AttributeOption'
        db.create_table(u'seed_attributeoption', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value_source', self.gf('django.db.models.fields.IntegerField')()),
            ('building_variant', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='options', null=True, to=orm['seed.BuildingAttributeVariant'])),
        ))
        db.send_create_signal(u'seed', ['AttributeOption'])

        # Adding model 'BuildingAttributeVariant'
        db.create_table(u'seed_buildingattributevariant', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('building_snapshot', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='variants', null=True, to=orm['seed.BuildingSnapshot'])),
        ))
        db.send_create_signal(u'seed', ['BuildingAttributeVariant'])

        # Adding unique constraint on 'BuildingAttributeVariant', fields ['field_name', 'building_snapshot']
        db.create_unique(u'seed_buildingattributevariant', ['field_name', 'building_snapshot_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'BuildingAttributeVariant', fields ['field_name', 'building_snapshot']
        db.delete_unique(u'seed_buildingattributevariant', ['field_name', 'building_snapshot_id'])

        # Removing unique constraint on 'ColumnMapping', fields ['organization', 'column_raw']
        db.delete_unique(u'seed_columnmapping', ['organization_id', 'column_raw'])

        # Removing unique constraint on 'StatusLabel', fields ['name', 'organization']
        db.delete_unique(u'seed_statuslabel', ['name', 'organization_id'])

        # Removing unique constraint on 'ProjectBuilding', fields ['building_snapshot', 'project']
        db.delete_unique(u'seed_projectbuilding', ['building_snapshot_id', 'project_id'])

        # Deleting model 'Project'
        db.delete_table(u'seed_project')

        # Deleting model 'ProjectBuilding'
        db.delete_table(u'seed_projectbuilding')

        # Deleting model 'StatusLabel'
        db.delete_table(u'seed_statuslabel')

        # Deleting model 'Compliance'
        db.delete_table(u'seed_compliance')

        # Deleting model 'CustomBuildingHeaders'
        db.delete_table(u'seed_custombuildingheaders')

        # Deleting model 'ColumnMapping'
        db.delete_table(u'seed_columnmapping')

        # Deleting model 'CanonicalBuilding'
        db.delete_table(u'seed_canonicalbuilding')

        # Deleting model 'BuildingSnapshot'
        db.delete_table(u'seed_buildingsnapshot')

        # Removing M2M table for field children on 'BuildingSnapshot'
        db.delete_table(db.shorten_name(u'seed_buildingsnapshot_children'))

        # Deleting model 'AttributeOption'
        db.delete_table(u'seed_attributeoption')

        # Deleting model 'BuildingAttributeVariant'
        db.delete_table(u'seed_buildingattributevariant')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'data_importer.importfile': {
            'Meta': {'object_name': 'ImportFile'},
            'cached_first_row': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cached_second_to_fifth_row': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'coercion_mapping_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'export_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'file_size_in_bytes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'has_header_row': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_source_id': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_record': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['data_importer.ImportRecord']"}),
            'initial_mapping_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_espm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mapping_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mapping_confidence': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mapping_error_messages': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'num_coercion_errors': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'num_coercions_total': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'num_columns': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_mapping_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_mapping_warnings': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_rows': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_tasks_complete': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_tasks_total': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_validation_errors': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'data_importer.importrecord': {
            'Meta': {'ordering': "('-updated_at',)", 'object_name': 'ImportRecord'},
            'app': ('django.db.models.fields.CharField', [], {'default': "'seed'", 'max_length': '64'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_completed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'is_imported_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'keep_missing_buildings': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'modified_import_records'", 'null': 'True', 'to': u"orm['landing.SEEDUser']"}),
            'matching_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'matching_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mcm_version': ('django.db.models.fields.IntegerField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'merge_analysis_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'merge_analysis_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'merge_analysis_queued': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'merge_completed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Unnamed Dataset'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['landing.SEEDUser']", 'null': 'True', 'blank': 'True'}),
            'premerge_analysis_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'premerge_analysis_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'premerge_analysis_queued': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'landing.seeduser': {
            'Meta': {'object_name': 'SEEDUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default_custom_columns': ('djorm_pgjson.fields.JSONField', [], {'default': '{}'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'organizations.organization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Organization'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '200', 'separator': "u'-'", 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['landing.SEEDUser']", 'through': u"orm['organizations.OrganizationUser']", 'symmetrical': 'False'})
        },
        u'organizations.organizationuser': {
            'Meta': {'ordering': "['organization', 'user']", 'unique_together': "(('user', 'organization'),)", 'object_name': 'OrganizationUser'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organization_users'", 'to': u"orm['organizations.Organization']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'organization_users'", 'to': u"orm['landing.SEEDUser']"})
        },
        u'seed.attributeoption': {
            'Meta': {'object_name': 'AttributeOption'},
            'building_variant': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'options'", 'null': 'True', 'to': u"orm['seed.BuildingAttributeVariant']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value_source': ('django.db.models.fields.IntegerField', [], {})
        },
        u'seed.buildingattributevariant': {
            'Meta': {'unique_together': "(('field_name', 'building_snapshot'),)", 'object_name': 'BuildingAttributeVariant'},
            'building_snapshot': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'variants'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'seed.buildingsnapshot': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'BuildingSnapshot'},
            'address_line_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'address_line_1_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'address_line_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'address_line_2_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'best_guess_canonical_building': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'best_guess'", 'null': 'True', 'to': u"orm['seed.CanonicalBuilding']"}),
            'best_guess_confidence': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'building_certification': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'building_certification_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'building_count': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'building_count_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'canonical_building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seed.CanonicalBuilding']", 'null': 'True', 'blank': 'True'}),
            'canonical_for_ds': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['data_importer.ImportRecord']"}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'parents'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['seed.BuildingSnapshot']"}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'conditioned_floor_area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'conditioned_floor_area_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'confidence': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'custom_id_1': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'custom_id_1_id_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'district': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'district_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'energy_alerts': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'energy_alerts_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'energy_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'energy_score_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'extra_data': ('djorm_pgjson.fields.JSONField', [], {'default': '{}'}),
            'extra_data_sources': ('djorm_pgjson.fields.JSONField', [], {'default': '{}'}),
            'generation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'generation_date_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'gross_floor_area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gross_floor_area_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['data_importer.ImportFile']", 'null': 'True', 'blank': 'True'}),
            'import_record': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['data_importer.ImportRecord']", 'null': 'True', 'blank': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['landing.SEEDUser']", 'null': 'True', 'blank': 'True'}),
            'match_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'occupied_floor_area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'occupied_floor_area_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'owner_email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'owner_email_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'owner_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'owner_telephone': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'owner_telephone_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'pm_property_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'pm_property_id_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'postal_code_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'property_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'property_name_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'property_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'property_notes_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'recent_sale_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recent_sale_date_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'release_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'release_date_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'site_eui': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'site_eui_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'site_eui_weather_normalized': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'site_eui_weather_normalized_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'source_eui': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'source_eui_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'source_eui_weather_normalized': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'source_eui_weather_normalized_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'source_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'space_alerts': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'space_alerts_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'tax_id_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'tax_lot_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'year_built': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'year_built_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"}),
            'year_ending': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'year_ending_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['seed.BuildingSnapshot']"})
        },
        u'seed.canonicalbuilding': {
            'Meta': {'object_name': 'CanonicalBuilding'},
            'canonical_snapshot': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seed.BuildingSnapshot']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'seed.columnmapping': {
            'Meta': {'unique_together': "(('organization', 'column_raw'),)", 'object_name': 'ColumnMapping'},
            'column_mapped': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'column_raw': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizations.Organization']", 'null': 'True', 'blank': 'True'}),
            'source_type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['landing.SEEDUser']", 'null': 'True', 'blank': 'True'})
        },
        u'seed.compliance': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Compliance'},
            'compliance_type': ('django.db.models.fields.CharField', [], {'default': "'Benchmarking'", 'max_length': '30'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deadline_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seed.Project']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'seed.custombuildingheaders': {
            'Meta': {'object_name': 'CustomBuildingHeaders'},
            'building_headers': ('djorm_pgjson.fields.JSONField', [], {'default': '{}'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizations.Organization']"})
        },
        u'seed.project': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Project'},
            'building_snapshots': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['seed.BuildingSnapshot']", 'null': 'True', 'through': u"orm['seed.ProjectBuilding']", 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_modified_user'", 'null': 'True', 'to': u"orm['landing.SEEDUser']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizations.Organization']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['landing.SEEDUser']", 'null': 'True', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': "'name'", 'unique_with': '()'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'seed.projectbuilding': {
            'Meta': {'ordering': "['project', 'building_snapshot']", 'unique_together': "(('building_snapshot', 'project'),)", 'object_name': 'ProjectBuilding'},
            'approved_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'approver': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['landing.SEEDUser']", 'null': 'True', 'blank': 'True'}),
            'building_snapshot': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_building_snapshots'", 'to': u"orm['seed.BuildingSnapshot']"}),
            'compliant': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_building_snapshots'", 'to': u"orm['seed.Project']"}),
            'status_label': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seed.StatusLabel']", 'null': 'True', 'blank': 'True'})
        },
        u'seed.statuslabel': {
            'Meta': {'ordering': "['-name']", 'unique_together': "(('name', 'organization'),)", 'object_name': 'StatusLabel'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'green'", 'max_length': '30'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizations.Organization']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['seed']