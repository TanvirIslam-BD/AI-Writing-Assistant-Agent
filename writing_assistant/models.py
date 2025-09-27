from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TextImprovement(models.Model):
    """Model to store text improvement requests and results."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_text = models.TextField(help_text="Original text submitted by user")
    improved_text = models.TextField(help_text="Text after improvements")
    tools_used = models.JSONField(default=list, help_text="List of tools applied")
    improvements_details = models.JSONField(default=dict, help_text="Detailed improvement information")
    analysis_results = models.JSONField(default=dict, help_text="Analysis results from each tool")
    created_at = models.DateTimeField(default=timezone.now)
    processing_time = models.FloatField(null=True, blank=True, help_text="Time taken to process in seconds")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Text Improvement"
        verbose_name_plural = "Text Improvements"

    def __str__(self):
        return f"Improvement {self.id} - {self.original_text[:50]}..."

    @property
    def tools_used_display(self):
        """Return a comma-separated string of tools used."""
        return ', '.join(self.tools_used) if self.tools_used else 'None'


class ToolUsageStats(models.Model):
    """Model to track tool usage statistics."""

    tool_name = models.CharField(max_length=100)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(default=timezone.now)
    average_improvement_score = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Tool Usage Statistics"
        verbose_name_plural = "Tool Usage Statistics"
        unique_together = ['tool_name']

    def __str__(self):
        return f"{self.tool_name} - Used {self.usage_count} times"
