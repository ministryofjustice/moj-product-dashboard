"""dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf import settings
from django.contrib import admin
from moj_irat.views import PingJsonView, HealthcheckView

from dashboard.apps.prototype.views import (
    index, service_html, service_json, project_html, project_json,
    project_group_json, project_group_html,
    portfolio_html, portfolio_json, sync_from_float)
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^sync.json$', sync_from_float, name='sync'),
    url(r'^services/(?P<id>[0-9]+)?$', service_html, name='service'),
    url(r'^service.json', service_json, name='service_json'),
    url(r'^projects/(?P<id>[0-9]+)?$', project_html, name='project'),
    url(r'^project-groups/(?P<id>[0-9]+)?$', project_group_html,
        name='project_group'),
    url(r'^project.json', project_json, name='project_json'),
    url(r'^project-group.json', project_group_json, name='project_group_json'),
    url(r'^portfolio.json', portfolio_json, name='portfolio_json'),
    url(r'^portfolio', portfolio_html, name='portfolio_html'),
    url(r'^admin/', admin.site.urls),
    url(r'^login/', auth_views.login),
    url(r'^logout/', auth_views.logout, kwargs={'next_page': '/'}),
    url(r'^password_change/', auth_views.password_change),
    url(r'^ping.json$', PingJsonView.as_view(**settings.PING_JSON_KEYS),
        name='ping_json'),
    url(r'^healthcheck.json$', HealthcheckView.as_view(),
        name='healthcheck_json'),
]
