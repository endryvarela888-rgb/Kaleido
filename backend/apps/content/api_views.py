from django.db.models import Count, Exists, OuterRef, Subquery, Value
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .access import annotate_lock_state
from .models import Category, Collection, Comment, Content, ContentHistory, ContentLike, SavedItem
from .queries import social_queryset, visible_content_filter
from .serializers import (
    CategorySerializer, CollectionSerializer, CommentSerializer, ContentSerializer,
    CreatorCollectionSerializer, CreatorContentSerializer,
)


def public_content_queryset(request):
    """One canonical public queryset so API cards and detail pages agree."""
    return social_queryset(
        request,
        Content.objects.filter(visible_content_filter()).select_related(
            'creator', 'creator__creator_profile',
            'creator__creator_profile__category', 'minimum_tier', 'collection',
        ),
    )


def content_or_404(request, pk):
    item = get_object_or_404(public_content_queryset(request), pk=pk)
    annotate_lock_state(request, [item])
    return item


class IsCreator(permissions.BasePermission):
    message = 'Creator accounts are required for this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_creator)


class ContentFeedView(generics.ListAPIView):
    """Powers the home feed. Supports ?q= and ?category= just like the
    Django template version did — same filtering rules, now over JSON."""

    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = public_content_queryset(self.request).order_by('-created_at')

        query = self.request.query_params.get('q', '').strip()
        category = self.request.query_params.get('category', '').strip()
        if query:
            queryset = queryset.filter(creator__display_name__icontains=query)
        if category:
            queryset = queryset.filter(creator__creator_profile__category__slug=category)

        return queryset

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is not None:
            annotate_lock_state(self.request, page)
        return page


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ContentDetailView(generics.RetrieveAPIView):
    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return content_or_404(self.request, self.kwargs['pk'])


class ToggleLikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        content = content_or_404(request, pk)
        if content.is_locked:
            return Response({'detail': 'Subscribe to interact with this content.'}, status=status.HTTP_403_FORBIDDEN)
        _, created = ContentLike.objects.get_or_create(content=content, user=request.user)
        if not created:
            ContentLike.objects.filter(content=content, user=request.user).delete()
        return Response({'liked': created, 'count': ContentLike.objects.filter(content=content).count()})


class CommentListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        content_or_404(request, pk)
        comments = Comment.objects.filter(content_id=pk).select_related('author').order_by('created_at')
        return Response(CommentSerializer(comments, many=True, context={'request': request}).data)

    def post(self, request, pk):
        content = content_or_404(request, pk)
        if content.is_locked:
            return Response({'detail': 'Subscribe to comment on this content.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(content=content, author=request.user)
        return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ToggleSavedContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        content_or_404(request, pk)
        saved, created = SavedItem.objects.get_or_create(user=request.user, content_id=pk)
        if not created:
            saved.delete()
        return Response({'saved': created})


class CollectionDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        collection = get_object_or_404(
            Collection.objects.select_related('creator', 'creator__creator_profile', 'creator__creator_profile__category', 'minimum_tier')
            .annotate(item_count=Count('items', filter=visible_content_filter(prefix='items__'))),
            pk=pk,
        )
        items = list(social_queryset(request, collection.items.filter(visible_content_filter()).select_related(
            'creator', 'creator__creator_profile', 'creator__creator_profile__category', 'minimum_tier', 'collection',
        ).order_by('order', '-created_at')))
        annotate_lock_state(request, items)
        return Response({
            'collection': CollectionSerializer(collection, context={'request': request}).data,
            'content': ContentSerializer(items, many=True, context={'request': request}).data,
        })


class ToggleSavedCollectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        get_object_or_404(Collection, pk=pk)
        saved, created = SavedItem.objects.get_or_create(user=request.user, collection_id=pk)
        if not created:
            saved.delete()
        return Response({'saved': created})


class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = ContentHistory.objects.filter(
            user=request.user, content__isnull=False, content__in=Content.objects.filter(visible_content_filter()),
        ).select_related('content', 'content__creator', 'content__creator__creator_profile', 'content__creator__creator_profile__category', 'content__minimum_tier', 'content__collection').order_by('-last_viewed_at')
        items = [entry.content for entry in entries]
        annotate_lock_state(request, items)
        data = ContentSerializer(items, many=True, context={'request': request}).data
        for entry, item in zip(entries, data):
            item['history'] = {
                'last_viewed_at': entry.last_viewed_at,
                'progress_seconds': entry.progress_seconds,
                'duration_seconds': entry.duration_seconds,
                'completed': entry.completed,
            }
        return Response(data)


class HistoryProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        content = content_or_404(request, pk)
        if content.is_locked:
            return Response({'detail': 'Subscribe to watch this content.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            position = max(0, float(request.data.get('position', 0)))
            duration_raw = request.data.get('duration')
            duration = max(0, float(duration_raw)) if duration_raw is not None else None
        except (TypeError, ValueError):
            return Response({'detail': 'Position and duration must be numbers.'}, status=status.HTTP_400_BAD_REQUEST)
        completed = bool(request.data.get('completed', False)) or bool(duration and position >= max(duration - 2, 0))
        history, _ = ContentHistory.objects.get_or_create(user=request.user, content=content)
        history.progress_seconds, history.duration_seconds, history.completed = position, duration, completed
        history.save(update_fields=['last_viewed_at', 'progress_seconds', 'duration_seconds', 'completed'])
        return Response({'saved': True, 'completed': completed})


class SavedItemsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        content_saves = SavedItem.objects.filter(user=request.user, content__isnull=False)
        content_items = list(social_queryset(request, Content.objects.filter(
            visible_content_filter(), id__in=content_saves.values('content_id'),
        ).select_related('creator', 'creator__creator_profile', 'creator__creator_profile__category', 'minimum_tier', 'collection').annotate(
            saved_at=Subquery(content_saves.filter(content_id=OuterRef('pk')).values('created_at')[:1]),
        ).order_by('-saved_at')))
        annotate_lock_state(request, content_items)
        collection_saves = SavedItem.objects.filter(user=request.user, collection__isnull=False)
        collections = Collection.objects.filter(id__in=collection_saves.values('collection_id')).select_related(
            'creator', 'creator__creator_profile', 'creator__creator_profile__category', 'minimum_tier',
        ).annotate(item_count=Count('items', filter=visible_content_filter(prefix='items__'))).order_by('-created_at')
        return Response({
            'content': ContentSerializer(content_items, many=True, context={'request': request}).data,
            'collections': CollectionSerializer(collections, many=True, context={'request': request}).data,
        })


class CreatorContentListView(generics.ListCreateAPIView):
    permission_classes = [IsCreator]
    pagination_class = None

    def get_queryset(self):
        return Content.objects.filter(creator=self.request.user).select_related('collection', 'minimum_tier').order_by('-created_at')

    def get_serializer_class(self):
        return CreatorContentSerializer if self.request.method == 'POST' else ContentSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class CreatorContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCreator]

    def get_queryset(self):
        return Content.objects.filter(creator=self.request.user).select_related('collection', 'minimum_tier')

    def get_serializer_class(self):
        return CreatorContentSerializer if self.request.method in ('PUT', 'PATCH') else ContentSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class CreatorCollectionListView(generics.ListCreateAPIView):
    permission_classes = [IsCreator]
    serializer_class = CreatorCollectionSerializer
    pagination_class = None

    def get_queryset(self):
        return Collection.objects.filter(creator=self.request.user).annotate(item_count=Count('items')).order_by('-created_at')

    def get_serializer_context(self):
        return {'request': self.request}


class CreatorCollectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCreator]
    serializer_class = CreatorCollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(creator=self.request.user).annotate(item_count=Count('items'))

    def get_serializer_context(self):
        return {'request': self.request}
