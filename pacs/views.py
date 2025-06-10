from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Study, Series, DicomFile
import pydicom
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.db import transaction
from django.http import FileResponse
import mimetypes
from django.db.models import Count, Prefetch
import zipfile
from io import BytesIO

# Create your views here.

@login_required
def home(request):
    studies = Study.objects.all().order_by('-study_date').prefetch_related(
        Prefetch('series_set', queryset=Series.objects.annotate(
            total_images=Count('dicom_files')
        ))
    )
    
    # Calcular totais para cada estudo
    for study in studies:
        study.total_series = study.series_set.count()
        study.total_images = sum(series.total_images for series in study.series_set.all())
    
    return render(request, 'pacs/home.html', {'studies': studies})

@login_required
def upload_dicom(request):
    if request.method == 'POST':
        dicom_files = request.FILES.getlist('dicom_files')
        if dicom_files:
            try:
                with transaction.atomic():
                    # Processa o primeiro arquivo para obter informações do estudo
                    first_file = dicom_files[0]
                    temp_path = default_storage.save(f'temp/{first_file.name}', ContentFile(first_file.read()))
                    temp_file_path = default_storage.path(temp_path)
                    
                    # Força a leitura do arquivo DICOM mesmo sem o cabeçalho padrão
                    ds = pydicom.dcmread(temp_file_path, force=True)
                    
                    # Cria ou obtém o estudo
                    study, created = Study.objects.get_or_create(
                        study_instance_uid=str(ds.get('StudyInstanceUID', '')),
                        defaults={
                            'patient_name': str(ds.get('PatientName', '')),
                            'patient_id': str(ds.get('PatientID', '')),
                            'study_date': ds.get('StudyDate', None),
                            'study_description': str(ds.get('StudyDescription', '')),
                            'uploaded_by': request.user
                        }
                    )
                    
                    # Processa cada arquivo
                    for dicom_file in dicom_files:
                        temp_path = default_storage.save(f'temp/{dicom_file.name}', ContentFile(dicom_file.read()))
                        temp_file_path = default_storage.path(temp_path)
                        
                        # Força a leitura do arquivo DICOM mesmo sem o cabeçalho padrão
                        ds = pydicom.dcmread(temp_file_path, force=True)
                        
                        # Cria ou obtém a série
                        series, created = Series.objects.get_or_create(
                            series_instance_uid=str(ds.get('SeriesInstanceUID', '')),
                            defaults={
                                'study': study,
                                'series_description': str(ds.get('SeriesDescription', '')),
                                'modality': str(ds.get('Modality', ''))
                            }
                        )
                        
                        # Cria o arquivo DICOM
                        dicom_obj = DicomFile.objects.create(
                            series=series,
                            file=dicom_file,
                            instance_number=ds.get('InstanceNumber', None),
                            sop_instance_uid=str(ds.get('SOPInstanceUID', ''))
                        )
                        
                        # Gera a pré-visualização
                        dicom_obj.generate_preview()
                        
                        # Remove o arquivo temporário
                        default_storage.delete(temp_path)
                    
                    messages.success(request, 'Arquivos DICOM enviados com sucesso!')
                    return redirect('home')
            except Exception as e:
                messages.error(request, f'Erro ao processar arquivos DICOM: {str(e)}')
                return redirect('upload_dicom')
    return render(request, 'pacs/upload.html')

@login_required
def view_study(request, pk):
    study = get_object_or_404(Study.objects.prefetch_related(
        Prefetch('series_set', queryset=Series.objects.annotate(
            total_images=Count('dicom_files')
        ))
    ), pk=pk)
    return render(request, 'pacs/view_study.html', {'study': study})

@login_required
def view_series(request, pk):
    series = get_object_or_404(Series.objects.select_related('study').prefetch_related('dicom_files'), pk=pk)
    return render(request, 'pacs/view_series.html', {'series': series})

@login_required
def delete_study(request, pk):
    study = get_object_or_404(Study, pk=pk)
    if request.method == 'POST':
        study.delete()
        messages.success(request, 'Estudo excluído com sucesso!')
        return redirect('home')
    return render(request, 'pacs/delete_study.html', {'study': study})

@login_required
def serve_dicom(request, pk):
    dicom_file = get_object_or_404(DicomFile, pk=pk)
    response = FileResponse(dicom_file.file, as_attachment=False)
    response['Content-Type'] = 'application/dicom'
    return response

@login_required
def download_series_zip(request, pk):
    series = get_object_or_404(Series.objects.prefetch_related('dicom_files'), pk=pk)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for dicom_file in series.dicom_files.all():
            filename = f"{dicom_file.instance_number or dicom_file.pk}.dcm"
            zip_file.writestr(filename, dicom_file.file.read())
            dicom_file.file.seek(0)  # Reset pointer
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename=f'serie_{series.pk}.zip')
    response['Content-Type'] = 'application/zip'
    return response
