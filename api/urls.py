from django.conf.urls import patterns, include, url

from api.views import hotspot

urlpatterns = patterns('',
    url(r'^hotspot/(?P<id>\d+)/?$', hotspot),
    url(r'^hotspots/(?P<id>\d+)/?$', hotspot),
)