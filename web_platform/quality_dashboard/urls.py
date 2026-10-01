from django.urls import path
from . import views

app_name = 'quality_dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('batch/<str:batch_id>/', views.batch_detail, name='batch_detail'),
]
