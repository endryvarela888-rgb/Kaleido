from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='core')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('subscriptions/', include('apps.subscriptions.urls', namespace='subscriptions')),
    path('', include('apps.content.public_urls', namespace='content')),
    path('creator/', include('apps.content.urls', namespace='creator_content')),
    path('creator/tiers/', include('apps.tiers.urls', namespace='creator_tiers')),
    path('api/content/', include('apps.content.api_urls', namespace='content_api')),
    path('api/subscriptions/', include('apps.subscriptions.api_urls', namespace='subscriptions_api')),
    path('api/creator/tiers/', include('apps.tiers.api_urls', namespace='tiers_api')),
    path('api/payments/', include('apps.payments.api_urls', namespace='payments_api')),


    # API (consumed by the React frontend)
    path('api/users/', include('apps.users.api_urls', namespace='users_api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
