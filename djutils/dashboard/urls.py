from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^$', 'djutils.dashboard.views.dashboard', name='djutils_dashboard_dashboard'),
)
