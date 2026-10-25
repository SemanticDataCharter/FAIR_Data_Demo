# One-off for production after the 4.2.3 packages are built: generate the two 4.2.3 standalone apps with SDCStudio's
# generate_app and put each zip in the bucket under fair/apps/4.2.3/ (the 4.2.0 apps stay where they are).
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/oneoff_apps_errata.py)\""
import io, os, shutil, tempfile, zipfile
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
MODELS = {'nhanes_participant': 'eehpfapwgvxtzdrofgstdcfs', 'brfss_respondent': 'w9ozx00idgs5k8tw4359skvn'}
for app, ct in MODELS.items():
    out = tempfile.mkdtemp()
    call_command('generate_app', dm=ct, standalone=True, output_dir=out, app_name=app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, out))
    name = default_storage.save(f'fair/apps/4.2.3/{app}_sdc_project.zip', ContentFile(buf.getvalue()))
    print('APP', app, ct, name, len(buf.getvalue()))
    shutil.rmtree(out, ignore_errors=True)
print('DONE')
