from django.conf.urls import patterns, url
from .views import MarkdownToHtmlView


urlpatterns = patterns('',
    url('^markdown/$', MarkdownToHtmlView.as_view(), name='markdown-to-html'),
)
