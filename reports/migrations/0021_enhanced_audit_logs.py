# Generated migration for enhanced audit logs

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0020_esignature_workflow_fixed'),
    ]

    operations = [
        # Update AuditLog model with new fields and choices
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('LOGIN', 'User Login'),
                    ('LOGOUT', 'User Logout'),
                    ('LOGIN_FAILED', 'Failed Login Attempt'),
                    ('PASSWORD_CHANGE', 'Password Changed'),
                    ('PASSWORD_RESET_REQUEST', 'Password Reset Requested'),
                    ('PASSWORD_RESET_COMPLETE', 'Password Reset Completed'),
                    ('USER_CREATE', 'User Created'),
                    ('USER_UPDATE', 'User Updated'),
                    ('USER_DELETE', 'User Deleted'),
                    ('USER_ACTIVATE', 'User Activated'),
                    ('USER_DEACTIVATE', 'User Deactivated'),
                    ('FILE_UPLOAD', 'File Uploaded'),
                    ('FILE_DOWNLOAD', 'File Downloaded'),
                    ('FILE_DELETE', 'File Deleted'),
                    ('FILE_ARCHIVE', 'File Archived'),
                    ('FILE_RESTORE', 'File Restored'),
                    ('FILE_VIEW', 'File Viewed'),
                    ('FILE_EXPORT', 'File Exported'),
                    ('REPORT_GENERATE', 'Report Generated'),
                    ('REPORT_PREVIEW', 'Report Previewed'),
                    ('REPORT_VIEW', 'Report Viewed'),
                    ('REPORT_EXPORT', 'Report Exported'),
                    ('REPORT_DELETE', 'Report Deleted'),
                    ('REPORT_SIGN', 'Report Signed'),
                    ('SIGNATURE_CREATE', 'E-Signature Created'),
                    ('SIGNATURE_UPDATE', 'E-Signature Updated'),
                    ('SIGNATURE_DELETE', 'E-Signature Deleted'),
                    ('SIGNATURE_VIEW', 'E-Signature Viewed'),
                    ('SIGNATURE_SETUP_ACCESS', 'Signature Setup Page Accessed'),
                    ('SIGNATURE_SETUP_COMPLETE', 'Signature Setup Completed'),
                    ('AUTH_REQUEST_CREATE', 'Authorization Request Created'),
                    ('AUTH_REQUEST_APPROVE', 'Authorization Request Approved'),
                    ('AUTH_REQUEST_REJECT', 'Authorization Request Rejected'),
                    ('AUTH_REQUEST_CANCEL', 'Authorization Request Cancelled'),
                    ('AUTH_REQUEST_VIEW', 'Authorization Request Viewed'),
                    ('AUTH_GRANT', 'Authorization Granted'),
                    ('AUTH_REVOKE', 'Authorization Revoked'),
                    ('AUTH_APPROVE_EXISTING', 'Authorization Approved with Existing Signature'),
                    ('DATA_CREATE', 'Data Created'),
                    ('DATA_UPDATE', 'Data Updated'),
                    ('DATA_DELETE', 'Data Deleted'),
                    ('DATA_VIEW', 'Data Viewed'),
                    ('DATA_SEARCH', 'Data Searched'),
                    ('DATA_FILTER', 'Data Filtered'),
                    ('DATA_SORT', 'Data Sorted'),
                    ('SYSTEM_BACKUP', 'System Backup'),
                    ('SYSTEM_RESTORE', 'System Restore'),
                    ('SYSTEM_MAINTENANCE', 'System Maintenance'),
                    ('SYSTEM_CONFIG_CHANGE', 'System Configuration Changed'),
                    ('SYSTEM_ERROR', 'System Error'),
                    ('PAGE_ACCESS', 'Page Accessed'),
                    ('DASHBOARD_VIEW', 'Dashboard Viewed'),
                    ('MENU_NAVIGATE', 'Menu Navigation'),
                    ('COMPONENT_LOAD', 'Component Loaded'),
                    ('EMAIL_SENT', 'Email Sent'),
                    ('EMAIL_FAILED', 'Email Failed'),
                    ('EMAIL_LINK_CLICKED', 'Email Link Clicked'),
                    ('SECURITY_VIOLATION', 'Security Violation'),
                    ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
                    ('PERMISSION_DENIED', 'Permission Denied'),
                    ('TOKEN_EXPIRED', 'Token Expired'),
                    ('TOKEN_INVALID', 'Invalid Token Used'),
                    ('API_CALL', 'API Call Made'),
                    ('API_ERROR', 'API Error'),
                    ('API_RATE_LIMIT', 'API Rate Limit Hit'),
                    ('CREATE', 'Create'),
                    ('UPDATE', 'Update'),
                    ('DELETE', 'Delete'),
                    ('UPLOAD', 'Upload'),
                    ('EXPORT', 'Export'),
                    ('APPROVE', 'Approve'),
                    ('REJECT', 'Reject'),
                    ('VIEW', 'View'),
                    ('ACCESS', 'Access'),
                ],
                max_length=30
            ),
        ),
        
        # Make model_name optional
        migrations.AlterField(
            model_name='auditlog',
            name='model_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        
        # Make user optional
        migrations.AlterField(
            model_name='auditlog',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='audit_logs',
                to='auth.user'
            ),
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='auditlog',
            name='session_key',
            field=models.CharField(blank=True, help_text='Session identifier', max_length=40),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='url_path',
            field=models.CharField(blank=True, help_text='URL path accessed', max_length=500),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='http_method',
            field=models.CharField(blank=True, help_text='HTTP method used', max_length=10),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='request_data',
            field=models.JSONField(blank=True, default=dict, help_text='Request parameters/data'),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='response_status',
            field=models.IntegerField(blank=True, help_text='HTTP response status', null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='duration_ms',
            field=models.IntegerField(blank=True, help_text='Operation duration in milliseconds', null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='category',
            field=models.CharField(blank=True, help_text='Category for grouping similar actions', max_length=50),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='severity',
            field=models.CharField(
                choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')],
                default='LOW',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='success',
            field=models.BooleanField(default=True, help_text='Whether the action was successful'),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='error_message',
            field=models.TextField(blank=True, help_text='Error message if action failed'),
        ),
        
        # Add new indexes
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['ip_address', 'timestamp'], name='reports_auditlog_ip_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['category', 'timestamp'], name='reports_auditlog_category_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['severity', 'timestamp'], name='reports_auditlog_severity_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['success', 'timestamp'], name='reports_auditlog_success_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['url_path'], name='reports_auditlog_url_path_idx'),
        ),
    ]