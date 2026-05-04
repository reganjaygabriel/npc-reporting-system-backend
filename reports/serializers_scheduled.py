from rest_framework import serializers
from .models_scheduled import ScheduledReport, ReportExecution
from .models import Plant
from django.contrib.auth.models import User


class ScheduledReportSerializer(serializers.ModelSerializer):
    """Serializer for scheduled reports"""
    
    plants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Plant.objects.all(),
        required=False
    )
    recipients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    recipients_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'frequency', 'frequency_display', 'format', 'format_display',
            'status', 'status_display', 'plants', 'date_range_days',
            'schedule_time', 'schedule_day', 'recipients', 'recipients_count',
            'additional_emails', 'last_run', 'next_run', 'run_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_run', 'next_run', 'run_count', 'created_at', 'updated_at']
    
    def get_recipients_count(self, obj):
        count = obj.recipients.count()
        if obj.additional_emails:
            count += len([e for e in obj.additional_emails.split('\n') if e.strip()])
        return count


class ReportExecutionSerializer(serializers.ModelSerializer):
    """Serializer for report execution history"""
    
    scheduled_report_name = serializers.CharField(source='scheduled_report.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = [
            'id', 'scheduled_report', 'scheduled_report_name', 'status', 'status_display',
            'started_at', 'completed_at', 'duration_seconds', 'file_path', 'file_size',
            'records_processed', 'error_message', 'recipients_sent', 'recipients_failed'
        ]
        read_only_fields = fields
