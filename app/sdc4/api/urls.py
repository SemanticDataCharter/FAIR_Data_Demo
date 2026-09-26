"""API URL routing."""

from django.urls import path

from .views import (
    ZIPUploadView,
    SchemaUploadView,
    RDFUploadView,
    XMLValidationView,
)

app_name = 'api'

urlpatterns = [
    # Upload endpoints
    path('upload/zip/', ZIPUploadView.as_view(), name='upload-zip'),
    path('upload/schema/', SchemaUploadView.as_view(), name='upload-schema'),
    path('upload/rdf/', RDFUploadView.as_view(), name='upload-rdf'),

    # Validation endpoints
    path('validate/xml/', XMLValidationView.as_view(), name='validate-xml'),
]
