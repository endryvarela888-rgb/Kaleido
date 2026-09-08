from django.urls import path

from . import views

app_name = 'content'

urlpatterns = [
    path('history/', views.history, name='history'),
    path('saved/', views.saved_for_later, name='saved'),
    path('collections/<int:pk>/', views.public_collection_detail, name='collection_detail'),
    path('content/<int:pk>/', views.public_content_detail, name='content_detail'),
    path('content/<int:pk>/like/', views.toggle_like, name='content_like'),
    path('content/<int:pk>/save/', views.toggle_content_save, name='content_save'),
    path('content/<int:pk>/history/', views.update_content_history, name='content_history'),
    path('content/<int:pk>/comment/', views.create_comment, name='content_comment'),
    path('collections/<int:pk>/save/', views.toggle_collection_save, name='collection_save'),
]
