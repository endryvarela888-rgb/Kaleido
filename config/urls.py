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
    path('creator/', include('apps.content.urls', namespace='creator_content')),
    path('creator/tiers/', include('apps.tiers.urls', namespace='creator_tiers')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)