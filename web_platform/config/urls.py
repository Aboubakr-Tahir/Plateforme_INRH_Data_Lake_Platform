from django.urls import include, path


urlpatterns = [
    path("", include("quality_dashboard.urls")),
    path("business/", include("business_dashboard.urls")),
]