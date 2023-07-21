from django.views.generic.list import ListView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from offers.models import Offer
from .models import Provider


class ProviderListView(ListView):
    """
    Displays a list of all providers on the site
    """
    model = Provider
    template_name = "providers/providers.html"
    paginate_by = 10

    def get_queryset(self):
        return self.model.objects.order_by('name')


def provider_profile(request, provider_name):
    """
    Displays the profile of a provider, including recent offers
    """
    provider = get_object_or_404(Provider, name_slug=provider_name)
    offer_list = Offer.visible_offers.for_provider(provider)

    paginator = Paginator(offer_list, 5)
    page = request.GET.get('page')
    try:
        offers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        offers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        offers = paginator.page(paginator.num_pages)

    return render(request, "offers/provider.html", {
        "provider": provider,
        "offers": offers,
    })
