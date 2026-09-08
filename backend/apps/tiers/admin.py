from django.contrib import admin

from .models import Tier


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'level', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'creator__email']
    