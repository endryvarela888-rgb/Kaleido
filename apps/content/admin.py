from django.contrib import admin

from .models import Category, Collection, Content


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'created_at']
    list_filter = ['creator']
    search_fields = ['title']


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'content_type', 'collection', 'is_published', 'created_at']
    list_filter = ['content_type', 'is_published']
    search_fields = ['title', 'description']