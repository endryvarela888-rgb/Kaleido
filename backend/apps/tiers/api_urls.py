from django.urls import path

from . import api_views

app_name = 'tiers_api'

urlpatterns = [
    path('', api_views.TierListView.as_view(), name='list'),
    path('<int:pk>/', api_views.TierDetailView.as_view(), name='detail'),
]
