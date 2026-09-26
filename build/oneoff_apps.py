# One-off for production after the models are published: generate the ten standalone apps with SDCStudio's generate_app
# (the command behind the UI's app download) and put each zip in the bucket under cordova/apps/.
import io, os, shutil, tempfile, zipfile
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
MODELS = {'civil_registry': 'etkbxubkngv0v81yvqz77xrs', 'vital_statistics_record': 'sokc3go551qsp4s72lo6ys9c', 'business_registry': 'nb7gtyimcusmritzx0o0x40o',
          'property_registry': 'goc13fg5a97ghcqv64h782af', 'education_record': 'mtwtwhn0csuhbw56sjx01ol8', 'employment_record': 'rxv2ck9k9r1bqkggeydam32s',
          'tax_and_revenue_record': 'apc16uwrj02wgitw7ji1utng', 'healthcare_record': 'dcsd8bxr8a6lzcptwwyms44t', 'law_enforcement_record': 'zdhuex1xwf8s5niriw878e0o',
          'maritime_port_authority': 'v42afzhs22bvschuo56rdpzi'}
for app, ct in MODELS.items():
    out = tempfile.mkdtemp()
    call_command('generate_app', dm=ct, standalone=True, output_dir=out, app_name=app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, out))
    name = default_storage.save(f'cordova/apps/{app}_sdc_project.zip', ContentFile(buf.getvalue()))
    print('APP', app, ct, name, len(buf.getvalue()))
    shutil.rmtree(out, ignore_errors=True)
print('DONE')
