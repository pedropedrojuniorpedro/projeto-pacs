from django import forms
from .models import DicomFile

class DicomUploadForm(forms.ModelForm):
    class Meta:
        model = DicomFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.dcm,application/dicom'})
        } 