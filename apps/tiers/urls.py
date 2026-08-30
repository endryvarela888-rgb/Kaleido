from django.urls import path

from . import views

app_name = 'creator_tiers'

urlpatterns = [
    path('', views.creator_tier_list, name='list'),
    path('<int:pk>/edit/', views.creator_tier_edit, name='edit'),
    path('<int:pk>/deactivate/', views.creator_tier_deactivate, name='deactivate'),
]