from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscriber', 'creator', 'tier', 'status', 'cancel_at_period_end', 'current_period_end']
    list_filter = ['status', 'cancel_at_period_end']
    search_fields = ['subscriber__email', 'creator__email']
    autocomplete_fields = ['subscriber', 'creator', 'tier', 'pending_tier']