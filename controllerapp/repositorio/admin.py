from django.contrib import admin
from .models import ResourceCategory, Resource, ResourceComment

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'project', 'visibility', 'category', 'created_by', 'created_at')
    list_filter = ('resource_type', 'visibility', 'category', 'project', 'created_at')
    search_fields = ('title', 'description', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('project', 'created_by')
    readonly_fields = ('file_size', 'file_type')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'description', 'resource_type', 'category', 'project', 'visibility', 'featured', 'tags')
        }),
        ('Conteúdo', {
            'fields': ('file', 'file_size', 'file_type', 'text_content', 'external_url')
        }),
        ('Metadados', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ResourceComment)
class ResourceCommentAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'text', 'created_at')
    list_filter = ('resource', 'user', 'created_at')
    search_fields = ('text', 'user__first_name', 'user__last_name', 'resource__title')
    raw_id_fields = ('resource', 'user')
    date_hierarchy = 'created_at'
