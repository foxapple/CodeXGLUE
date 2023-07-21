from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import SandboxRequest, Playground, Sandbox, SshKey, VMPlayground, Repository, UserConfig

class ProxyForm(forms.Form):
    http_proxy = forms.CharField(label="Http Proxy", max_length=100)
    https_proxy = forms.CharField(label="Https Proxy", max_length=100)

class AwsForm(forms.Form):
    aws_public = forms.CharField(label="Access Key", max_length=100)
    aws_secret = forms.CharField(label="Secret Key", max_length=200)
    
class UserConfigForm(forms.ModelForm):
    class Meta:
        model = UserConfig
        fields = ['val']
        labels = {
            'val': ""
        }
        
class RepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ['name', 'uri']
        labels = {
            'name': "Repository Name",
            'uri': "Repository Git URI"
        }
        
class SshKeyForm(forms.ModelForm):
    class Meta:
        model = SshKey
        fields = ['name', 'key']
        labels = {
            'name': "Key Name",
            'key': "SSH Public Key"
        }

class VMPlaygroundForm(forms.ModelForm):
    class Meta:
        model = VMPlayground
        fields = ['name', 'environment', 'description_is_markdown', 'description']
        labels = {
            'description_is_markdown': _("Description contains Markdown?")
        }

class VMPlaygroundDescriptionForm(forms.ModelForm):
    class Meta:
        model = VMPlayground
        fields = ['description_is_markdown', 'description']
        labels = {
            'description_is_markdown': _("Description contains Markdown?")
        }

class VMPlaygroundUserAccessForm(forms.ModelForm):
    class Meta:
        model = VMPlayground
        fields = ['access_users']
        labels = {
            'access_users': _("Users with Playground Access")
        }

class VMPlaygroundGroupAccessForm(forms.ModelForm):
    class Meta:
        model = VMPlayground
        fields = ['access_groups']
        labels = {
            'access_groups': _("Groups with Playground Access")
        }
        
class SandboxRequestForm(forms.ModelForm):
    class Meta:
        model = SandboxRequest
        fields = '__all__'
        exclude = ['request_status', 'sandbox', 'requested_by', 'request_progress', 'request_progress_msg']
        widgets = {
            'justification': forms.Textarea(attrs={'cols': 30, 'rows': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SandboxRequestForm, self).__init__(*args, **kwargs)
        
    def clean_sandbox_name(self):
        data = self.cleaned_data['sandbox_name']
        playground_id = self.request.session['current_playground_id']
        if Sandbox.objects.filter(name=data).filter(playground=playground_id):
            raise forms.ValidationError("That sandbox name is already in use in this playground. Please specify a different name.")

        return data

class PlaygroundForm(forms.ModelForm):
    class Meta:
        model = Playground
        fields = "__all__"
        exclude = ["owner"]
        
    def clean_name(self):
        data = self.cleaned_data['name']
        if Playground.objects.filter(name=data):
            raise forms.ValidationError("That playground name is already in use. Please specify a different name.")

        return data
