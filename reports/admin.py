from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Plant, Unit, UploadedFile, GenerationReport, 
    PlantCapacity, HistoricalData, WaterNomination, 
    ActualGeneration, Testimonial, UserProfile, AuditLog,
    PasswordResetRequest, ESignature, ReportSignature,
    SignatoryAuthorization, SignatureVerificationToken, 
    SignatureSecuritySettings, SignatoryAuthorizationRequest, 
    Document, SignatureRequest, DigitalSignature, SignatureAuditLog
)


# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ['role', 'plant', 'phone', 'department', 'position', 
              'email_notifications', 'notify_on_upload', 'notify_on_approval', 'notify_daily_summary']


# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'profile__role']
    
    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else 'No Profile'
    get_role.short_description = 'Role'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'capacity_mw', 'location', 'is_active']
    list_filter = ['is_active', 'code']
    search_fields = ['code', 'name', 'location']
    ordering = ['code']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['plant', 'unit_number', 'capacity_mw', 'is_active', 'commissioned_date']
    list_filter = ['plant', 'is_active']
    search_fields = ['plant__code', 'plant__name']
    ordering = ['plant', 'unit_number']


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'plant', 'uploaded_by', 'uploaded_at', 'status', 'records_imported']
    list_filter = ['status', 'plant', 'uploaded_at']
    search_fields = ['original_filename', 'plant__code', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'checksum', 'file_size']
    ordering = ['-uploaded_at']


@admin.register(GenerationReport)
class GenerationReportAdmin(admin.ModelAdmin):
    list_display = ['plant', 'unit', 'report_date', 'generation_kwh', 'capacity_factor', 'availability_factor']
    list_filter = ['plant', 'report_date']
    search_fields = ['plant__code', 'unit__unit_number']
    date_hierarchy = 'report_date'
    ordering = ['-report_date', 'plant', 'unit']


@admin.register(PlantCapacity)
class PlantCapacityAdmin(admin.ModelAdmin):
    list_display = ['plant', 'installed_capacity', 'dependable_capacity', 'effective_date']
    list_filter = ['plant', 'effective_date']
    search_fields = ['plant__code', 'plant__name']
    date_hierarchy = 'effective_date'
    ordering = ['-effective_date', 'plant']


@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = ['plant', 'date', 'generation_mwh', 'availability_percent', 'status']
    list_filter = ['plant', 'status', 'date']
    search_fields = ['plant__code', 'plant__name']
    date_hierarchy = 'date'
    ordering = ['-date', 'plant']


@admin.register(WaterNomination)
class WaterNominationAdmin(admin.ModelAdmin):
    list_display = ['plant', 'nomination_date', 'nomination_type', 'status', 
                   'total_nominated_mwh', 'submitted_by', 'approved_by']
    list_filter = ['status', 'nomination_type', 'plant', 'nomination_date']
    search_fields = ['plant__code', 'submitted_by__username', 'approved_by__username']
    date_hierarchy = 'nomination_date'
    readonly_fields = ['total_nominated_mw', 'total_nominated_mwh', 'submitted_at', 'approved_at']
    ordering = ['-nomination_date', 'plant']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('plant', 'nomination_date', 'nomination_type', 'status')
        }),
        ('Hourly Nomination (MW)', {
            'fields': (
                ('hour_00', 'hour_01', 'hour_02', 'hour_03'),
                ('hour_04', 'hour_05', 'hour_06', 'hour_07'),
                ('hour_08', 'hour_09', 'hour_10', 'hour_11'),
                ('hour_12', 'hour_13', 'hour_14', 'hour_15'),
                ('hour_16', 'hour_17', 'hour_18', 'hour_19'),
                ('hour_20', 'hour_21', 'hour_22', 'hour_23'),
            )
        }),
        ('Summary', {
            'fields': ('total_nominated_mw', 'total_nominated_mwh')
        }),
        ('Water Parameters', {
            'fields': ('reservoir_level_start', 'reservoir_level_end', 'water_flow_rate', 'inflow_rate'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('submitted_by', 'submitted_at', 'approved_by', 'approved_at', 'remarks')
        }),
    )


@admin.register(ActualGeneration)
class ActualGenerationAdmin(admin.ModelAdmin):
    list_display = ['plant', 'generation_date', 'total_actual_mwh', 'actual_water_flow', 'reservoir_level']
    list_filter = ['plant', 'generation_date']
    search_fields = ['plant__code', 'plant__name']
    date_hierarchy = 'generation_date'
    readonly_fields = ['total_actual_mw', 'total_actual_mwh']
    ordering = ['-generation_date', 'plant']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'plant', 'rating', 'is_active', 'order']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'position', 'plant', 'testimonial']
    ordering = ['order', '-created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'plant', 'department', 'position', 'email_notifications']
    list_filter = ['role', 'plant', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'department', 'position']
    ordering = ['user__username']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'plant')
        }),
        ('Contact Details', {
            'fields': ('phone', 'department', 'position')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'notify_on_upload', 'notify_on_approval', 'notify_daily_summary')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 
                      'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ['username', 'status', 'created_at', 'processed_by', 'processed_at']
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['username', 'reason', 'admin_notes']
    readonly_fields = ['username', 'reason', 'ip_address', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('username', 'reason', 'ip_address', 'status')
        }),
        ('Admin Actions', {
            'fields': ('processed_by', 'processed_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set processed_by and processed_at when status changes"""
        if change and 'status' in form.changed_data:
            if obj.status in ['APPROVED', 'REJECTED', 'COMPLETED']:
                if not obj.processed_by:
                    obj.processed_by = request.user
                if not obj.processed_at:
                    from django.utils import timezone
                    obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_approved', 'mark_as_rejected', 'mark_as_completed']
    
    def mark_as_approved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} request(s) marked as approved.')
    mark_as_approved.short_description = 'Mark selected as Approved'
    
    def mark_as_rejected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} request(s) marked as rejected.')
    mark_as_rejected.short_description = 'Mark selected as Rejected'
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='APPROVED').update(
            status='COMPLETED',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} request(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as Completed'


# Customize admin site
admin.site.site_header = "NPC Reporting System Administration"
admin.site.site_title = "NPC Admin"
admin.site.index_title = "Welcome to NPC Reporting System Administration"

@admin.register(ESignature)
class ESignatureAdmin(admin.ModelAdmin):
    list_display = ['signatory_name', 'signatory_title', 'signature_type', 'is_active', 'is_default', 'created_at']
    list_filter = ['signature_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['signatory_name', 'signatory_title', 'signatory_role']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Signatory Information', {
            'fields': ['signatory_name', 'signatory_title', 'signatory_role']
        }),
        ('Signature Data', {
            'fields': ['signature_image', 'signature_type', 'signature_data']
        }),
        ('Settings', {
            'fields': ['is_active', 'is_default', 'created_by']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(ReportSignature)
class ReportSignatureAdmin(admin.ModelAdmin):
    list_display = ['signatory_name', 'signatory_role', 'report_type', 'report_date', 'signed_at', 'is_verified']
    list_filter = ['report_type', 'signatory_role', 'is_verified', 'signed_at', 'report_date']
    search_fields = ['signatory_name', 'signatory_role']
    readonly_fields = ['signed_at', 'verification_hash']
    date_hierarchy = 'report_date'
    fieldsets = [
        ('Report Information', {
            'fields': ['report_date', 'report_type']
        }),
        ('Signature Information', {
            'fields': ['signature', 'signatory_name', 'signatory_role']
        }),
        ('Signing Details', {
            'fields': ['signed_by', 'signed_at', 'ip_address']
        }),
        ('Verification', {
            'fields': ['is_verified', 'verification_hash']
        })
    ]



@admin.register(SignatoryAuthorization)
class SignatoryAuthorizationAdmin(admin.ModelAdmin):
    list_display = ['user', 'signatory_name', 'is_active', 'requires_2fa', 'authorization_date', 'expiry_date', 'is_valid_status']
    list_filter = ['is_active', 'requires_2fa', 'authorization_date']
    search_fields = ['user__username', 'signatory_name', 'authorized_by__username']
    readonly_fields = ['authorization_date']
    date_hierarchy = 'authorization_date'
    
    fieldsets = (
        ('Authorization', {
            'fields': ('user', 'signatory_name', 'is_active')
        }),
        ('Security', {
            'fields': ('requires_2fa', 'expiry_date')
        }),
        ('Tracking', {
            'fields': ('authorized_by', 'authorization_date', 'notes')
        }),
    )
    
    def is_valid_status(self, obj):
        return '✓' if obj.is_valid() else '✗'
    is_valid_status.short_description = 'Valid'
    is_valid_status.boolean = True
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.authorized_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SignatureAuditLog)
class SignatureAuditLogAdmin(admin.ModelAdmin):
    list_display = ['signature_request', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['signature_request__signer_name', 'signature_request__document__title', 'ip_address']
    readonly_fields = ['signature_request', 'action', 'details', 'ip_address', 
                      'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SignatureVerificationToken)
class SignatureVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'is_valid_status', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'token', 'secret', 'signature_intent', 'created_at', 
                      'expires_at', 'is_used', 'verified_at', 'attempts', 'ip_address']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def is_valid_status(self, obj):
        return '✓' if obj.is_valid() else '✗'
    is_valid_status.short_description = 'Valid'
    is_valid_status.boolean = True
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SignatureSecuritySettings)
class SignatureSecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'require_2fa_for_all', 'enable_encryption', 'enable_verification_hash', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('2FA Settings', {
            'fields': ('require_2fa_for_all', 'otp_validity_minutes', 'max_otp_attempts')
        }),
        ('Rate Limiting', {
            'fields': ('max_signatures_per_hour', 'max_signatures_per_day')
        }),
        ('Audit Settings', {
            'fields': ('audit_retention_days', 'log_geolocation')
        }),
        ('Security Features', {
            'fields': ('enable_encryption', 'enable_verification_hash', 'require_device_fingerprint')
        }),
        ('Notifications', {
            'fields': ('notify_on_signature', 'notify_on_suspicious')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SignatureSecuritySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SignatoryAuthorizationRequest)
class SignatoryAuthorizationRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'signatory_name', 'role', 'email', 'status', 'created_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'role', 'requires_2fa', 'created_at', 'reviewed_at']
    search_fields = ['user__username', 'user__email', 'email', 'signatory_name', 'justification']
    readonly_fields = ['user', 'signatory_name', 'role', 'email', 'justification', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'signatory_name', 'role', 'email', 'justification', 'status')
        }),
        ('Authorization Settings', {
            'fields': ('requires_2fa', 'expiry_date')
        }),
        ('Admin Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set reviewed_by and reviewed_at when status changes"""
        if change and 'status' in form.changed_data:
            if obj.status in ['APPROVED', 'REJECTED']:
                if not obj.reviewed_by:
                    obj.reviewed_by = request.user
                if not obj.reviewed_at:
                    from django.utils import timezone
                    obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Approve selected requests"""
        approved_count = 0
        for auth_request in queryset.filter(status='PENDING'):
            try:
                auth_request.approve(request.user, 'Bulk approved by admin')
                approved_count += 1
            except Exception as e:
                self.message_user(request, f'Error approving request {auth_request.id}: {e}', level='ERROR')
        
        if approved_count > 0:
            self.message_user(request, f'{approved_count} request(s) approved successfully.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected requests"""
        rejected_count = 0
        for auth_request in queryset.filter(status='PENDING'):
            try:
                auth_request.reject(request.user, 'Bulk rejected by admin')
                rejected_count += 1
            except Exception as e:
                self.message_user(request, f'Error rejecting request {auth_request.id}: {e}', level='ERROR')
        
        if rejected_count > 0:
            self.message_user(request, f'{rejected_count} request(s) rejected.')
    reject_requests.short_description = 'Reject selected requests'
    
    def get_queryset(self, request):
        """Show pending requests first"""
        qs = super().get_queryset(request)
        return qs.extra(
            select={'status_order': "CASE WHEN status='PENDING' THEN 0 ELSE 1 END"}
        ).order_by('status_order', '-created_at')

# E-signature workflow admin configurations

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'status', 'created_by', 'created_at', 'signature_count']
    list_filter = ['document_type', 'status', 'created_at']
    search_fields = ['title', 'content', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'document_type', 'content', 'file_path', 'status')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def signature_count(self, obj):
        return obj.signature_requests.count()
    signature_count.short_description = 'Signature Requests'


@admin.register(SignatureRequest)
class SignatureRequestAdmin(admin.ModelAdmin):
    list_display = ['signer_name', 'signer_email', 'document', 'status', 'sent_at', 'signed_at', 'expires_at']
    list_filter = ['status', 'sent_at', 'signed_at', 'expires_at', 'created_at']
    search_fields = ['signer_name', 'signer_email', 'document__title', 'token']
    readonly_fields = ['token', 'sent_at', 'signed_at', 'created_at', 'updated_at', 'signing_url']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Signer Information', {
            'fields': ('signer_name', 'signer_email', 'signer_role')
        }),
        ('Document & Status', {
            'fields': ('document', 'status', 'expires_at')
        }),
        ('Signature Placement', {
            'fields': ('signature_x', 'signature_y', 'signature_page'),
            'classes': ('collapse',)
        }),
        ('Security & Tracking', {
            'fields': ('token', 'signing_url', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'signed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def signing_url(self, obj):
        return obj.generate_signing_url()
    signing_url.short_description = 'Signing URL'


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = ['signer_name', 'document_title', 'signature_type', 'signing_timestamp', 'verification_hash']
    list_filter = ['signature_type', 'signing_timestamp']
    search_fields = ['signature_request__signer_name', 'signature_request__document__title', 'verification_hash']
    readonly_fields = ['verification_hash', 'signing_timestamp', 'signer_name', 'document_title']
    date_hierarchy = 'signing_timestamp'
    ordering = ['-signing_timestamp']
    
    fieldsets = (
        ('Signature Information', {
            'fields': ('signature_request', 'signer_name', 'document_title')
        }),
        ('Signature Data', {
            'fields': ('signature_image', 'signature_type', 'signature_data', 'width', 'height')
        }),
        ('Verification & Security', {
            'fields': ('verification_hash', 'signing_timestamp', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def signer_name(self, obj):
        return obj.signature_request.signer_name
    signer_name.short_description = 'Signer Name'
    
    def document_title(self, obj):
        return obj.signature_request.document.title
    document_title.short_description = 'Document Title'