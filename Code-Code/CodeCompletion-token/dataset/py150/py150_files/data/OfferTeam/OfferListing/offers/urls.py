from django.conf.urls import patterns, url, include
from haystack.views import search_view_factory, SearchView
from offers.feeds import OfferFeed, OfferAtomFeed
from offers.forms import OfferSearchForm
from . import views as offer_views


urlpatterns = patterns('offers.views',
    url(r'^view/(?P<offer_pk>\d+)/$', 'view_offer', name='view'),
    url(r'^view/(?P<offer_pk>\d+)-(?P<slug>[-\w]+)/$', 'view_offer', name='view_slug'),
    url(r'^comment/like/(?P<comment_pk>\d+)/', 'like_comment', name="like"),

    url(r'^search/$', search_view_factory(
            view_class=SearchView,
            form_class=OfferSearchForm,
            template='offers/search.html',
            results_per_page=8,
        ),
        name='search',
    ),

    url(r'^feed/', OfferFeed(), name='rss'),
    url(r'^atom/', OfferAtomFeed(), name='atom'),

    url(r'^manage/$', 'admin_provider_home', name="admin_home"),

    url(r'^manage/requests/$', 'admin_provider_requests', name="admin_requests"),
    url(r'^manage/request/$', 'admin_submit_request', name="admin_request_new"),
    url(r'^manage/request/(?P<offer_pk>\d+)/$', 'admin_edit_request', name="admin_request_edit"),
    url(r'^manage/request/(?P<offer_pk>\d+)/delete/$', 'admin_provider_delete_confirm', name="admin_request_delete"),
    url(r'^manage/request/(?P<offer_pk>\d+)/mark/$', 'admin_mark_request', name="admin_request_mark"),
    url(r'^manage/request/(?P<offer_pk>\d+)/preview/$', 'admin_preview_request', name="admin_request_preview"),

    url(r'^manage/offers/$', 'admin_provider_offer_list', name="admin_offers"),
    url(r'^manage/offer/(?P<offer_pk>\d+)/$', 'admin_provider_offer_edit', name="admin_offer"),
    url(r'^manage/offer/(?P<offer_pk>\d+)/mark/$', 'admin_provider_offer_mark', name="admin_offer_mark"),
    url(
        r'^manage/offer/(?P<offer_pk>\d+)/mark/(?P<plan_pk>\d+)$',
        'admin_provider_offer_plan_mark',
        name="admin_offer_plan_mark"
    ),
    url(r'^manage/offer/(?P<offer_pk>\d+)/update/$', 'admin_provider_update_offer', name="admin_offer_update"),

    url(r'^manage/locations/$', 'admin_provider_locations', name="admin_locations"),
    url(r'^manage/location/(?P<location_pk>\d+)/$', 'admin_provider_locations_edit', name="admin_location_edit"),
    url(r'^manage/location/new/$', 'admin_provider_locations_new', name="admin_location_new"),

)
