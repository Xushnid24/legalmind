from django.contrib import admin
from .models import Case, GeneratedDocument

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')
    list_filter = ('date',)
    search_fields = ('title', 'text')
    ordering = ('-date',)
    fields = ('title', 'text')


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'created_at')
    list_filter = ('doc_type', 'created_at')
    search_fields = ('doc_type', 'text')
    ordering = ('-created_at',)
    fields = ('doc_type', 'text')
