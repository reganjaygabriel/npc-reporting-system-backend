from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import (
    Plant, Unit, UploadedFile, GenerationReport, PlantCapacity, 
    HistoricalData, WaterNomination, ActualGeneration, Testimonial,
    UserProfile, AuditLog, PasswordResetRequest, ESignature, ReportSignature,
    MonthlyTarget
)


class UserSerializer(serializers.ModelSerializer):
    """User serializer for basic user info"""
    profile = serializers.SerializerMethodField()
    role = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'profile', 'role', 'password']
        read_only_fields = ['id', 'date_joined']
    
    def get_profile(self, obj):
        try:
            return {
                'role': obj.profile.role,
                'phone': obj.profile.phone,
                'department': obj.profile.department
            }
        except:
            return {'role': 'VIEWER', 'phone': '', 'department': ''}
    
    def validate_username(self, value):
        """Validate and sanitize username"""
        # Remove spaces and convert to lowercase for consistency
        sanitized = value.strip()
        
        # Check if username already exists
        if self.instance is None:  # Only check on creation
            if User.objects.filter(username=sanitized).exists():
                raise serializers.ValidationError('A user with this username already exists.')
        
        return sanitized
    
    def create(self, validated_data):
        role = validated_data.pop('role', 'VIEWER')
        password = validated_data.pop('password', None)
        
        if not password:
            raise serializers.ValidationError({'password': 'Password is required'})
        
        user = User.objects.create_user(**validated_data, password=password)
        
        # Generate full_name from first_name and last_name
        full_name = f"{user.first_name} {user.last_name}".strip()
        if not full_name:
            full_name = user.username
        
        # Create or update profile with role and full_name
        from .models import UserProfile
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'full_name': full_name
            }
        )
        
        return user
    
    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)
        validated_data.pop('password', None)  # Don't update password through this serializer
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update role if provided
        if role:
            from .models import UserProfile
            UserProfile.objects.update_or_create(
                user=instance,
                defaults={'role': role}
            )
        
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Password fields did not match'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with additional info"""
    uploads_count = serializers.SerializerMethodField()
    last_upload = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'last_login',
            'uploads_count', 'last_upload', 'profile'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'uploads_count', 'last_upload', 'profile']
    
    def get_uploads_count(self, obj):
        return obj.uploadedfile_set.count()
    
    def get_last_upload(self, obj):
        last_upload = obj.uploadedfile_set.order_by('-uploaded_at').first()
        if last_upload:
            return {
                'filename': last_upload.original_filename,
                'date': last_upload.uploaded_at,
                'plant': last_upload.plant.code
            }
        return None
    
    def get_profile(self, obj):
        """Get user profile with role and permissions"""
        if not hasattr(obj, 'profile'):
            return None
        
        profile = obj.profile
        return {
            'role': profile.role,
            'role_display': profile.get_role_display(),
            'plant': profile.plant.code if profile.plant else None,
            'plant_name': profile.plant.name if profile.plant else None,
            'phone': profile.phone,
            'department': profile.department,
            'position': profile.position,
            'email_notifications': profile.email_notifications,
            'permissions': {
                'can_upload_data': profile.can_upload_data(),
                'can_approve_data': profile.can_approve_data(),
                'can_manage_users': profile.can_manage_users(),
                'can_export_data': profile.can_export_data(),
            }
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                'new_password': 'Password fields did not match'
            })
        return attrs


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    
    class Meta:
        model = Unit
        fields = '__all__'


class UploadedFileSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = UploadedFile
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at', 'status', 'records_imported', 'checksum']


class GenerationReportSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    unit_number = serializers.IntegerField(source='unit.unit_number', read_only=True)
    
    class Meta:
        model = GenerationReport
        fields = '__all__'


class GenerationReportListSerializer(serializers.ModelSerializer):
    """Optimized serializer for list views"""
    plant_code = serializers.CharField(source='plant.code')
    unit_number = serializers.IntegerField(source='unit.unit_number')
    
    class Meta:
        model = GenerationReport
        fields = ['id', 'plant_code', 'unit_number', 'report_date', 'generation_kwh', 
                  'operating_hours', 'capacity_factor', 'availability_factor']


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    plant_code = serializers.CharField(max_length=10)
    
    def validate_file(self, value):
        # Accept .xlsx, .xls, and .csv formats
        valid_extensions = ['.xlsx', '.xls', '.csv']
        file_ext = value.name.lower()[-5:] if len(value.name) > 5 else value.name.lower()
        
        if not any(file_ext.endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError("Only Excel files (.xlsx, .xls) and CSV files (.csv) are allowed")
        
        # Increase file size limit to 100MB
        if value.size > 104857600:  # 100MB
            raise serializers.ValidationError("File size must not exceed 100MB")
        
        return value
    
    def validate_plant_code(self, value):
        """Validate that the plant code exists in the database"""
        if not Plant.objects.filter(code=value, is_active=True).exists():
            raise serializers.ValidationError(f"Plant with code '{value}' not found or is inactive")
        return value


class ReportGenerationSerializer(serializers.Serializer):
    plant_codes = serializers.ListField(
        child=serializers.CharField(max_length=10),
        allow_empty=False
    )
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    report_type = serializers.ChoiceField(choices=['psr', 'daily_status'], default='psr')
    
    def validate_plant_codes(self, value):
        """Validate that all plant codes exist in the database"""
        invalid_codes = []
        for code in value:
            if not Plant.objects.filter(code=code, is_active=True).exists():
                invalid_codes.append(code)
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid or inactive plant codes: {', '.join(invalid_codes)}"
            )
        return value
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("start_date must be before end_date")
        return data


class PlantCapacitySerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    
    class Meta:
        model = PlantCapacity
        fields = '__all__'


class HistoricalDataSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    
    class Meta:
        model = HistoricalData
        fields = '__all__'


class HistoricalDataUploadSerializer(serializers.Serializer):
    capacity_file = serializers.FileField(required=False, allow_null=True)
    historical_file = serializers.FileField(required=False, allow_null=True)
    
    def validate(self, data):
        if not data.get('capacity_file') and not data.get('historical_file'):
            raise serializers.ValidationError("At least one file must be provided")
        
        for field in ['capacity_file', 'historical_file']:
            file = data.get(field)
            if file:
                if not file.name.endswith('.xlsx'):
                    raise serializers.ValidationError(f"{field}: Only .xlsx files are allowed")
                if file.size > 52428800:  # 50MB for historical data
                    raise serializers.ValidationError(f"{field}: File size must not exceed 50MB")
        
        return data


class WaterNominationSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    hourly_data = serializers.SerializerMethodField()
    
    class Meta:
        model = WaterNomination
        fields = '__all__'
        read_only_fields = ['submitted_by', 'submitted_at', 'approved_by', 'approved_at', 
                           'total_nominated_mw', 'total_nominated_mwh']
    
    def get_hourly_data(self, obj):
        return obj.get_hourly_data()


class ActualGenerationSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    hourly_data = serializers.SerializerMethodField()
    
    class Meta:
        model = ActualGeneration
        fields = '__all__'
        read_only_fields = ['total_actual_mw', 'total_actual_mwh']
    
    def get_hourly_data(self, obj):
        return obj.get_hourly_data()


class NominationVarianceSerializer(serializers.Serializer):
    """Serializer for nomination vs actual variance analysis"""
    date = serializers.DateField()
    plant_code = serializers.CharField()
    plant_name = serializers.CharField()
    nomination_type = serializers.CharField()
    total_nominated_mwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_actual_mwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance_mwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    hourly_comparison = serializers.ListField()


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'position', 'plant', 'testimonial', 'rating', 'is_active', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']



class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed user profile with role and permissions"""
    user = UserSerializer(read_only=True)
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_permissions(self, obj):
        return {
            'can_upload_data': obj.can_upload_data(),
            'can_approve_data': obj.can_approve_data(),
            'can_manage_users': obj.can_manage_users(),
            'can_export_data': obj.can_export_data(),
        }


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    model_display_name = serializers.SerializerMethodField()
    location_display = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['user', 'timestamp']

    def get_user_full_name(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return full_name if full_name else obj.user.username
        return "System"
        
    def get_user_role(self, obj):
        if obj.user and hasattr(obj.user, 'profile'):
            role_map = {
                'VIEWER': 'Viewer',
                'OPERATOR': 'Data Encoder / Operator',
                'MANAGER': 'Data Manager',
                'ADMIN': 'Administrator'
            }
            return role_map.get(obj.user.profile.role, obj.user.profile.get_role_display())
        if obj.user and obj.user.is_superuser:
            return "Administrator"
        return "System Role"

    def get_model_display_name(self, obj):
        if not obj.model_name:
            # Check category or action to provide a better name than N/A
            if obj.category == 'authentication':
                return "Authentication"
            if obj.category == 'security':
                return "Security"
            if obj.category == 'system':
                return "System"
            if 'view' in obj.description.lower() or 'access' in obj.description.lower():
                return "Page Access"
            return "General System"
            
        model_map = {
            'Plant': 'Power Plant',
            'Unit': 'Generation Unit',
            'UploadedFile': 'File Upload',
            'GenerationReport': 'Generation Report',
            'PlantCapacity': 'Plant Capacity',
            'HistoricalData': 'Historical Data',
            'WaterNomination': 'Water Nomination',
            'ActualGeneration': 'Actual Generation',
            'Testimonial': 'User Testimonial',
            'UserProfile': 'User Profile',
            'User': 'System User',
            'AuditLog': 'Audit Log',
            'PasswordResetRequest': 'Password Reset',
            'ESignature': 'Electronic Signature',
            'ReportSignature': 'Report Signature',
            'SignatoryAuthorization': 'Signatory Authorization',
            'SignatureVerificationToken': 'Security Token',
            'SignatureSecuritySettings': 'Security Settings',
            'Document': 'System Document',
            'AuthRequest': 'Authorization Request',
            'SignatoryAuthorizationRequest': 'Authorization Request',
        }
        
        # Check if the model_name is in our map
        if obj.model_name in model_map:
            return model_map[obj.model_name]
            
        # If not in map, try to make it more readable (e.g., "GenerationReport" -> "Generation Report")
        import re
        readable = re.sub(r'(?<!^)(?=[A-Z])', ' ', obj.model_name)
        return readable

    def get_location_display(self, obj):
        if not obj.location or obj.location.lower() == 'unknown':
            if obj.ip_address in ['127.0.0.1', '::1']:
                return "Local System (Internal)"
            return "Internal Network"
        return obj.location


class PasswordResetRequestSerializer(serializers.ModelSerializer):
    """Serializer for password reset requests"""
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = PasswordResetRequest
        fields = ['id', 'username', 'reason', 'status', 'ip_address', 
                  'processed_by', 'processed_by_username', 'processed_at', 
                  'admin_notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'processed_by', 'processed_at', 
                           'created_at', 'updated_at', 'ip_address']

class ESignatureSerializer(serializers.ModelSerializer):
    """Serializer for E-Signature model with security features"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ESignature
        fields = [
            'id', 'signatory_name', 'signatory_title', 'signatory_role',
            'signature_image', 'signature_type', 'signature_data',
            'created_by', 'created_by_name', 'is_active', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_name']
    
    def create(self, validated_data):
        # Set created_by to current user if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)
        
        # Encrypt signature data if enabled
        if settings.enable_encryption and validated_data.get('signature_data'):
            encryptor = SignatureEncryption()
            validated_data['signature_data'] = encryptor.encrypt_signature_data(
                validated_data['signature_data']
            )
        
        # Create signature
        signature = super().create(validated_data)
        
        # Generate verification hash if enabled
        if settings.enable_verification_hash:
            # Decrypt data temporarily for hash generation
            data_for_hash = validated_data.get('signature_data', '')
            if settings.enable_encryption:
                encryptor = SignatureEncryption()
                data_for_hash = encryptor.decrypt_signature_data(data_for_hash)
            
            signature.verification_hash = SignatureVerifier.generate_signature_hash(
                data_for_hash,
                signature.signatory_name,
                signature.created_at.isoformat()
            )
            signature.save(update_fields=['verification_hash'])
        
        # Log creation
        self._log_audit(request, 'CREATE', signature, True)
        
        return signature
    
    def _log_audit(self, request, action, signature, success, failure_reason=''):
        """Log signature operation to audit log"""
        from .models import SignatureAuditLog
        
        if not request:
            return
        
        SignatureAuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            signature=signature,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_fingerprint=request.data.get('device_fingerprint', ''),
            success=success,
            failure_reason=failure_reason
        )
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class ReportSignatureSerializer(serializers.ModelSerializer):
    """Serializer for Report Signature model with enhanced security"""
    signature_details = ESignatureSerializer(source='signature', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.username', read_only=True)
    is_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSignature
        fields = [
            'id', 'report_date', 'report_type', 'signature', 'signature_details',
            'signatory_name', 'signatory_role', 'signed_by', 'signed_by_name',
            'signed_at', 'ip_address', 'is_verified', 'verification_hash'
        ]
        read_only_fields = ['id', 'signed_at', 'signed_by_name', 'verification_hash', 'is_verified']
    
    def get_is_verified(self, obj):
        """Check if report signature is verified"""
        return obj.is_verified and bool(obj.verification_hash)
    
    def create(self, validated_data):
        from .signature_utils.signature_crypto import SignatureVerifier
        
        # Set signed_by to current user if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['signed_by'] = request.user
            # Set IP address from request
            try:
                validated_data['ip_address'] = self.get_client_ip(request)
            except Exception:
                validated_data['ip_address'] = '127.0.0.1'
        
        # Create report signature
        report_sig = super().create(validated_data)
        
        # Generate verification hash
        report_sig.verification_hash = SignatureVerifier.generate_report_signature_hash(
            str(report_sig.report_date),
            report_sig.report_type,
            report_sig.signatory_name,
            report_sig.signature.id,
            report_sig.signed_at.isoformat()
        )
        report_sig.save(update_fields=['verification_hash'])
        
        # Log application
        self._log_audit(request, 'APPLY', report_sig, True)
        
        return report_sig
    
    def _log_audit(self, request, action, report_signature, success, failure_reason=''):
        """Log report signature operation to audit log"""
        from .models import AuditLog
        
        if not request or not request.user.is_authenticated:
            return
        
        try:
            AuditLog.objects.create(
                user=request.user,
                action='CREATE' if action == 'APPLY' else action,
                model_name='ReportSignature',
                object_id=report_signature.id if report_signature else None,
                description=f"Report signature applied: {report_signature.signatory_name} for {report_signature.report_date}",
                ip_address=self.get_client_ip(request),
                location=''
            )
        except Exception as e:
            # Don't fail the signature operation if audit logging fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log: {str(e)}")
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            return ip or '127.0.0.1'
        except Exception:
            return '127.0.0.1'


class ESignatureCreateSerializer(serializers.Serializer):
    """Serializer for creating e-signatures from frontend data"""
    signatory_name = serializers.CharField(max_length=100)
    signatory_title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    signatory_role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    signature_type = serializers.ChoiceField(choices=ESignature.SIGNATURE_TYPE_CHOICES)
    signature_data = serializers.CharField(help_text="Base64 encoded signature data")
    is_default = serializers.BooleanField(default=False)
    
    def create(self, validated_data):
        # Convert base64 data to image file
        import base64
        import io
        from django.core.files.base import ContentFile
        
        signature_data = validated_data.pop('signature_data')
        
        # Remove data URL prefix if present
        if signature_data.startswith('data:image'):
            signature_data = signature_data.split(',')[1]
        
        # Decode base64 data
        try:
            image_data = base64.b64decode(signature_data)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid base64 data: {str(e)}")
        
        # Create filename
        filename = f"{validated_data['signatory_name'].replace(' ', '_').lower()}_signature.png"
        
        # Create signature instance
        signature = ESignature.objects.create(
            **validated_data,
            signature_image=ContentFile(image_data, filename),
            signature_data=signature_data  # Keep original base64 for backup
        )
        
        # Set created_by if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            signature.created_by = request.user
            signature.save()
        
        return signature


class MonthlyTargetSerializer(serializers.ModelSerializer):
    """Serializer for monthly targets"""
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_code = serializers.CharField(source='plant.code', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = MonthlyTarget
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_month(self, value):
        """Validate month is between 1-12"""
        if not (1 <= value <= 12):
            raise serializers.ValidationError("Month must be between 1 and 12")
        return value
    
    def validate_year(self, value):
        """Validate year is reasonable"""
        from datetime import datetime
        current_year = datetime.now().year
        if not (2020 <= value <= current_year + 10):
            raise serializers.ValidationError(f"Year must be between 2020 and {current_year + 10}")
        return value
    
    def validate_target_percentage(self, value):
        """Validate target percentage is reasonable"""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Target percentage must be between 0 and 100")
        return value
    
    def create(self, validated_data):
        # Set created_by to current user if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)