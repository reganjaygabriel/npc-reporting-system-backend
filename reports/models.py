from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import logging

logger = logging.getLogger(__name__)


class Plant(models.Model):
    """Agus and Pulangi Hydroelectric Plants"""
    PLANT_CHOICES = [
        ('AGUS1', 'Agus 1'),
        ('AGUS2', 'Agus 2'),
        ('AGUS4', 'Agus 4'),
        ('AGUS5', 'Agus 5'),
        ('AGUS6', 'Agus 6'),
        ('AGUS7', 'Agus 7'),
        ('PULANGI4', 'Pulangi 4'),
    ]
    
    code = models.CharField(max_length=10, choices=PLANT_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    capacity_mw = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    commissioned_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plants'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Unit(models.Model):
    """Generation units within each plant"""
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='units')
    unit_number = models.IntegerField(validators=[MinValueValidator(1)])
    capacity_mw = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    commissioned_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'units'
        unique_together = ['plant', 'unit_number']
        ordering = ['plant', 'unit_number']
        indexes = [
            models.Index(fields=['plant', 'unit_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - Unit {self.unit_number}"


class UploadedFile(models.Model):
    """Audit trail for uploaded Excel files"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    file = models.FileField(upload_to='uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    records_imported = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    file_size = models.IntegerField()
    checksum = models.CharField(max_length=64)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_files')
    
    class Meta:
        db_table = 'uploaded_files'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['plant', 'uploaded_at']),
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['is_archived']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.uploaded_at}"


class GenerationReport(models.Model):
    """Daily generation data for each unit"""
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='generation_reports')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='generation_reports')
    report_date = models.DateField()
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='generation_reports')
    
    # Generation data
    generation_kwh = models.DecimalField(max_digits=15, decimal_places=2)
    operating_hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(24)])
    availability_hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(24)])
    forced_outage_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    scheduled_outage_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Performance metrics
    capacity_factor = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    availability_factor = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Additional fields
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'generation_reports'
        unique_together = ['plant', 'unit', 'report_date']
        ordering = ['-report_date', 'plant', 'unit']
        indexes = [
            models.Index(fields=['plant', 'report_date']),
            models.Index(fields=['report_date']),
            models.Index(fields=['unit', 'report_date']),
            models.Index(fields=['uploaded_file']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - Unit {self.unit.unit_number} - {self.report_date}"
    
    def save(self, *args, **kwargs):
        # Calculate capacity factor
        if self.unit.capacity_mw > 0:
            max_generation = float(self.unit.capacity_mw) * 24
            self.capacity_factor = (float(self.generation_kwh) / 1000 / max_generation) * 100
        
        # Calculate availability factor
        if self.availability_hours > 0:
            self.availability_factor = (float(self.availability_hours) / 24) * 100
        
        super().save(*args, **kwargs)


class PlantCapacity(models.Model):
    """Historical capacity data for plants"""
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='capacity_records')
    installed_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    dependable_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plant_capacity'
        unique_together = ['plant', 'effective_date']
        ordering = ['-effective_date', 'plant']
        indexes = [
            models.Index(fields=['plant', 'effective_date']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - {self.effective_date}"


class HistoricalData(models.Model):
    """Historical operational data imported from legacy systems"""
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='historical_data')
    date = models.DateField()
    generation_mwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    availability_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='Operating')
    remarks = models.TextField(blank=True)
    sheet_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'historical_data'
        unique_together = ['plant', 'date']
        ordering = ['-date', 'plant']
        indexes = [
            models.Index(fields=['plant', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - {self.date}"



class WaterNomination(models.Model):
    """Water nomination and dispatch scheduling for hydroelectric plants"""
    
    NOMINATION_TYPE_CHOICES = [
        ('DAY_AHEAD', 'Day-Ahead'),
        ('HOUR_AHEAD', 'Hour-Ahead'),
        ('REAL_TIME', 'Real-Time'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    
    # Basic Information
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='water_nominations')
    nomination_date = models.DateField(help_text="Date for which nomination is made")
    nomination_type = models.CharField(max_length=20, choices=NOMINATION_TYPE_CHOICES, default='DAY_AHEAD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Hourly Nomination (24 hours)
    hour_00 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 00:00-01:00")
    hour_01 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 01:00-02:00")
    hour_02 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 02:00-03:00")
    hour_03 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 03:00-04:00")
    hour_04 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 04:00-05:00")
    hour_05 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 05:00-06:00")
    hour_06 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 06:00-07:00")
    hour_07 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 07:00-08:00")
    hour_08 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 08:00-09:00")
    hour_09 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 09:00-10:00")
    hour_10 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 10:00-11:00")
    hour_11 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 11:00-12:00")
    hour_12 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 12:00-13:00")
    hour_13 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 13:00-14:00")
    hour_14 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 14:00-15:00")
    hour_15 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 15:00-16:00")
    hour_16 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 16:00-17:00")
    hour_17 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 17:00-18:00")
    hour_18 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 18:00-19:00")
    hour_19 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 19:00-20:00")
    hour_20 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 20:00-21:00")
    hour_21 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 21:00-22:00")
    hour_22 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 22:00-23:00")
    hour_23 = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Nominated MW for 23:00-24:00")
    
    # Summary Fields
    total_nominated_mw = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total nominated MW for the day")
    total_nominated_mwh = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total nominated MWh for the day")
    
    # Water Parameters (Optional - can be customized)
    reservoir_level_start = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Reservoir level at start (meters)")
    reservoir_level_end = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Reservoir level at end (meters)")
    water_flow_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Average water flow rate (m³/s)")
    inflow_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Water inflow rate (m³/s)")
    
    # Tracking
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_nominations')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_nominations')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'water_nominations'
        unique_together = ['plant', 'nomination_date', 'nomination_type']
        ordering = ['-nomination_date', 'plant']
        indexes = [
            models.Index(fields=['plant', 'nomination_date']),
            models.Index(fields=['nomination_date']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_by']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - {self.nomination_date} ({self.nomination_type})"
    
    def save(self, *args, **kwargs):
        # Calculate totals
        hourly_values = [
            float(getattr(self, f'hour_{str(i).zfill(2)}', 0) or 0)
            for i in range(24)
        ]
        self.total_nominated_mw = sum(hourly_values)
        self.total_nominated_mwh = sum(hourly_values)  # Each hour = 1 MWh per MW
        
        super().save(*args, **kwargs)
    
    def get_hourly_data(self):
        """Return hourly nomination data as a list"""
        return [
            {
                'hour': i,
                'time': f"{str(i).zfill(2)}:00-{str(i+1).zfill(2)}:00",
                'nominated_mw': float(getattr(self, f'hour_{str(i).zfill(2)}', 0) or 0)
            }
            for i in range(24)
        ]


class ActualGeneration(models.Model):
    """Actual hourly generation data for comparison with nominations"""
    
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='actual_generations')
    generation_date = models.DateField()
    
    # Hourly Actual Generation (24 hours)
    hour_00 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_01 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_02 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_03 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_04 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_05 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_06 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_07 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_08 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_09 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_10 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_11 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_12 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_13 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_14 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_15 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_16 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_17 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_18 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_19 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_20 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_21 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_22 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hour_23 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Summary
    total_actual_mw = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_actual_mwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Water Parameters
    actual_water_flow = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reservoir_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'actual_generations'
        unique_together = ['plant', 'generation_date']
        ordering = ['-generation_date', 'plant']
        indexes = [
            models.Index(fields=['plant', 'generation_date']),
            models.Index(fields=['generation_date']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - {self.generation_date} (Actual)"
    
    def save(self, *args, **kwargs):
        # Calculate totals
        hourly_values = [
            float(getattr(self, f'hour_{str(i).zfill(2)}', 0) or 0)
            for i in range(24)
        ]
        self.total_actual_mw = sum(hourly_values)
        self.total_actual_mwh = sum(hourly_values)
        
        super().save(*args, **kwargs)
    
    def get_hourly_data(self):
        """Return hourly actual data as a list"""
        return [
            {
                'hour': i,
                'time': f"{str(i).zfill(2)}:00-{str(i+1).zfill(2)}:00",
                'actual_mw': float(getattr(self, f'hour_{str(i).zfill(2)}', 0) or 0)
            }
            for i in range(24)
        ]


class Testimonial(models.Model):
    """User testimonials for the landing page"""
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    plant = models.CharField(max_length=100, blank=True)
    testimonial = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'testimonials'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.position}"


class UserProfile(models.Model):
    """Extended user profile with role-based permissions"""

    ROLE_CHOICES = [
        ('VIEWER', 'Viewer'),
        ('OPERATOR', 'Operator'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    full_name = models.CharField(max_length=200, blank=True, default='')
    plant = models.ForeignKey(Plant, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text="Assigned plant for operators")
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    notify_on_upload = models.BooleanField(default=True)
    notify_on_approval = models.BooleanField(default=True)
    notify_daily_summary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['plant']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def can_upload_data(self):
        """Check if user can upload data"""
        return self.role in ['OPERATOR', 'MANAGER', 'ADMIN'] or self.user.is_staff

    def can_approve_data(self):
        """Check if user can approve data"""
        return self.role in ['MANAGER', 'ADMIN'] or self.user.is_staff

    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == 'ADMIN' or self.user.is_staff

    def can_export_data(self):
        """Check if user can export data"""
        return True  # All authenticated users can export


class AuditLog(models.Model):
    """Comprehensive audit trail for all system actions"""
    
    ACTION_CHOICES = [
        # Authentication & User Management
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
        
        # File Operations
        ('FILE_UPLOAD', 'File Uploaded'),
        ('FILE_DOWNLOAD', 'File Downloaded'),
        ('FILE_DELETE', 'File Deleted'),
        ('FILE_ARCHIVE', 'File Archived'),
        ('FILE_RESTORE', 'File Restored'),
        ('FILE_VIEW', 'File Viewed'),
        ('FILE_EXPORT', 'File Exported'),
        
        # Report Operations
        ('REPORT_GENERATE', 'Report Generated'),
        ('REPORT_PREVIEW', 'Report Previewed'),
        ('REPORT_VIEW', 'Report Viewed'),
        ('REPORT_EXPORT', 'Report Exported'),
        ('REPORT_DELETE', 'Report Deleted'),
        ('REPORT_SIGN', 'Report Signed'),
        
        # E-Signature Operations
        ('SIGNATURE_CREATE', 'E-Signature Created'),
        ('SIGNATURE_UPDATE', 'E-Signature Updated'),
        ('SIGNATURE_DELETE', 'E-Signature Deleted'),
        ('SIGNATURE_VIEW', 'E-Signature Viewed'),
        ('SIGNATURE_SETUP_ACCESS', 'Signature Setup Page Accessed'),
        ('SIGNATURE_SETUP_COMPLETE', 'Signature Setup Completed'),
        
        # Authorization Operations
        ('AUTH_REQUEST_CREATE', 'Authorization Request Created'),
        ('AUTH_REQUEST_APPROVE', 'Authorization Request Approved'),
        ('AUTH_REQUEST_REJECT', 'Authorization Request Rejected'),
        ('AUTH_REQUEST_CANCEL', 'Authorization Request Cancelled'),
        ('AUTH_REQUEST_VIEW', 'Authorization Request Viewed'),
        ('AUTH_GRANT', 'Authorization Granted'),
        ('AUTH_REVOKE', 'Authorization Revoked'),
        ('AUTH_APPROVE_EXISTING', 'Authorization Approved with Existing Signature'),
        
        # Data Operations
        ('DATA_CREATE', 'Data Created'),
        ('DATA_UPDATE', 'Data Updated'),
        ('DATA_DELETE', 'Data Deleted'),
        ('DATA_VIEW', 'Data Viewed'),
        ('DATA_SEARCH', 'Data Searched'),
        ('DATA_FILTER', 'Data Filtered'),
        ('DATA_SORT', 'Data Sorted'),
        
        # Document Operations
        ('DOCUMENT_CREATE', 'Document Created / Saved'),
        ('DOCUMENT_UPDATE', 'Document Updated'),
        ('DOCUMENT_DELETE', 'Document Deleted'),
        ('DOCUMENT_VIEW', 'Document Viewed'),
        
        # System Operations
        ('SYSTEM_BACKUP', 'System Backup'),
        ('SYSTEM_RESTORE', 'System Restore'),
        ('SYSTEM_MAINTENANCE', 'System Maintenance'),
        ('SYSTEM_CONFIG_CHANGE', 'System Configuration Changed'),
        ('SYSTEM_ERROR', 'System Error'),
        
        # Navigation & Page Access
        ('PAGE_ACCESS', 'Page Accessed'),
        ('DASHBOARD_VIEW', 'Dashboard Viewed'),
        ('MENU_NAVIGATE', 'Menu Navigation'),
        ('COMPONENT_LOAD', 'Component Loaded'),
        
        # Email Operations
        ('EMAIL_SENT', 'Email Sent'),
        ('EMAIL_FAILED', 'Email Failed'),
        ('EMAIL_LINK_CLICKED', 'Email Link Clicked'),
        
        # Security Events
        ('SECURITY_VIOLATION', 'Security Violation'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('TOKEN_EXPIRED', 'Token Expired'),
        ('TOKEN_INVALID', 'Invalid Token Used'),
        
        # API Operations
        ('API_CALL', 'API Call Made'),
        ('API_ERROR', 'API Error'),
        ('API_RATE_LIMIT', 'API Rate Limit Hit'),
        
        # Generic Operations (for backward compatibility)
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('UPLOAD', 'Upload'),
        ('EXPORT', 'Export'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('VIEW', 'View'),
        ('ACCESS', 'Access'),
    ]
    
    # Core audit fields
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Approximate location based on IP")
    session_key = models.CharField(max_length=40, blank=True, null=True, help_text="Session identifier")
    
    # Additional context
    url_path = models.CharField(max_length=500, blank=True, help_text="URL path accessed")
    http_method = models.CharField(max_length=10, blank=True, help_text="HTTP method used")
    request_data = models.JSONField(default=dict, blank=True, help_text="Request parameters/data")
    response_status = models.IntegerField(null=True, blank=True, help_text="HTTP response status")
    
    # Timing and performance
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Operation duration in milliseconds")
    
    # Categorization
    category = models.CharField(max_length=50, blank=True, help_text="Category for grouping similar actions")
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='LOW')
    
    # Success/failure tracking
    success = models.BooleanField(default=True, help_text="Whether the action was successful")
    error_message = models.TextField(blank=True, help_text="Error message if action failed")
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
            models.Index(fields=['url_path']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.get_action_display()} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, user=None, action=None, description='', model_name='', object_id=None, 
                   request=None, category='', severity='LOW', success=True, error_message='',
                   duration_ms=None, **kwargs):
        """
        Convenient method to log actions with automatic context extraction
        """
        try:
            audit_data = {
                'user': user,
                'action': action,
                'description': description,
                'model_name': model_name,
                'object_id': object_id,
                'category': category,
                'severity': severity,
                'success': success,
                'error_message': error_message,
                'duration_ms': duration_ms,
            }
            
            # Extract request context if available
            if request:
                try:
                    audit_data.update({
                        'ip_address': cls._get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '') if hasattr(request, 'META') else '',
                        'session_key': cls._get_session_key_safely(request),
                        'url_path': request.path if hasattr(request, 'path') else '',
                        'http_method': request.method if hasattr(request, 'method') else '',
                        'request_data': cls._sanitize_request_data(request),
                    })
                except Exception as e:
                    # If request context extraction fails, continue without it
                    logger.error(f"Failed to extract request context: {e}")
            
            # Add any additional kwargs that match model fields
            model_fields = [f.name for f in cls._meta.fields]
            for key, value in kwargs.items():
                if key in model_fields:
                    audit_data[key] = value
            
            return cls.objects.create(**audit_data)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        except Exception:
            return None
    
    @staticmethod
    def _get_session_key_safely(request):
        """Safely get session key from request"""
        try:
            if hasattr(request, 'session') and request.session:
                return getattr(request.session, 'session_key', '')
        except Exception:
            pass
        return ''
    
    @staticmethod
    def _sanitize_request_data(request):
        """Sanitize request data to remove sensitive information"""
        try:
            if not hasattr(request, 'META'):
                return {}
            
            sensitive_fields = ['password', 'token', 'secret', 'key', 'signature_data']
            data = {}
            
            # Get data from different sources
            if hasattr(request, 'data') and request.data:
                data.update(dict(request.data))
            if hasattr(request, 'GET') and request.GET:
                data.update(dict(request.GET))
            if hasattr(request, 'POST') and request.POST:
                data.update(dict(request.POST))
            
            # Remove sensitive fields
            for field in sensitive_fields:
                if field in data:
                    data[field] = '[REDACTED]'
            
            # Limit data size
            import json
            try:
                json_str = json.dumps(data, default=str)
                if len(json_str) > 5000:  # Limit to 5KB
                    data = {'_truncated': True, '_size': len(json_str)}
            except Exception:
                data = {'_error': 'Could not serialize request data'}
            
            return data
        except Exception:
            return {}


class ESignature(models.Model):
    """Electronic signatures for report authorization"""
    
    SIGNATURE_TYPE_CHOICES = [
        ('DRAW', 'Hand Drawn'),
        ('UPLOAD', 'Uploaded Image'),
        ('TYPE', 'Typed Text'),
    ]
    
    # Signatory information
    signatory_name = models.CharField(max_length=100, help_text="Name of the person signing")
    signatory_title = models.CharField(max_length=100, blank=True, help_text="Job title of the signatory")
    signatory_role = models.CharField(max_length=100, blank=True, help_text="Role in the authorization (e.g., 'Prepared by', 'Approved by')")
    
    # Signature data
    signature_image = models.ImageField(upload_to='signatures/%Y/%m/', help_text="Signature image file")
    signature_type = models.CharField(max_length=10, choices=SIGNATURE_TYPE_CHOICES, default='DRAW')
    signature_data = models.TextField(blank=True, help_text="Base64 encoded signature data for backup")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_signatures')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default signature for this signatory")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'e_signatures'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['signatory_name', 'is_active']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_default', 'signatory_name']),
        ]
    
    def __str__(self):
        return f"{self.signatory_name} - {self.get_signature_type_display()}"


class ReportSignature(models.Model):
    """Track which signatures are applied to which reports"""
    
    # Report identification
    report_date = models.DateField(help_text="Date of the report")
    report_type = models.CharField(max_length=50, default='PSR', help_text="Type of report (PSR, etc.)")
    
    # Signature information
    signature = models.ForeignKey(ESignature, on_delete=models.CASCADE, related_name='report_usages')
    signatory_name = models.CharField(max_length=100, help_text="Name of the signatory")
    signatory_role = models.CharField(max_length=100, help_text="Role in authorization")
    
    # Signing metadata
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_signatures')
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=True)
    verification_hash = models.CharField(max_length=64, blank=True, help_text="Hash for signature verification")
    
    class Meta:
        db_table = 'report_signatures'
        unique_together = ['report_date', 'report_type', 'signatory_name', 'signatory_role']
        ordering = ['-signed_at']
        indexes = [
            models.Index(fields=['report_date', 'report_type'], name='report_sig_date_type_idx'),
            models.Index(fields=['signatory_name'], name='report_sig_name_idx'),
            models.Index(fields=['signed_by', 'signed_at'], name='report_sig_user_time_idx'),
        ]
    
    def __str__(self):
        return f"{self.signatory_name} - {self.report_type} - {self.report_date}"


class PasswordResetRequest(models.Model):
    """Password reset requests from users"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    
    username = models.CharField(max_length=150, help_text="Username requesting password reset")
    reason = models.TextField(blank=True, help_text="Optional reason for password reset request")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Admin actions
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='processed_reset_requests',
                                    help_text="Admin who processed this request")
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes from admin")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'password_reset_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"



class SignatoryAuthorization(models.Model):
    """Authorization for users to sign as specific signatories"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signatory_authorizations')
    signatory_name = models.CharField(max_length=100, help_text="Name of signatory this user can sign as")
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                     null=True, related_name='granted_authorizations',
                                     help_text="Admin who granted this authorization")
    authorization_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="When this authorization expires")
    is_active = models.BooleanField(default=True)
    requires_2fa = models.BooleanField(default=True, help_text="Require 2FA for this signatory")
    notes = models.TextField(blank=True)
    
    # E-signature setup fields
    setup_token = models.CharField(max_length=64, null=True, blank=True, help_text="Secure token for signature setup")
    token_expires = models.DateTimeField(null=True, blank=True, help_text="When setup token expires")
    signature_created = models.BooleanField(default=False, help_text="Whether user has created their signature")
    
    class Meta:
        db_table = 'signatory_authorizations'
        unique_together = ['user', 'signatory_name']
        ordering = ['-authorization_date']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['signatory_name', 'is_active']),
            models.Index(fields=['setup_token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} authorized as {self.signatory_name}"
    
    def is_valid(self):
        """Check if authorization is currently valid"""
        from django.utils import timezone
        
        if not self.is_active:
            return False
        if self.expiry_date and timezone.now() > self.expiry_date:
            return False
        return True
    
    def is_setup_token_valid(self):
        """Check if setup token is valid"""
        try:
            from django.utils import timezone
            
            if not self.setup_token:
                return False
            if self.token_expires and timezone.now() > self.token_expires:
                return False
            return True
        except Exception as e:
            # Fallback: if there's any error, assume token is valid if it exists
            # This prevents the NameError from breaking the signature setup
            print(f"Warning: Error in token validation: {e}")
            return bool(self.setup_token)


# SignatureAuditLog model removed - using the one from e-signature workflow system


class SignatureVerificationToken(models.Model):
    """2FA tokens for signature verification"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signature_tokens')
    token = models.CharField(max_length=6, help_text="6-digit OTP code")
    secret = models.CharField(max_length=64, help_text="Secret for token generation")
    signature_intent = models.JSONField(help_text="What the user is trying to sign")
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this token expires")
    is_used = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Security tracking
    attempts = models.IntegerField(default=0, help_text="Number of verification attempts")
    max_attempts = models.IntegerField(default=3)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'signature_verification_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['token', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Token {self.token} - {'Used' if self.is_used else 'Active'}"
    
    def is_valid(self):
        """Check if token is still valid"""
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        if self.attempts >= self.max_attempts:
            return False
        return True
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])


class SignatureSecuritySettings(models.Model):
    """Global security settings for signature system"""
    
    # 2FA Settings
    require_2fa_for_all = models.BooleanField(default=False, help_text="Require 2FA for all signatures")
    otp_validity_minutes = models.IntegerField(default=5, help_text="OTP validity in minutes")
    max_otp_attempts = models.IntegerField(default=3, help_text="Maximum OTP verification attempts")
    
    # Rate Limiting
    max_signatures_per_hour = models.IntegerField(default=10, help_text="Max signatures per user per hour")
    max_signatures_per_day = models.IntegerField(default=50, help_text="Max signatures per user per day")
    
    # Audit Settings
    audit_retention_days = models.IntegerField(default=2555, help_text="Audit log retention (7 years default)")
    log_geolocation = models.BooleanField(default=False, help_text="Log approximate geolocation")
    
    # Security Features
    enable_encryption = models.BooleanField(default=True, help_text="Encrypt signature data at rest")
    enable_verification_hash = models.BooleanField(default=True, help_text="Generate verification hashes")
    require_device_fingerprint = models.BooleanField(default=True, help_text="Require device fingerprinting")
    
    # Notification Settings
    notify_on_signature = models.BooleanField(default=True, help_text="Email notification on signature")
    notify_on_suspicious = models.BooleanField(default=True, help_text="Alert on suspicious activity")
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'signature_security_settings'
        verbose_name = 'Signature Security Settings'
        verbose_name_plural = 'Signature Security Settings'
    
    def __str__(self):
        return f"Signature Security Settings (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_settings(cls):
        """Get or create singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Document(models.Model):
    """Documents that require signatures"""
    
    DOCUMENT_TYPES = [
        ('PSR', 'Plant Status Report'),
        ('DAILY', 'Daily Report'),
        ('MONTHLY', 'Monthly Report'),
        ('CUSTOM', 'Custom Document'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_SIGNATURE', 'Pending Signature'),
        ('SIGNED', 'Signed'),
        ('COMPLETED', 'Completed'),
    ]
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file_path = models.FileField(upload_to='documents/%Y/%m/', null=True, blank=True)
    content = models.TextField(blank=True, help_text="Document content if not file-based")
    description = models.TextField(blank=True, help_text="Document description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class SignatureRequest(models.Model):
    """Signature requests sent to users"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SIGNED', 'Signed'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signature_requests')
    signer_name = models.CharField(max_length=100)
    signer_email = models.EmailField()
    signer_role = models.CharField(max_length=100, help_text="Role in document (e.g., 'Prepared by', 'Approved by')")
    
    # Token-based security
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Signature position in document
    signature_x = models.IntegerField(null=True, blank=True, help_text="X coordinate for signature placement")
    signature_y = models.IntegerField(null=True, blank=True, help_text="Y coordinate for signature placement")
    signature_page = models.IntegerField(default=1, help_text="Page number for signature placement")
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signature_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Signature request for {self.signer_name} - {self.document.title}"
    
    def is_valid(self):
        """Check if signature request is still valid"""
        from django.utils import timezone
        return (
            self.status == 'PENDING' and 
            self.expires_at > timezone.now()
        )
    
    def generate_signing_url(self, base_url=None):
        """Generate the signing URL for this request"""
        if base_url is None:
            from django.conf import settings
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:3000')
        return f"{base_url}/sign/{self.token}"


class DigitalSignature(models.Model):
    """Digital signatures created by users"""
    
    SIGNATURE_TYPES = [
        ('DRAWN', 'Hand Drawn'),
        ('UPLOADED', 'Uploaded Image'),
        ('TYPED', 'Typed Text'),
    ]
    
    signature_request = models.OneToOneField(
        SignatureRequest, 
        on_delete=models.CASCADE, 
        related_name='signature'
    )
    
    # Signature data
    signature_image = models.ImageField(upload_to='signatures/%Y/%m/')
    signature_type = models.CharField(max_length=10, choices=SIGNATURE_TYPES)
    signature_data = models.TextField(blank=True, help_text="Base64 signature data for drawn signatures")
    
    # Verification data
    verification_hash = models.CharField(max_length=64, blank=True)
    signing_timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Signature metadata
    width = models.IntegerField(default=400)
    height = models.IntegerField(default=200)
    
    class Meta:
        db_table = 'digital_signatures'
        ordering = ['-signing_timestamp']
    
    def __str__(self):
        return f"Signature by {self.signature_request.signer_name} - {self.signature_request.document.title}"


class SignatureAuditLog(models.Model):
    """Audit log for signature-related activities"""
    
    ACTION_CHOICES = [
        ('REQUEST_CREATED', 'Signature Request Created'),
        ('EMAIL_SENT', 'Signature Email Sent'),
        ('LINK_ACCESSED', 'Signature Link Accessed'),
        ('SIGNATURE_CREATED', 'Signature Created'),
        ('DOCUMENT_SIGNED', 'Document Signed'),
        ('REQUEST_EXPIRED', 'Request Expired'),
        ('REQUEST_CANCELLED', 'Request Cancelled'),
    ]
    
    signature_request = models.ForeignKey(
        SignatureRequest, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signature_audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.signature_request.signer_name} - {self.timestamp}"


class SignatoryAuthorizationRequest(models.Model):
    """User-friendly authorization requests"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Request details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authorization_requests')
    signatory_name = models.CharField(max_length=100, help_text="Name of signatory requested")
    role = models.CharField(max_length=100, help_text="Role (Prepared by, Approved by, etc.)")
    email = models.EmailField(help_text="Email address for notifications")
    justification = models.TextField(help_text="User's justification for the request")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Admin review
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='reviewed_authorization_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Admin notes on the decision")
    
    # Auto-approval settings
    requires_2fa = models.BooleanField(default=True, help_text="Require 2FA for this authorization")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="When authorization expires")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signatory_authorization_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['signatory_name']),
        ]
    
    def __str__(self):
        return f"{self.user.username} requests {self.signatory_name} - {self.status}"
    
    def approve(self, admin_user, notes=''):
        """Approve the request and create authorization"""
        from django.utils import timezone
        
        # Update request status
        self.status = 'APPROVED'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()
        
        # Create the actual authorization
        authorization, created = SignatoryAuthorization.objects.get_or_create(
            user=self.user,
            signatory_name=self.signatory_name,
            defaults={
                'authorized_by': admin_user,
                'requires_2fa': self.requires_2fa,
                'expiry_date': self.expiry_date,
                'notes': f"Auto-created from request #{self.id}. {notes}".strip(),
                'is_active': True
            }
        )
        
        if not created:
            # Update existing authorization
            authorization.is_active = True
            authorization.authorized_by = admin_user
            authorization.requires_2fa = self.requires_2fa
            authorization.expiry_date = self.expiry_date
            authorization.notes = f"Updated from request #{self.id}. {notes}".strip()
            authorization.save()
        
        return authorization
    
    def reject(self, admin_user, notes=''):
        """Reject the request"""
        from django.utils import timezone
        
        self.status = 'REJECTED'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()


class MonthlyTarget(models.Model):
    """Monthly performance targets for plants"""
    
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='monthly_targets')
    month = models.IntegerField(help_text="Month (1-12)")
    year = models.IntegerField(help_text="Year")
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Target capacity factor percentage")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_monthly_targets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'monthly_targets'
        unique_together = ['plant', 'year', 'month']
        ordering = ['-year', '-month', 'plant']
        indexes = [
            models.Index(fields=['plant', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.plant.code} - {self.year}-{str(self.month).zfill(2)} - {self.target_percentage}%"
    
    @classmethod
    def get_current_target(cls, plant_code, month=None, year=None):
        """Get current month's target for a plant"""
        from datetime import datetime
        
        if month is None or year is None:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        try:
            plant = Plant.objects.get(code=plant_code)
            target = cls.objects.get(plant=plant, month=month, year=year)
            return float(target.target_percentage)
        except (Plant.DoesNotExist, cls.DoesNotExist):
            return None
