from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'authentication.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'authentication.views.login', name='login'),
    #url(r'^accounts/logout/$', 'django_cas.views.logout'),
    url(r'^admin/', include(admin.site.urls)),
)
