"""
URL configuration for blendjoy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView

from app.admin import list_admin_path_names

urlpatterns = [
    path("tinymce/", include("tinymce.urls")),
    path("admin/", include("loginas.urls")),
    path("admin/", admin.site.urls),
    path("path-names/", list_admin_path_names, name="admin-path-names"),
    path("", include("app.urls")),
    path("", include("app.authentication.urls")),
    path("", include("app.books.urls")),
    path("", include("app.forum.urls")),
    path("", include("app.social_newsfeed.urls")),
    path("", include("app.rewards.urls")),
    path("", include("app.notifications.urls")),
    path("", include("app.chat.urls")),
    path("", include("pwa.urls")),
]
