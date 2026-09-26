"""
The console renders one record three ways. These tests render the templates
with canned context and check the things that broke once: the page title
carried a <script> (fixed in #19), and the version badge drifted from the
tag (now read from app/sdc4/VERSION).
"""
import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings

# Plain static storage: the tests render templates, they do not need a collectstatic
# manifest, and the CI runner has none.
PLAIN_STATIC = override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})


def render(template, ctx):
    """Render with a request so the context processors (the version among them) run."""
    return render_to_string(template, ctx, request=RequestFactory().get('/'))


@PLAIN_STATIC
class ConsoleTemplateTests(SimpleTestCase):
    def test_instance_title_is_clean_and_script_sits_before_body_end(self):
        html = render('console/instance.html', {
            'h': {'dm_label': 'CivilRegistry', 'instance_id': 'i-test', 'ct_id': 'dm-test',
                  'validation_status': 'valid', 'validation_label': 'Valid', 'stated_absences': []},
            'pane': 'table', 'panes': ['table', 'document', 'graph'], 'rows': [],
            'nav': {'prev': 'i-prev', 'next': 'i-next', 'position': 2, 'total': 3}, 'governed': None,
        })
        title = re.search(r'<title>(.*?)</title>', html, re.S).group(1)
        self.assertIn('CivilRegistry i-test', title)
        self.assertNotIn('<script', title)
        self.assertLess(html.index('keydown'), html.index('</body>'))
        self.assertGreater(html.index('keydown'), html.index('<main>'))


@PLAIN_STATIC
class VersionTests(SimpleTestCase):
    def test_version_file_is_the_single_source(self):
        on_disk = (Path(settings.BASE_DIR) / 'VERSION').read_text().strip()
        self.assertRegex(on_disk, r'^\d+\.\d+\.\d+$')
        self.assertEqual(settings.CORDOVAOS_VERSION, on_disk)

    def test_templates_carry_the_version_not_a_literal(self):
        for template, ctx in (('demo/base.html', {}), ('index.html', {})):
            html = render(template, ctx)
            self.assertIn(f'v{settings.CORDOVAOS_VERSION}', html, template)
            found = set(re.findall(r'\bv(\d+\.\d+\.\d+)\b', html))
            self.assertEqual(found, {settings.CORDOVAOS_VERSION}, template)
