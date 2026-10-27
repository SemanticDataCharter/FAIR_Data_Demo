# One-off for production after the 4.3.0 packages are built: the four apps into fair/apps/4.3.0/. Run it once.
#   bash run_oneoff.sh build/oneoff_apps_430.py   (or: gcloud run jobs execute sdcstudio-migrate ... shell -c "$(grep -v '^#' build/oneoff_apps_430.py)")
import io, os, shutil, tempfile, zipfile
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dmgen.models import DM
MODELS = {'nhanes_participant': 'NHANES Participant 4.3.0', 'brfss_respondent': 'BRFSS Respondent 4.3.0', 'nhanes_medication': 'NHANES Medication 4.3.0', 'cms_beneficiary': 'CMS Beneficiary 4.3.0'}
for app, title in MODELS.items():
    ct = DM.objects.get(project__name='FAIR Data Demo', title=title).ct_id
    out = tempfile.mkdtemp()
    call_command('generate_app', dm=ct, standalone=True, output_dir=out, app_name=app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, out))
    name = default_storage.save(f'fair/apps/4.3.0/{app}_sdc_project.zip', ContentFile(buf.getvalue()))
    print('APP', app, ct, name, len(buf.getvalue()))
    shutil.rmtree(out, ignore_errors=True)
print('DONE')
