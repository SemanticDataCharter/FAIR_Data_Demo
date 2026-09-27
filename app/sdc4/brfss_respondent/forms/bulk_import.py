"""
Bulk Import Form for uploading ZIP archives or specifying directory paths
containing SDC4 XML instances.
"""
from django import forms


class BulkImportForm(forms.Form):
    """Form for bulk importing XML instances."""

    IMPORT_SOURCE_CHOICES = [
        ('zip', 'ZIP Archive'),
        ('directory', 'Directory Path'),
    ]

    import_source = forms.ChoiceField(
        choices=IMPORT_SOURCE_CHOICES,
        initial='zip',
        widget=forms.RadioSelect,
        help_text='Choose whether to upload a ZIP file or specify a server directory path.',
    )
    zip_file = forms.FileField(
        required=False,
        help_text='Upload a ZIP archive containing XML instances.',
    )
    directory_path = forms.CharField(
        required=False,
        initial='/import_data/brfss_respondent',
        help_text='Place XML files in the import_data/brfss_respondent/ folder next to docker-compose.yml.',
    )

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get('import_source')
        if source == 'zip' and not cleaned.get('zip_file'):
            self.add_error('zip_file', 'ZIP file is required when import source is ZIP Archive.')
        elif source == 'directory' and not cleaned.get('directory_path'):
            self.add_error('directory_path', 'Directory path is required when import source is Directory Path.')
        return cleaned
