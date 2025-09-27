from django.contrib import admin
from .models import TextImprovement, ToolUsageStats


@admin.register(TextImprovement)
class TextImprovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'original_text_preview', 'tools_used_display', 'created_at', 'processing_time')
    list_filter = ('created_at', 'tools_used')
    search_fields = ('original_text', 'improved_text')
    readonly_fields = ('created_at', 'processing_time')

    def original_text_preview(self, obj):
        return obj.original_text[:100] + "..." if len(obj.original_text) > 100 else obj.original_text
    original_text_preview.short_description = "Original Text"


@admin.register(ToolUsageStats)
class ToolUsageStatsAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'usage_count', 'last_used', 'average_improvement_score')
    list_filter = ('last_used',)
    readonly_fields = ('last_used',)
