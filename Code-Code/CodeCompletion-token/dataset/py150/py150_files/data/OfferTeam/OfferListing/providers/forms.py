from django import forms
from django.forms.models import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit
from .models import Provider, Location, TestDownload, TestIP


class ProviderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProviderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["start_date"].help_text = "The date your company started."
        self.fields["tos"].help_text = \
            "A link to your terms of service that will be displayed at the bottom of each offer."

        self.helper.layout = Layout(
            Fieldset(
                'General',
                'name',
                'website',
                'start_date'
            ),
            Fieldset(
                'Legal',
                'tos',
                'aup',
                'sla',
                'billing_agreement'
            ),
            Fieldset(
                'Other',
                'logo'
            )
        )

        self.helper.add_input(Submit('save', 'Save Profile'))

    class Meta:
        model = Provider
        fields = ('name', 'start_date', 'website', 'tos', 'aup', 'sla', 'billing_agreement', 'logo')


# Locations
class LocationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields['looking_glass'].help_text = "The url to your looking glass installation. Not required."

    class Meta:
        model = Location
        fields = ('city', 'country', 'datacenter', 'looking_glass')


TestIPFormsetBase = inlineformset_factory(Location, TestIP, extra=4, fields=('ip', 'ip_type'), fk_name='location')
TestDownloadFormsetBase = inlineformset_factory(
    Location,
    TestDownload,
    extra=4,
    fields=('url', 'size'),
    fk_name='location',
)


class TestIPFormset(TestIPFormsetBase):

    def __init__(self, *args, **kwargs):
        super(TestIPFormset, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.template = 'offers/better_table_inline_form.html'
        self.helper.form_tag = False


class TestDownloadFormset(TestDownloadFormsetBase):

    def __init__(self, *args, **kwargs):
        super(TestDownloadFormset, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.template = 'offers/better_table_inline_form.html'
        self.helper.form_tag = False

        for form in self:
            form.fields["size"].label = 'Size (MB)'