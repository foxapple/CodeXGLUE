from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

from intranet.org.feeds import LatestDiarys, LatestEvents
from intranet.org.views import (DetailDiary, UpdateShopping,
                                ArchiveIndexEvent, CreateShopping,
                                ArchiveIndexDiary, CreateLend, UpdateLend,
                                MonthArchiveEvent, YearArchiveEvent,
                                MonthArchiveDiary, YearArchiveDiary)
from pipa.ldap.forms import LoginForm


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'intranet.org.views.index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ldappass/', 'pipa.ldap.views.password_change', name='ldap_password_change'),

    url(r'^events/$', login_required(ArchiveIndexEvent.as_view()), name="event_list"),
    url(r'^events/arhiv/(?P<year>\d{4})/$', login_required(YearArchiveEvent.as_view()), name="event_arhive_year"),
    url(r'^events/arhiv/(?P<year>\d{4})/(?P<month>[a-z]{3}|[0-9]{1,2})/$', login_required(MonthArchiveEvent.as_view()), name="event_arhive_month"),
    url(r'^events/create/', 'intranet.org.views.event_edit', name="event_create"),
    url(r'^events/(?P<event_pk>\d+)/edit/$', 'intranet.org.views.event_edit', name="event_edit"),
    url(r'^events/(?P<event_pk>\d+)/diary/edit/$', 'intranet.org.views.event_diary_edit', name="event_diary_edit"),
    url(r'^events/(?P<event_id>\d+)/count/$', 'intranet.org.views.event_count'),
    url(r'^events/(?P<event_id>\d+)/emails/$', 'intranet.org.views.add_event_emails'),
    url(r'^events/(?P<pk>\d+)/technician/take/$', 'intranet.org.views.event_technician_take', name="event_technician_take"),
    url(r'^events/(?P<pk>\d+)/technician/cancel/$', 'intranet.org.views.event_technician_cancel', name="event_technician_cancel"),
    url(r'^events/(?P<pk>\d+)/officer/take/$', 'intranet.org.views.event_officer_take', name="event_officer_take"),
    url(r'^events/(?P<pk>\d+)/officer/cancel/$', 'intranet.org.views.event_officer_cancel', name="event_officer_cancel"),
    url(r'^events/pr/(?P<year>\d{4})/(?P<week>\d{1,2})/$', 'intranet.org.views.event_template'),
    url(r'^events/pr/$', 'intranet.org.views.event_template'),

    url(r'^diarys/$', login_required(ArchiveIndexDiary.as_view()), name="diary_list"),
    url(r'^diarys/add/$', 'intranet.org.views.diarys_form', name="diary_add"),
    url(r'^diarys/(?P<pk>\d+)/$', login_required(DetailDiary.as_view())),
    url(r'^diarys/(?P<id>\d+)/edit/$', 'intranet.org.views.diarys_form', name="diary_edit"),
    (r'^diarys/commit_hook/$', 'intranet.org.views.commit_hook'),
    (r'^diarys/arhiv/(?P<year>\d{4})/$', login_required(YearArchiveDiary.as_view())),
    (r'^diarys/arhiv/(?P<year>\d{4})/(?P<month>[a-z]{3}|[0-9]{1,2})/$', login_required(MonthArchiveDiary.as_view())),

    url(r'^shopping/$', login_required(CreateShopping.as_view()), name="shopping_index"),
    url(r'^shopping/(?P<pk>\d+)/$', login_required(UpdateShopping.as_view()), name="shopping_detail"),
    url(r'^shopping/(?P<id>\d+)/buy/$', 'intranet.org.views.shopping_buy', name="shopping_buy"),
    url(r'^shopping/(?P<id>\d+)/support/$', 'intranet.org.views.shopping_support', name="shopping_support"),
    url(r'^shopping/(?P<id>\d+)/responsible/$', 'intranet.org.views.shopping_responsible', name="shopping_responsible"),

    url(r'^lend/$', login_required(CreateLend.as_view()), name="lend_index"),
    url(r'^lend/(?P<pk>\d+)/$', login_required(UpdateLend.as_view()), name="lend_detail"),
    url(r'^lend/(?P<id>\d+)/back/$', 'intranet.org.views.lend_back', name="lend_back"),

    (r'^tmp_upload/', 'intranet.org.views.temporary_upload'),
    (r'^image_crop_tool/resize/', 'intranet.org.views.image_resize'),
    (r'^image_crop_tool/save/', 'intranet.org.views.image_save'),
    (r'^image_crop_tool/$', 'intranet.org.views.image_crop_tool'),

    (r'^dezurni/$', 'intranet.org.views.dezurni'),
    (r'^dezurni/add/$', 'intranet.org.views.dezurni_add'),
    (r'^dezurni/(?P<year>\d+)/(?P<month>[a-z]{3})/$', 'intranet.org.views.dezurni_monthly'),
    (r'^dezurni/(?P<year>\d+)/(?P<week>\d+)/$', 'intranet.org.views.dezurni'),

    url(r'^member/add$', 'intranet.org.views.add_member', name="add_member"),

    (r'^scratchpad/change/$', 'intranet.org.views.scratchpad_change'),
    url(r'^statistika/(?P<year>\d{4})?', 'intranet.org.views.year_statistics', name='statistics_by_year'),

    # rss
    (r'^feeds/diarys/', LatestDiarys()),
    (r'^feeds/events/', LatestEvents()),

    (r'^addressbook/$', 'pipa.addressbook.views.addressbook'),
    (r'^mercenaries/', include('pipa.mercenaries.urls')),
    url(r'^accounts/login/$', 'pipa.ldap.views.login', {'authentication_form': LoginForm}, name="account_login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name="account_logout"),
    (r'^wiki/$', RedirectView.as_view(url='https://wiki.kiberpipa.org/')),
)
