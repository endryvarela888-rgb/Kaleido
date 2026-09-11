from django.urls import path

from . import api_views

app_name = 'payments_api'

urlpatterns = [
    path('checkout/<int:tier_id>/', api_views.CheckoutView.as_view(), name='checkout'),
    path('creator/stats/', api_views.CreatorStatsView.as_view(), name='creator_stats'),
    path('creator/payouts/', api_views.CreatorPayoutsView.as_view(), name='creator_payouts'),
    path('creator/payouts/connect/', api_views.CreatorPayoutsConnectView.as_view(), name='creator_payouts_connect'),
]