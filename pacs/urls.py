from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_dicom, name='upload_dicom'),
    path('study/<int:pk>/', views.view_study, name='view_study'),
    path('series/<int:pk>/', views.view_series, name='view_series'),
    path('study/<int:pk>/delete/', views.delete_study, name='delete_study'),
    path('dicom/<int:pk>/', views.serve_dicom, name='serve_dicom'),
    path('series/<int:pk>/download_zip/', views.download_series_zip, name='download_series_zip'),
] 