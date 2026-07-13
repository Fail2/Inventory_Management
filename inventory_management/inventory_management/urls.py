"""
URL configuration for inventory_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve


def health_check(request):
    """Dedicated health-check endpoint. Render's internal health checker
    hits this directly over plain HTTP (bypassing the HTTPS-terminating
    edge proxy), so it must return a plain 200 with no redirect at all -
    this path is also listed in SECURE_REDIRECT_EXEMPT for that reason."""
    return HttpResponse("OK")


urlpatterns = [
    # The bare root has no page of its own - send human visitors to the
    # storefront. Not used for the health check (see health_check above).
    path('', RedirectView.as_view(pattern_name='buyer_home', permanent=False)),
    path('healthz/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/',include('accounts.urls')),
]

# Serve uploaded product images in every environment. Django's static() url
# helper (the usual dev-only shortcut) silently no-ops whenever DEBUG=False,
# which meant product pictures returned 404 in production with no media/
# route at all. There's no CDN/S3 in front of this app, so Django serves
# media directly - fine at this project's scale, though it does mean
# uploaded files live on Render's ephemeral disk (see deployment notes).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
