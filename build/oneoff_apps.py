# One-off for production after the models are published: generate the seven standalone apps with SDCStudio's generate_app
# (the command behind the UI's app download) and put each zip in the bucket under fair/apps/.
import io, os, shutil, tempfile, zipfile
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
MODELS = {'nhanes_participant': 'xy8upneajsb8vdcmnve01g6g', 'nhanes_medication': 'epbdfmvxc3gbh5f66hhb3o2m', 'brfss_respondent': 'iymux9kjv8ndbkoi36xzx17i',
          'cms_beneficiary': 'fnv3zi2btk3s0sfodjsc25eb', 'cms_inpatient_claim': 'ji1eccop92mlmikwq5gwp7cr', 'cms_outpatient_claim': 'mllwhe842wtnim4ms48qonio',
          'cms_prescription_drug_event': 'nvemvhvdkctdlm9alwwgcay7'}
for app, ct in MODELS.items():
    out = tempfile.mkdtemp()
    call_command('generate_app', dm=ct, standalone=True, output_dir=out, app_name=app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, out))
    name = default_storage.save(f'fair/apps/{app}_sdc_project.zip', ContentFile(buf.getvalue()))
    print('APP', app, ct, name, len(buf.getvalue()))
    shutil.rmtree(out, ignore_errors=True)
print('DONE')
