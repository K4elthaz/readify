from django.urls import path

from app.views import LandingPageView, homepage, DashboardView, analytics_service

urlpatterns = [
    path("", LandingPageView.as_view(), name="home"),
    path("home", homepage, name="homepage"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("analytics", analytics_service, name="analytics_service"),
]
