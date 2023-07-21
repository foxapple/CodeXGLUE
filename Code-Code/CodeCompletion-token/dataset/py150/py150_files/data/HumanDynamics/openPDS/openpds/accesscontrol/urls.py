from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
#from openpds.meetup.views import update_approval_status, contribute_to_scheduling, create_request, meetup_home
from openpds.accesscontrol.views import storeAccessControl, deleteAccessControl, loadAccessControl, globalAccessControl

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('openpds.accesscontrol.views',
    (r'^store/$', storeAccessControl),
    (r'^load/$', loadAccessControl),
    (r'^delete/$', deleteAccessControl),
    (r'^global/$', globalAccessControl),
)

