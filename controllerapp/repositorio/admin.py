from django.contrib import admin
from .models import ResourceCategory, Resource, ResourceComment, ResourceFile

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'project', 'visibility', 'created_at', 'featured')
    list_filter = ('resource_type', 'visibility', 'featured', 'project')
    search_fields = ('title', 'description', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    # Removi os campos readonly que estavam causando erro
    
@admin.register(ResourceComment)
class ResourceCommentAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'created_at')
    list_filter = ('resource__resource_type', 'created_at')
    search_fields = ('text', 'user__first_name', 'user__last_name', 'resource__title')
    date_hierarchy = 'created_at'

@admin.register(ResourceFile)
class ResourceFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource', 'file_type', 'file_size', 'upload_date')
    list_filter = ('resource__project', 'file_type', 'upload_date')
    search_fields = ('title', 'resource__title')
    raw_id_fields = ('resource',)
    readonly_fields = ('file_size', 'file_type')  # Aqui os campos são válidos pois pertencem a ResourceFile
    date_hierarchy = 'upload_date'
