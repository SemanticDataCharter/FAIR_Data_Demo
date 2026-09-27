
"""
URL configuration for cms_outpatient_claim.

Routes for:
- Wizard flow (start, steps, complete)
- Instance list and detail views
- Download endpoints (XML, JSON)
- Delete endpoint
"""
from django.urls import path
from .views import (
    WizardStartView,
    WizardStepView,
    WizardCompleteView,
    InstanceListView,
    InstanceDetailView,
    InstanceDownloadXMLView,
    InstanceDownloadJSONView,
    InstanceDeleteView,
    BulkImportView,
    TemplateDownloadView,
)

app_name = 'cms_outpatient_claim'

urlpatterns = [
    # Wizard routes
    path('wizard/', WizardStartView.as_view(), name='wizard-start'),
    path('wizard/step/<int:step>/', WizardStepView.as_view(), name='wizard-step'),
    path('wizard/complete/', WizardCompleteView.as_view(), name='wizard-complete'),

    # Instance list and detail
    path('', InstanceListView.as_view(), name='instance-list'),
    path('instance/<str:pk>/', InstanceDetailView.as_view(), name='instance-detail'),

    # Download endpoints
    path('instance/<str:pk>/xml/', InstanceDownloadXMLView.as_view(), name='instance-download-xml'),
    path('instance/<str:pk>/json/', InstanceDownloadJSONView.as_view(), name='instance-download-json'),

    # Delete endpoint
    path('instance/<str:pk>/delete/', InstanceDeleteView.as_view(), name='instance-delete'),

    # Bulk import
    path('bulk-import/', BulkImportView.as_view(), name='bulk-import'),
    path('bulk-import/template/', TemplateDownloadView.as_view(), name='download-template'),
]

