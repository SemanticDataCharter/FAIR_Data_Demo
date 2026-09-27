"""
Views for core app - documentation rendering.
"""
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


def render_markdown(request, doc_name):
    """Render a markdown file as HTML."""
    # Map URL names to file paths
    doc_map = {
        'readme': settings.BASE_DIR / 'README.md',
        'triplestore': settings.BASE_DIR / 'docs' / 'TRIPLESTORE_GUIDE.md',
        'license': settings.BASE_DIR / 'LICENSE',
    }

    if doc_name not in doc_map:
        raise Http404("Documentation not found")

    doc_path = doc_map[doc_name]

    if not doc_path.exists():
        raise Http404(f"Documentation file not found: {doc_path}")

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert markdown to HTML if available
    if MARKDOWN_AVAILABLE:
        html_content = markdown.markdown(
            content,
            extensions=['fenced_code', 'tables', 'toc']
        )
    else:
        # Fallback: wrap in pre tag
        html_content = f'<pre style="white-space: pre-wrap;">{content}</pre>'

    # Get document title from first line
    title = content.split('\n')[0].lstrip('#').strip() if content else doc_name

    return render(request, 'docs/markdown_view.html', {
        'title': title,
        'content': html_content,
        'markdown_available': MARKDOWN_AVAILABLE,
    })
