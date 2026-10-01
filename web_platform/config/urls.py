from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('quality_dashboard:home')),
    path('quality/', include('quality_dashboard.urls')),
    path('business/', include('business_dashboard.urls')),
]
