from django.conf import settings
from django.contrib.gis.geos import Point
from django.views.generic import ListView, DetailView

from inspections.models import Establishment


class EstablishmentList(ListView):
    model = Establishment
    context_object_name = 'establishments'
    template_name = 'inspections/establishment_list.html'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        objects = self.model.objects.all()
        user_location = self.get_user_location()
        objects = objects.distance(user_location).order_by('distance')
        if query:
            objects = objects.filter(name__icontains=query)
        objects = objects.filter(status='active', type=1)
        objects = objects.extra(
            select={
	    'grade': "SELECT score FROM inspections_inspection WHERE inspections_inspection.establishment_id = inspections_establishment.id AND inspections_inspection.type = '1' ORDER BY inspections_inspection.date DESC LIMIT 1",
	    'insp_date': "SELECT date FROM inspections_inspection WHERE inspections_inspection.establishment_id = inspections_establishment.id AND inspections_inspection.type = '1' ORDER BY inspections_inspection.date DESC LIMIT 1"
            },
        )
        return objects

    def get_user_location(self):
        """Returns a Point object that represent the location of a user, if
        the user did not allow us to use his location it returns a Point with
        a default predefined location."""
        session = self.request.session
        lat = float(session.get('location', {}).get('lat', settings.LATITUDE))
        lon = float(session.get('location', {}).get('lon', settings.LONGITUDE))
        return Point(lon, lat)


class EstablishmentDetail(DetailView):
    model = Establishment
    context_object_name = 'establishment'

    def get_context_data(self, **kwargs):
        context = super(EstablishmentDetail, self).get_context_data(**kwargs)
        establishment = context['establishment']
        inspections = establishment.inspections.prefetch_related('violations')
        inspections = inspections.order_by('-date')
        try:
            context['latest'] = inspections.filter(type=1)[0]
        except IndexError:
            context['latest'] = None
        context['inspections'] = inspections
        return context
