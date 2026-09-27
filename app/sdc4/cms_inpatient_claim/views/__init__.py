"""
Views for cms_inpatient_claim.

This package contains all views organized by functionality:
- wizard.py: Multi-step wizard for data entry
- list.py: List view with search and filtering
- detail.py: Detail view with XML/JSON display
"""
from .wizard import (
    WizardStartView,
    WizardStepView,
    WizardCompleteView,
)
from .list import InstanceListView
from .detail import (
    InstanceDetailView,
    InstanceDownloadXMLView,
    InstanceDownloadJSONView,
    InstanceDeleteView,
)
from .bulk_import import BulkImportView, TemplateDownloadView

__all__ = [
    'WizardStartView',
    'WizardStepView',
    'WizardCompleteView',
    'InstanceListView',
    'InstanceDetailView',
    'InstanceDownloadXMLView',
    'InstanceDownloadJSONView',
    'InstanceDeleteView',
    'BulkImportView',
    'TemplateDownloadView',
]
