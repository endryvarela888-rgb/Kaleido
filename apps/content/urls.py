from django.urls import path

from . import views

app_name = 'creator_content'

urlpatterns = [
    path('', views.creator_content_new, name='new'),
    path('manage/', views.creator_content_list, name='list'),
    path('<int:pk>/edit/', views.creator_content_edit, name='edit'),
    path('<int:pk>/delete/', views.creator_content_delete, name='delete'),
    path('collections/', views.creator_collection_list, name='collection_list'),
    path('collections/<int:pk>/edit/', views.creator_collection_edit, name='collection_edit'),
]