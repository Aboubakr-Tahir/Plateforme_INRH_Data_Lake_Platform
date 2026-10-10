from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="quality_home"),
    path("pipeline/start/", views.start_pipeline, name="start_pipeline"),
    path("pipeline/status/<str:batch_id>/", views.pipeline_status, name="pipeline_status"),
    path("batch/<str:batch_id>/", views.batch_detail, name="batch_detail"),
]