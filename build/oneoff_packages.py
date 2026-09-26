# One-off for production: build the package (XSD, XML template, JSON, JSON-LD, RDF, TTL, SHACL, GQL, HTML, zip) of each 4.2.0 model,
# what the UI's Generate does; a shell publish does not build it.
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from dmgen.models import DM
from generator.core.generator import DataModelGenerator
user = get_user_model().objects.get(email='twcook@axius-sdc.com')
request = RequestFactory().get('/'); request.user = user
for dm in DM.objects.filter(project__name='FAIR Data Demo', retired=False, title__in=['NHANES Participant', 'NHANES Medication', 'BRFSS Respondent', 'CMS Beneficiary', 'CMS Inpatient Claim', 'CMS Outpatient Claim', 'CMS Prescription Drug Event']).order_by('title'):
    msg, kind = DataModelGenerator(dm, request).create_dm_package()
    dm.refresh_from_db()
    print('PACKAGE', dm.title, dm.ct_id, repr(dm.zip_file.name if dm.zip_file else None), str(msg)[:120])
print('DONE')
