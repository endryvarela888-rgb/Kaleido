from django.urls import path

from . import api_views

app_name = 'subscriptions_api'

urlpatterns = [
    path('', api_views.MySubscriptionsView.as_view(), name='list'),
    path('<int:pk>/<str:action>/', api_views.SubscriptionActionView.as_view(), name='action'),
]
