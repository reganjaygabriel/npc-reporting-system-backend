"""Views for e-signature workflow"""
import secrets
import hashlib
import base64
from datetime import timedelta
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Document, SignatureRequest, DigitalSignature, SignatureAuditLog
from .serializers_signature import (
    DocumentSerializer, SignatureRequestSerializer, DigitalSignatureSerializer,
    SignatureAuditLogSerializer, CreateSignatureRequestSerializer, SignDocumentSerializer
)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing documents"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter documents based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """Set the creator when creating a document"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def request_signatures(self, request, pk=None):
        """Request signatures for a document"""
        document = self.get_object()
        serializer = CreateSignatureRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            signers = serializer.validated_data['signers']
            expires_in_hours = serializer.validated_data['expires_in_hours']
            expires_at = timezone.now() + timedelta(hours=expires_in_hours)
            
            signature_requests = []
            
            for signer in signers:
                # Generate secure token
                token = secrets.token_urlsafe(32)
                
                # Create signature request
                signature_request = SignatureRequest.objects.create(
                    document=document,
                    signer_name=signer['name'],
                    signer_email=signer['email'],
                    signer_role=signer.get('role', 'Signer'),
                    token=token,
                    expires_at=expires_at,
                    signature_x=signer.get('x', 100),
                    signature_y=signer.get('y', 100),
                    signature_page=signer.get('page', 1)
                )
                
                # Send signature request email
                self._send_signature_request_email(signature_request, request)
                
                # Log the action
                SignatureAuditLog.objects.create(
                    signature_request=signature_request,
                    action='REQUEST_CREATED',
                    details={'expires_at': expires_at.isoformat()},
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                signature_requests.append(signature_request)
            
            # Update document status
            document.status = 'PENDING_SIGNATURE'
            document.save()
            
            # Serialize and return the created requests
            serializer = SignatureRequestSerializer(
                signature_requests, 
                many=True, 
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_signature_request_email(self, signature_request, request):
        """Send signature request email"""
        try:
            # Use configured SITE_URL for consistency
            signing_url = signature_request.generate_signing_url()
            
            subject = f'Signature Request: {signature_request.document.title}'
            
            # Create email content
            context = {
                'signer_name': signature_request.signer_name,
                'document_title': signature_request.document.title,
                'signer_role': signature_request.signer_role,
                'signing_url': signing_url,
                'expires_at': signature_request.expires_at,
                'sender_name': request.user.get_full_name() or request.user.username,
            }
            
            message = f"""
Hello {signature_request.signer_name},

You have been requested to provide your digital signature for the following document:

Document: {signature_request.document.title}
Your Role: {signature_request.signer_role}
Requested by: {context['sender_name']}

To sign the document, please click the secure link below:
{signing_url}

This link will expire on {signature_request.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

For security reasons, this link is unique to you and should not be shared.

If you have any questions, please contact the document sender.

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[signature_request.signer_email],
                fail_silently=False,
            )
            
            # Update sent timestamp
            signature_request.sent_at = timezone.now()
            signature_request.save()
            
            # Log email sent
            SignatureAuditLog.objects.create(
                signature_request=signature_request,
                action='EMAIL_SENT',
                details={'email': signature_request.signer_email},
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
        except Exception as e:
            print(f"Failed to send signature request email: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SignatureRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing signature requests"""
    queryset = SignatureRequest.objects.all()
    serializer_class = SignatureRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter signature requests based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(document__created_by=self.request.user)


class SigningViewSet(viewsets.ViewSet):
    """ViewSet for the signing process"""
    permission_classes = [AllowAny]  # Token-based access
    
    @action(detail=False, methods=['get'], url_path='verify/(?P<token>[^/.]+)')
    def verify_token(self, request, token=None):
        """Verify signature token and return signing information"""
        try:
            signature_request = get_object_or_404(SignatureRequest, token=token)
            
            # Log access
            SignatureAuditLog.objects.create(
                signature_request=signature_request,
                action='LINK_ACCESSED',
                details={'token': token[:8] + '...'},  # Log partial token for security
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if not signature_request.is_valid():
                return Response(
                    {'error': 'Signature request has expired or is no longer valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return signing information
            serializer = SignatureRequestSerializer(signature_request, context={'request': request})
            return Response(serializer.data)
            
        except SignatureRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid signature token'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='sign/(?P<token>[^/.]+)')
    def sign_document(self, request, token=None):
        """Process the digital signature"""
        try:
            signature_request = get_object_or_404(SignatureRequest, token=token)
            
            if not signature_request.is_valid():
                return Response(
                    {'error': 'Signature request has expired or is no longer valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if signature_request.status == 'SIGNED':
                return Response(
                    {'error': 'Document has already been signed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = SignDocumentSerializer(data=request.data)
            if serializer.is_valid():
                signature_data = serializer.validated_data
                
                # Create digital signature
                digital_signature = self._create_digital_signature(
                    signature_request, 
                    signature_data, 
                    request
                )
                
                # Update signature request status
                signature_request.status = 'SIGNED'
                signature_request.signed_at = timezone.now()
                signature_request.ip_address = self._get_client_ip(request)
                signature_request.user_agent = request.META.get('HTTP_USER_AGENT', '')
                signature_request.save()
                
                # Log signature creation
                SignatureAuditLog.objects.create(
                    signature_request=signature_request,
                    action='SIGNATURE_CREATED',
                    details={
                        'signature_type': signature_data['signature_type'],
                        'signature_id': digital_signature.id
                    },
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Check if all signatures are complete
                self._check_document_completion(signature_request.document)
                
                # Send confirmation email
                self._send_signature_confirmation_email(signature_request)
                
                return Response({
                    'message': 'Document signed successfully',
                    'signature_id': digital_signature.id
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except SignatureRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid signature token'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _create_digital_signature(self, signature_request, signature_data, request):
        """Create digital signature from provided data"""
        signature_type = signature_data['signature_type']
        
        if signature_type == 'DRAWN':
            # Process base64 signature data
            signature_image = self._process_drawn_signature(
                signature_data['signature_data'],
                signature_data['width'],
                signature_data['height']
            )
        elif signature_type == 'UPLOADED':
            signature_image = signature_data['signature_image']
        else:
            # For typed signatures, create a simple image
            signature_image = self._create_typed_signature(signature_data.get('signature_data', ''))
        
        # Generate verification hash
        verification_data = f"{signature_request.token}{timezone.now().isoformat()}"
        verification_hash = hashlib.sha256(verification_data.encode()).hexdigest()
        
        # Create digital signature record
        digital_signature = DigitalSignature.objects.create(
            signature_request=signature_request,
            signature_image=signature_image,
            signature_type=signature_type,
            signature_data=signature_data.get('signature_data', ''),
            verification_hash=verification_hash,
            width=signature_data['width'],
            height=signature_data['height'],
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return digital_signature
    
    def _process_drawn_signature(self, signature_data, width, height):
        """Process base64 signature data and create image file"""
        try:
            # Remove data URL prefix if present
            if signature_data.startswith('data:image'):
                signature_data = signature_data.split(',')[1]
            
            # Decode base64 data
            image_data = base64.b64decode(signature_data)
            
            # Create PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Resize if necessary
            if image.size != (width, height):
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to BytesIO
            output = BytesIO()
            image.save(output, format='PNG')
            output.seek(0)
            
            # Create Django file
            filename = f"signature_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
            return ContentFile(output.getvalue(), name=filename)
            
        except Exception as e:
            raise ValueError(f"Invalid signature data: {e}")
    
    def _create_typed_signature(self, text):
        """Create a simple signature image from typed text"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image
        width, height = 400, 100
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # Save to BytesIO
        output = BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        # Create Django file
        filename = f"typed_signature_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
        return ContentFile(output.getvalue(), name=filename)
    
    def _check_document_completion(self, document):
        """Check if all signatures are complete and update document status"""
        pending_requests = document.signature_requests.filter(status='PENDING').count()
        
        if pending_requests == 0:
            document.status = 'SIGNED'
            document.save()
            
            # Log document completion
            for request in document.signature_requests.all():
                SignatureAuditLog.objects.create(
                    signature_request=request,
                    action='DOCUMENT_SIGNED',
                    details={'document_id': document.id}
                )
    
    def _send_signature_confirmation_email(self, signature_request):
        """Send confirmation email to signer"""
        try:
            subject = f'Signature Confirmation: {signature_request.document.title}'
            
            message = f"""
Hello {signature_request.signer_name},

Thank you for signing the document: {signature_request.document.title}

Your digital signature has been successfully recorded and verified.

Signature Details:
- Document: {signature_request.document.title}
- Your Role: {signature_request.signer_role}
- Signed At: {signature_request.signed_at.strftime('%B %d, %Y at %I:%M %p')}
- Verification Hash: {signature_request.signature.verification_hash[:16]}...

This signature is legally binding and has been securely stored in our system.

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[signature_request.signer_email],
                fail_silently=True,
            )
            
        except Exception as e:
            print(f"Failed to send signature confirmation email: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DigitalSignatureViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing digital signatures"""
    queryset = DigitalSignature.objects.all()
    serializer_class = DigitalSignatureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter signatures based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(signature_request__document__created_by=self.request.user)