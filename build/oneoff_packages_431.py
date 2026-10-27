# One-off for production after build/oneoff_models_431.py: the three 4.3.1 packages.
#   bash run_oneoff.sh build/oneoff_packages_431.py
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from dmgen.models import DM
from generator.core.generator import DataModelGenerator
user = get_user_model().objects.get(email='twcook@axius-sdc.com')
request = RequestFactory().get('/'); request.user = user
for title in ('NHANES Participant 4.3.1', 'BRFSS Respondent 4.3.1', 'CMS Beneficiary 4.3.1'):
    dm = DM.objects.get(project__name='FAIR Data Demo', title=title); assert dm.published and not dm.retired, title
    msg, kind = DataModelGenerator(dm, request).create_dm_package()
    dm.refresh_from_db()
    print('PACKAGE', dm.title, dm.ct_id, repr(dm.zip_file.name if dm.zip_file else None), str(msg)[:120])
print('DONE')
