from django.db import models
from django.contrib.auth.models import User
import os
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Study(models.Model):
    patient_name = models.CharField(max_length=255)
    patient_id = models.CharField(max_length=64)
    study_date = models.DateField(null=True, blank=True)
    study_description = models.CharField(max_length=255, blank=True)
    study_instance_uid = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.patient_name} - {self.study_date}"

    class Meta:
        verbose_name_plural = "Studies"
        ordering = ['-study_date', '-created_at']

class Series(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='series_set')
    series_description = models.CharField(max_length=255, blank=True)
    series_instance_uid = models.CharField(max_length=64, unique=True)
    modality = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.series_description} - {self.modality}"

    class Meta:
        verbose_name_plural = "Series"
        ordering = ['created_at']

class DicomFile(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='dicom_files', null=True, blank=True)
    file = models.FileField(upload_to='dicom_files/')
    instance_number = models.IntegerField(null=True, blank=True)
    sop_instance_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    preview = models.ImageField(upload_to='previews/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    # Campos legados para migração
    patient_name = models.CharField(max_length=255, blank=True, null=True)
    patient_id = models.CharField(max_length=255, blank=True, null=True)
    study_date = models.DateField(null=True, blank=True)
    study_description = models.CharField(max_length=255, blank=True, null=True)
    modality = models.CharField(max_length=10, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.series:
            return f"Imagem {self.instance_number} - {self.series.series_description}"
        return f"Legacy DICOM - {self.patient_name}"

    def delete(self, *args, **kwargs):
        # Remove o arquivo físico quando o objeto é deletado
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def generate_preview(self):
        import pydicom
        import matplotlib.pyplot as plt
        import os
        from django.conf import settings
        from PIL import Image
        import io

        try:
            # Lê o arquivo DICOM forçando a leitura
            ds = pydicom.dcmread(self.file.path, force=True)
            
            # Obtém os dados da imagem
            pixel_array = ds.pixel_array
            
            # Cria a figura
            plt.figure(figsize=(8, 8))
            plt.imshow(pixel_array, cmap='gray')
            plt.axis('off')
            
            # Salva a imagem em um buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
            buffer.seek(0)
            
            # Cria o nome do arquivo de pré-visualização
            preview_filename = f"preview_{self.sop_instance_uid}.png"
            preview_path = os.path.join(settings.MEDIA_ROOT, 'previews', preview_filename)
            
            # Salva a imagem
            with open(preview_path, 'wb') as f:
                f.write(buffer.getvalue())
            
            # Atualiza o campo preview
            self.preview = f'previews/{preview_filename}'
            self.save()
            
            # Limpa a figura
            plt.close()
        except Exception as e:
            print(f"Erro ao gerar pré-visualização: {str(e)}")
            # Não propaga o erro para não interromper o upload

    class Meta:
        ordering = ['instance_number']
