from django.contrib import admin
from .models import Study, Series, DicomFile

@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'patient_id', 'study_date', 'study_description', 'uploaded_by', 'created_at')
    list_filter = ('study_date', 'uploaded_by')
    search_fields = ('patient_name', 'patient_id', 'study_description')
    date_hierarchy = 'study_date'

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('series_description', 'modality', 'study', 'created_at')
    list_filter = ('modality', 'study')
    search_fields = ('series_description', 'study__patient_name')
    date_hierarchy = 'created_at'

@admin.register(DicomFile)
class DicomFileAdmin(admin.ModelAdmin):
    list_display = ('instance_number', 'series', 'created_at')
    list_filter = ('series', 'series__modality')
    search_fields = ('series__series_description', 'series__study__patient_name')
    date_hierarchy = 'created_at'
