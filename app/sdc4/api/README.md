# SDC4 REST API

This Django app provides REST API endpoints for managing data model files, validating XML instances, and integrating with the GraphDB triplestore.

## Configuration

### 1. Add to INSTALLED_APPS

In your `settings.py`, add both `api` and `generic_storage` apps:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # Project apps
    'api',
    'generic_storage',
    'sdc4',
    # ... other apps ...
]
```

### 2. Configure Django REST Framework

Add REST Framework configuration to `settings.py`:

```python
# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.authentication.APIKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```

### 3. Configure GraphDB/Triplestore

Add triplestore settings to `settings.py`:

```python
# GraphDB Triplestore
GRAPHDB_URL = env('GRAPHDB_URL', default='http://localhost:17200')
GRAPHDB_REPOSITORY = env('GRAPHDB_REPOSITORY', default='sdc4_rdf')
GRAPHDB_USER = env('GRAPHDB_USER', default='admin')
GRAPHDB_PASSWORD = env('GRAPHDB_PASSWORD', default='admin123')
```

### 4. Add API URLs

In your main `urls.py`, include the API URLs:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    # ... other URLs ...
]
```

### 5. Run Migrations

Create and apply migrations for both apps:

```bash
python manage.py makemigrations api generic_storage
python manage.py migrate
```

## API Endpoints

### Authentication

All endpoints require authentication via API Key header:

```
X-API-Key: your-api-key-here
```

### Endpoints

- **POST /api/v1/upload/zip/** - Upload ZIP app file
- **POST /api/v1/upload/schema/** - Upload schema files (.xsd, .html, .owl)
- **POST /api/v1/upload/rdf/** - Upload RDF/Turtle files (.ttl, .rdf)
- **POST /api/v1/validate/xml/** - Validate and store XML instance

## Creating API Keys

1. Log into Django Admin at `/admin/`
2. Navigate to **API → API Keys**
3. Click **Add API Key**
4. Enter organization name and contact email
5. Click **Save**
6. **Copy the displayed API key immediately** - it cannot be retrieved later!

The generated key will be in format: `sdc4_xK9mN2pQ7rS4tU6vW8xY...`

## Usage Examples

### Upload ZIP File

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@test_app.zip" \
  http://localhost:18000/api/v1/upload/zip/
```

### Upload Schema Files

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "files=@dm-abc123.xsd" \
  -F "files=@dm-abc123.html" \
  http://localhost:18000/api/v1/upload/schema/
```

### Upload Turtle File

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@dm-abc123.ttl" \
  http://localhost:18000/api/v1/upload/rdf/
```

### Validate XML Instance

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@instance.xml" \
  http://localhost:18000/api/v1/validate/xml/
```

## Security Features

- **SHA-256 Hashing**: API keys are hashed before storage
- **One-Time Display**: Plaintext keys shown only at creation
- **Timing-Safe Comparison**: Uses `secrets.compare_digest()` to prevent timing attacks
- **Deactivation**: Keys can be deactivated without deletion
- **Usage Tracking**: Logs last usage time and request count

## Generic Instance Storage

XML instances without dedicated Django apps are stored in the `GenericInstance` model, which provides:

- **Full XML storage** (authoritative)
- **JSON representation** for JSONB queries
- **RDF content** for semantic integration
- **Validation metadata** and error tracking
- **Search text** for full-text search

View generic instances in Django Admin: **Generic Instance Storage → Generic Instances**

## Dependencies

Ensure these packages are installed:

```bash
pip install djangorestframework==3.14.0
pip install lxml==4.9.3
pip install cuid2==2.0.1
pip install requests==2.31.0
```

## Troubleshooting

### API Key Not Working

- Verify the key is active in Django Admin
- Check the `X-API-Key` header is set correctly
- Ensure the key hasn't been deleted or deactivated

### Triplestore Upload Failing

- Verify `GRAPHDB_URL` is accessible
- Check `GRAPHDB_USER` and `GRAPHDB_PASSWORD` are correct
- Ensure the repository exists in GraphDB
- Files will still be stored locally if triplestore upload fails

### Schema Not Found (404)

- Verify the XSD schema file exists in `mediafiles/dmlib/`
- Check the filename matches pattern: `dm-{ct_id}.xsd`
- Upload the schema using the `/api/v1/upload/schema/` endpoint first

## Architecture

### XML Validation Flow

1. Parse XML and extract `dm_ct_id` from root element `<sdc4:dm-{ct_id}>`
2. Check if schema `dm-{ct_id}.xsd` exists in `mediafiles/dmlib/`
3. Validate XML against XSD schema
4. Auto-correct with Exceptional Values (EVs) if validation fails
5. Check if Django app exists for this data model
6. Save to app-specific model or `GenericInstance`
7. Upload RDF to GraphDB triplestore
8. Return success response

### DM Registry

The DM registry (`sdc4/utils/dm_registry.py`) scans all installed apps for models with `DM_CT_ID` attribute, allowing dynamic routing of XML instances to the correct model class.

## Support

For issues or questions, contact your SDCStudio administrator.
