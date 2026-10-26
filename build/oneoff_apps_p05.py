# One-off for production after the 4.2.5 package is built: generate the NHANES Medication 4.2.5 app into fair/apps/4.2.5/.
# Run it once: a second run writes a second zip beside the first.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/oneoff_apps_p05.py)\""
#   (or: bash run_oneoff.sh build/oneoff_apps_p05.py)
import io, os, shutil, tempfile, zipfile
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dmgen.models import DM
MODELS = {'nhanes_medication': 'NHANES Medication 4.2.5'}
for app, title in MODELS.items():
    ct = DM.objects.get(project__name='FAIR Data Demo', title=title).ct_id
    out = tempfile.mkdtemp()
    call_command('generate_app', dm=ct, standalone=True, output_dir=out, app_name=app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, out))
    name = default_storage.save(f'fair/apps/4.2.5/{app}_sdc_project.zip', ContentFile(buf.getvalue()))
    print('APP', app, ct, name, len(buf.getvalue()))
    shutil.rmtree(out, ignore_errors=True)
print('DONE')
