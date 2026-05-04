"""Serializers for e-signature workflow"""
from rest_framework import serializers
from .models import Document, SignatureRequest, DigitalSignature, SignatureAuditLog


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    signature_requests_count = serializers.SerializerMethodField()
    signed_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'file_path', 'content', 'status',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'signature_requests_count', 'signed_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_signature_requests_count(self, obj):
        return obj.signature_requests.count()
    
    def get_signed_count(self, obj):
        return obj.signature_requests.filter(status='SIGNED').count()


class SignatureRequestSerializer(serializers.ModelSerializer):
    """Serializer for signature requests"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    is_valid = serializers.SerializerMethodField()
    signing_url = serializers.SerializerMethodField()
    has_signature = serializers.SerializerMethodField()
    
    class Meta:
        model = SignatureRequest
        fields = [
            'id', 'document', 'document_title', 'signer_name', 'signer_email', 
            'signer_role', 'token', 'expires_at', 'status', 'sent_at', 'signed_at',
            'signature_x', 'signature_y', 'signature_page', 'created_at', 'updated_at',
            'is_valid', 'signing_url', 'has_signature'
        ]
        read_only_fields = [
            'id', 'token', 'sent_at', 'signed_at', 'created_at', 'updated_at',
            'is_valid', 'signing_url', 'has_signature'
        ]
    
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    def get_signing_url(self, obj):
        """Get the signing URL for this signature request"""
        # Always use the configured SITE_URL for consistency
        return obj.generate_signing_url()
    
    def get_has_signature(self, obj):
        return hasattr(obj, 'signature')


class DigitalSignatureSerializer(serializers.ModelSerializer):
    """Serializer for digital signatures"""
    signer_name = serializers.CharField(source='signature_request.signer_name', read_only=True)
    document_title = serializers.CharField(source='signature_request.document.title', read_only=True)
    
    class Meta:
        model = DigitalSignature
        fields = [
            'id', 'signature_request', 'signer_name', 'document_title',
            'signature_image', 'signature_type', 'signature_data',
            'verification_hash', 'signing_timestamp', 'width', 'height'
        ]
        read_only_fields = [
            'id', 'verification_hash', 'signing_timestamp', 'signer_name', 'document_title'
        ]


class SignatureAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for signature audit logs"""
    signer_name = serializers.CharField(source='signature_request.signer_name', read_only=True)
    document_title = serializers.CharField(source='signature_request.document.title', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = SignatureAuditLog
        fields = [
            'id', 'signature_request', 'signer_name', 'document_title',
            'action', 'action_display', 'details', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class CreateSignatureRequestSerializer(serializers.Serializer):
    """Serializer for creating signature requests"""
    signers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )
    expires_in_hours = serializers.IntegerField(default=72, min_value=1, max_value=168)  # 1 hour to 1 week
    
    def validate_signers(self, value):
        """Validate signer data"""
        required_fields = ['name', 'email', 'role']
        for signer in value:
            for field in required_fields:
                if field not in signer:
                    raise serializers.ValidationError(f"Missing required field '{field}' in signer data")
            
            # Validate email format
            email = signer.get('email', '')
            if not email or '@' not in email:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        
        return value


class SignDocumentSerializer(serializers.Serializer):
    """Serializer for signing documents"""
    signature_type = serializers.ChoiceField(choices=DigitalSignature.SIGNATURE_TYPES)
    signature_data = serializers.CharField(required=False, allow_blank=True)
    signature_image = serializers.ImageField(required=False)
    width = serializers.IntegerField(default=400, min_value=100, max_value=1000)
    height = serializers.IntegerField(default=200, min_value=50, max_value=500)
    
    def validate(self, data):
        """Validate signature data based on type"""
        signature_type = data.get('signature_type')
        
        if signature_type == 'DRAWN':
            if not data.get('signature_data'):
                raise serializers.ValidationError("signature_data is required for drawn signatures")
        elif signature_type == 'UPLOADED':
            if not data.get('signature_image'):
                raise serializers.ValidationError("signature_image is required for uploaded signatures")
        
        return data