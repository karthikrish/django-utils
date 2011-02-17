DATABASE_ENGINE = 'sqlite3'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'djutils',
    'djutils.tests',
]

CACHE_BACKEND = 'djutils.tests.cache_backend://'

TEMPLATE_CONTEXT_PROCESSORS = (
    'djutils.context_processors.settings',
)

IGNORE_THIS = 'testing'
