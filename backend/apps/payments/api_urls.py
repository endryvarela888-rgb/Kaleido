from django.urls import path

from . import api_views

app_name = 'payments_api'

urlpatterns = [path('checkout/<int:tier_id>/', api_views.CheckoutView.as_view(), name='checkout')]
