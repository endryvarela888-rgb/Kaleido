from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.my_subscriptions, name='my_subscriptions'),
    path('<int:subscription_id>/cancel/', views.cancel_subscription, name='cancel'),
    path('<int:subscription_id>/renew/', views.renew_subscription, name='renew'),
]