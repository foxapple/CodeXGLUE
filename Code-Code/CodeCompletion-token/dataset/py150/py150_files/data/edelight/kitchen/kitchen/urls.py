"""Root URL routing"""
from django.conf.urls import patterns
from django.conf.urls.static import static
from django.views.generic import TemplateView

from kitchen.dashboard import api
import kitchen.settings as settings


if settings.SHOW_LIST_VIEW:
    root_view = 'kitchen.dashboard.views.list'
elif settings.SHOW_VIRT_VIEW:
    root_view = 'kitchen.dashboard.views.virt'
elif settings.SHOW_GRAPH_VIEW:
    root_view = 'kitchen.dashboard.views.graph'
else:
    raise Exception("No views enabled! Please edit settings.py.")


urlpatterns = patterns('',
    (r'^$', root_view),
    (r'^virt/$', 'kitchen.dashboard.views.virt'),
    (r'^graph/$', 'kitchen.dashboard.views.graph'),
    (r'^plugins/((?P<plugin_type>(virt|v|list|l))/)?(?P<name>[\w\-\_]+)/(?P<method>\w+)/?$', 'kitchen.dashboard.views.plugins'),
    (r'^api/nodes/(?P<name>\w+)$', api.get_node),
    (r'^api/nodes', api.get_nodes),
    (r'^api/roles', api.get_roles),
    (r'^404', TemplateView.as_view(template_name="404.html")),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
