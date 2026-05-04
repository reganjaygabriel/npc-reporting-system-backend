from django.db import models
from django.contrib.auth.models import User
from .models import Plant


class ScheduledReport(models.Model):
    """Automated report scheduling"""
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('PSR', 'Plant Status Report (PSR)'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('BOTH', 'Both PDF and Excel'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('INACTIVE', 'Inactive'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='PDF')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Filters
    plants = models.ManyToManyField(Plant, blank=True, help_text="Leave empty for all plants")
    date_range_days = models.IntegerField(default=30, help_text="Number of days to include in report")
    
    # Schedule
    schedule_time = models.TimeField(help_text="Time to generate report (24-hour format)")
    schedule_day = models.IntegerField(null=True, blank=True, help_text="Day of week (0=Monday) or month (1-31)")
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='scheduled_reports', help_text="Users to receive report")
    additional_emails = models.TextField(blank=True, help_text="Additional email addresses (one per line)")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_scheduled_reports')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_run']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class ReportExecution(models.Model):
    """Track report execution history"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    records_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    recipients_sent = models.IntegerField(default=0)
    recipients_failed = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'report_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scheduled_report', 'started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.scheduled_report.name} - {self.started_at}"
