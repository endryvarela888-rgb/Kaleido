from django.urls import path

from . import api_views

app_name = 'content_api'

urlpatterns = [
    path('feed/', api_views.ContentFeedView.as_view(), name='feed'),
    path('categories/', api_views.CategoryListView.as_view(), name='categories'),
    path('<int:pk>/', api_views.ContentDetailView.as_view(), name='detail'),
    path('<int:pk>/like/', api_views.ToggleLikeView.as_view(), name='like'),
    path('<int:pk>/comments/', api_views.CommentListCreateView.as_view(), name='comments'),
    path('<int:pk>/save/', api_views.ToggleSavedContentView.as_view(), name='save'),
    path('collections/<int:pk>/', api_views.CollectionDetailView.as_view(), name='collection_detail'),
    path('collections/<int:pk>/save/', api_views.ToggleSavedCollectionView.as_view(), name='collection_save'),
    path('<int:pk>/history/', api_views.HistoryProgressView.as_view(), name='history_progress'),
    path('history/', api_views.HistoryView.as_view(), name='history'),
    path('saved/', api_views.SavedItemsView.as_view(), name='saved'),
    path('creator/content/', api_views.CreatorContentListView.as_view(), name='creator_content'),
    path('creator/content/<int:pk>/', api_views.CreatorContentDetailView.as_view(), name='creator_content_detail'),
    path('creator/collections/', api_views.CreatorCollectionListView.as_view(), name='creator_collections'),
    path('creator/collections/<int:pk>/', api_views.CreatorCollectionDetailView.as_view(), name='creator_collection_detail'),
]
