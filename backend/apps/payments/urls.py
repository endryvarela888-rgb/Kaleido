from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:tier_id>/', views.create_checkout_session, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('checkout/cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('creator/stats/', views.creator_stats, name='creator_stats'),
    path('creator/payouts/', views.creator_payouts, name='creator_payouts'),
    path('creator/payouts/connect/', views.creator_payouts_connect, name='creator_payouts_connect'),
]