"""
Django admin customization for core app.

Provides custom admin views for app installation.
"""
from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django import forms
from pathlib import Path
from sdc4_shared.utils.app_installer import AppInstaller


class AppUploadForm(forms.Form):
    """Form for uploading app ZIP files."""
    zip_file = forms.FileField(
        label='App ZIP File',
        help_text='Upload a generated SDC4 app ZIP file',
        widget=forms.FileInput(attrs={'accept': '.zip'})
    )


class CoreAdminSite(admin.AdminSite):
    """Custom admin site with app installation capability."""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('install-app/', self.admin_view(self.install_app_view), name='install_app'),
        ]
        return custom_urls + urls

    def install_app_view(self, request):
        """View for installing apps via file upload."""
        if request.method == 'POST':
            form = AppUploadForm(request.POST, request.FILES)
            if form.is_valid():
                # Save uploaded file to temp location
                uploaded_file = request.FILES['zip_file']
                temp_path = Path('/tmp') / uploaded_file.name

                with open(temp_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Run installation
                installer = AppInstaller(str(temp_path))
                result = installer.install()

                # Clean up temp file
                temp_path.unlink(missing_ok=True)

                # Display results
                if result.success:
                    messages.success(
                        request,
                        f"Successfully installed app: {result.app_name}"
                    )

                    if result.warnings:
                        for warning in result.warnings:
                            messages.warning(request, warning)

                    messages.info(
                        request,
                        f"Restart your server and visit: /{result.app_name}/"
                    )
                else:
                    for error in result.errors:
                        messages.error(request, error)

                    if result.warnings:
                        for warning in result.warnings:
                            messages.warning(request, warning)

                return redirect('admin:index')
        else:
            form = AppUploadForm()

        context = {
            **self.each_context(request),
            'form': form,
            'title': 'Install SDC4 App',
            'opts': None,  # Required for admin base template
        }

        return render(request, 'admin/install_app.html', context)


# Replace default admin site
admin.site.__class__ = CoreAdminSite
