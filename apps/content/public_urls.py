from django.urls import path

from . import views

app_name = 'content'

urlpatterns = [
    path('collections/<int:pk>/', views.public_collection_detail, name='collection_detail'),
    path('content/<int:pk>/', views.public_content_detail, name='content_detail'),
]
