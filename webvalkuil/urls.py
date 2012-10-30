from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',    
    (r'^$','valkuil.views.start'),
    (r'^info/?$','valkuil.views.about'),
    (r'^help/?$','valkuil.views.help'),
    (r'^process/?$','valkuil.views.process'),
    (r'^(?P<id>D[0-9a-f]+)/correct/?$','valkuil.views.correct'), 
    (r'^(?P<id>D[0-9a-f]+)/ignore/?$','valkuil.views.ignore'), 
    (r'^(?P<id>D[0-9a-f]+)/text/?$','valkuil.views.text'), 
    (r'^(?P<id>D[0-9a-f]+)/xml/?$','valkuil.views.xml'), 
    (r'^(?P<id>D[0-9a-f]+)/log/?$','valkuil.views.log'), 
    (r'^(?P<id>D[0-9a-f]+)/?$','valkuil.views.viewer'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
