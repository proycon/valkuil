# Django settings for webvalkuil project.
from socket import gethostname
from base64 import b64decode as D
from os import environ

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Maarten van Gompel', 'proycon@anaproy.nl'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'nl'

#SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True


hostname = gethostname()
if hostname == "spitfire" or hostname == "spitfire.science.ru.nl":  #Nijmegen
    ROOT_DIR = "/var/www2/valkuil/live/repo/valkuil/"
    DOCDIR = "/var/www2/valkuil/live/writable/userdocs/" 
    CLAMSERVICE = 'http://lst-webservices.science.ru.nl/valkuil/'
    
    MEDIA_URL = 'http://valkuil.science.ru.nl/style/' #TODO: adapt to new domains
    
    CLAMUSER = 'internal'
    CLAMPASS = D(open(environ['CLAMOPENER_PASSFILE']).read().strip())
    
    DEBUG = False #No debug in production environment            
elif hostname == 'echo' or hostname == 'nomia' or hostname == 'echo.uvt.nl' or hostname == 'nomia.uvt.nl': #Tilburg
    ROOT_DIR = "/var/www/valkuil/"
    DOCDIR = ROOT_DIR + 'userdocs/'
    CLAMSERVICE = 'http://webservices.ticc.uvt.nl/valkuil/'    
    
    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash if there is a path component (optional in other cases).
    # Examples: "http://media.lawrence.com", "http://example.com/media/"
    MEDIA_URL = 'http://valkuil.net/style/'
        
elif hostname == "aurora" or hostname == "roma": #proycon's laptop/server
    ROOT_DIR = "/home/proycon/work/valkuil/"
    DOCDIR = ROOT_DIR + 'userdocs/'
    CLAMSERVICE = 'http://' + hostname + ':8080'
        
    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash if there is a path component (optional in other cases).
    # Examples: "http://media.lawrence.com", "http://example.com/media/"
    MEDIA_URL = ''
else:
    raise Exception("Don't know where I'm running from!")


# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ROOT_DIR + 'webvalkuil/style/'


# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@r&t#+-0+_v^g_+p^1s&mm-4)33ti0ys^0^$ypb@a7d6-sawxf'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    ROOT_DIR + "webvalkuil/templates",
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'valkuil',
    #'django.contrib.sessions',
    #'django.contrib.sites',
    #'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)
