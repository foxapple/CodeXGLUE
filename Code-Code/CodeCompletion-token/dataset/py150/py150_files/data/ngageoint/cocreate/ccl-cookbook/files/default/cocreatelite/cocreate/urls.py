from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import index, profile, playgrounds, sandboxes, api, status, settings
from cocreate import old_views


urlpatterns = [

    # help screens
    url(r'^help/?$', index.help, name="help"),
    # Auth - link to SSO
    url(r'^logout/', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),
    
    # Just our basic index/welcome page
    url(r'^$', index.index, name="home"),
    
    # Settings
    url(r'^settings/proxy$', settings.proxy, name="proxy"),
    url(r'^settings/proxy/edit$', settings.edit_proxy, name="proxy-edit"),
    url(r'^settings/aws$', settings.awsKey, name="awskey"),
    url(r'^settings/aws/edit$', settings.edit_awsKey, name="awskey-edit"),
    
    # Playgrounds
    url(r'^playgrounds/?$', playgrounds.index, name="playgrounds"),
    url(r'^playground/(?P<playground_id>\d+)/?$', playgrounds.playground, name="playground"),
    url(r'^playground/add/?$', playgrounds.add, name="playground-add"),
    url(r'^playground/(?P<playground_id>\d+)/remove/?$', playgrounds.remove, name="playground-remove"),
    url(r'^playground/(?P<playground_id>\d+)/description/edit/?$', playgrounds.editDesc, name="playground-desc-edit"),
    url(r'^playground/(?P<playground_id>\d+)/access/users/alter/?$', playgrounds.alterUserAccess, name="playground-useraccess-alter"),
    url(r'^playground/(?P<playground_id>\d+)/access/groups/alter/?$', playgrounds.alterGroupAccess, name="playground-groupaccess-alter"),
    
    # Sandboxes
    url(r'^playground/(?P<playground_id>\d+)/sandbox/add/?$', sandboxes.add, name="sandbox-add"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/pause$', sandboxes.pause, name="sandbox-pause"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/start$', sandboxes.start, name="sandbox-start"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/reboot$', sandboxes.reboot, name="sandbox-reboot"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/delete$', sandboxes.delete, name="sandbox-delete"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/demo$', sandboxes.toggleDemo, name="sandbox-toggle-demo"),
    url(r'^playground/(?P<playground_id>\d+)/sandbox/(?P<sandbox_id>\d+)/?$', sandboxes.details, name="sandbox-details"),
    
    
    # API
    url(r'^api/aws/instanceTypes/?$', api.aws_instanceTypes, name="api-aws-instancetypes"),
    url(r'^api/isee/instanceTypes/?$', api.isee_instanceTypes, name="api-isee-instancetypes"),
    
    url(r'^api/aws/amis/?$', api.aws_amis, name="api-aws-amis"),
    url(r'^api/aws/vpcs/?$', api.aws_vpcs, name="api-aws-vpcs"),
    url(r'^api/aws/vpc/(?P<vpc_name>([a-zA-Z0-9\-]+))/subnets/?$', api.aws_vpc_subnets, name="api-aws-vpc-subnets"),
    url(r'^api/aws/vpc/(?P<vpc_name>([a-zA-Z0-9\-]+))/secgroups/?$', api.aws_vpc_secgroups, name="api-aws-vpc-secgroups"),
    url(r'^api/aws/create/?$', api.aws_create, name="aws-create"),
    
    url(r'^api/aws/application/(?P<recipe_name>([a-zA-Z0-9\-\:]+))/config$', api.aws_recipeConfig, name="api-aws-recipe-config"),
    url(r'^api/isee/application/(?P<recipe_name>([a-zA-Z0-9\-\:]+))/config$', api.isee_recipeConfig, name="api-isee-recipe-config"),
    
    url(r'^api/chef/cookbooks$', api.chef_cookbooks, name="api-chef-cookbooks"),
    url(r'^api/ssh/keys$', api.keypairs, name="api-ssh-keypairs"),
    url(r'^api/git/repositories$', api.repositories, name="api-git-repositories"),
    
    # Notifications
    url(r'^notifications/?$', index.index, name="notifications"),
    
    # Feedback
    url(r'^feedback/?$', index.index, name="feedback"),
    
    # User Profile
    url(r'^profile/?$', profile.index, name="profile"),
    url(r'^profile/sshkeys/$', profile.sshkeys, name="profile-sshkeys"),
    url(r'^profile/sshkeys/add/?$', profile.addSshKey, name="profile-sshkeys-add"),
    url(r'^profile/sshkeys/remove/(?P<sshkey_id>\d+)?$', profile.removeSshKey, name="profile-sshkeys-remove"),
    url(r'^profile/repositories/$', profile.repositories, name="profile-repositories"),
    url(r'^profile/repositories/add/?$', profile.addRepository, name="profile-repository-add"),
    url(r'^profile/repositories/remove/(?P<repository_id>\d+)?$', profile.removeRepository, name="profile-repository-remove"),
    
    # Data Depot
    url(r'^datadepot/?', index.index, name="data-depot"),

    # Site status and control
    url(r'^status/?$', status.index, name="status"),
    
    # old URI structure
    # url(r'^$', TemplateView.as_view(template_name="index.html"), name="home"),
    url(r'^admin/', include(admin.site.urls)),
    #url(r'^login/', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    
#    url(r'^accounts/profile/$', views.profileView),
    
#    url(r'^sandboxes/request/random/?$', views.requestRandomSandbox),
    #url(r'^sandbox/request/aws/?$', views.requestAWSSandbox),
#    url(r'^sandbox/request$', views.requestSandbox),
#    url(r'^sandbox/submitted', TemplateView.as_view(template_name="sandboxRequestSubmitted.html")),
    
#    url(r'^sandbox/request_aws', views.awsRequestView),
    url(r'^sandbox/status_aws', old_views.awsRequestStatusView),
#    url(r'^sandbox/status/aws/(?P<instance_name>[a-zA-Z0-9\-]+)/?$', views.awsStatusOfInstance),
    
    
    # new URI structure
#    url(r'^$', views.index, name="home"),
    
#    url(r'^playgrounds/', views.playgroundList),
#    url(r'^playground/(?P<playground_id>[0-9]+)/?$', views.playgroundDetails),
#    url(r'^playground/request/random/?$', views.requestRandomPlayground),
#    url(r'^playground/request/?$', views.requestPlayground, name="playground-request"),
#    url(r'^playground/clearall$', views.clearPlaygrounds),
    
#    url(r'^sandbox/(?P<sandbox_id>[0-9]+)/?$', views.sandboxDetails, name="sandbox-details"),
    
#    url(r'^notifications/?$', views.notificationList),
#    url(r'^notifications/mark/read/all', views.notificationMarkAllRead),
    
    # # Registration
    # url('^registration/', include('registration.urls')),
    # url(r'^register/', views.registerView),
    
    # Feedback
#    url(r'^feedback/', views.feedbackView),
    
    # Account profile
#    url(r'^accounts/profile/', views.profileView),
    
#    url(r'^user/sshkey/add', views.addSshKey),
#    url(r'^user/sshkey/remove/(?P<sshkey_id>\d+)', views.removeSshKey),
    
#    url(r'^user/(?P<user_id>\d+)/sshkey/list', views.listSshKeys),
#    url(r'^user/(?P<user_id>\d+)/sshkey/(?P<sshkey_id>\d+)/get', views.getSshKey),
    
    # Data depot
#    url(r'^datadepot/', views.dataDepotView),
]

