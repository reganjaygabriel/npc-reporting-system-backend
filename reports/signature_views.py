"""
Temporary signature setup views that don't require authentication
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import SignatoryAuthorization
import json
import base64
import os
from django.conf import settings


@require_http_methods(["GET"])
def signature_setup_no_auth(request, token):
    """Handle signature setup via secure token - NO AUTHENTICATION REQUIRED"""
    try:
        authorization = SignatoryAuthorization.objects.get(
            setup_token=token,
            is_active=True
        )
        
        if not authorization.is_setup_token_valid():
            return JsonResponse({
                'error': 'Setup link has expired. Please contact your administrator.'
            }, status=400)
        
        # Return authorization details for signature setup
        return JsonResponse({
            'signatory_name': authorization.signatory_name,
            'user_name': authorization.user.get_full_name() or authorization.user.username,
            'requires_2fa': authorization.requires_2fa,
            'token': token
        })
        
    except SignatoryAuthorization.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid setup link. Please contact your administrator.'
        }, status=404)
    except Exception as e:
        # Log the actual error for debugging
        print(f"❌ Signature setup error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': 'An error occurred while setting up your signature. Please contact your administrator.'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_signature_no_auth(request, token):
    """Save signature via secure token - NO AUTHENTICATION REQUIRED"""
    try:
        authorization = SignatoryAuthorization.objects.get(
            setup_token=token,
            is_active=True
        )
        
        if not authorization.is_setup_token_valid():
            return JsonResponse({
                'error': 'Setup link has expired. Please contact your administrator.'
            }, status=400)
        
        # Parse JSON data
        data = json.loads(request.body)
        signature_data = data.get('signature')
        
        if not signature_data:
            return JsonResponse({
                'error': 'Signature data is required'
            }, status=400)
        
        # Save signature to admin_signatures folder
        # Decode base64 signature
        format, imgstr = signature_data.split(';base64,')
        ext = format.split('/')[-1]
        
        # Create filename
        filename = f"{authorization.signatory_name.lower().replace(' ', '_').replace('.', '_')}_signature.{ext}"
        
        # Save to admin_signatures folder
        admin_signatures_dir = os.path.join(settings.MEDIA_ROOT, 'admin_signatures')
        os.makedirs(admin_signatures_dir, exist_ok=True)
        
        file_path = os.path.join(admin_signatures_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(imgstr))
        
        # Update authorization
        authorization.signature_created = True
        authorization.setup_token = None  # Invalidate token after use
        authorization.token_expires = None
        authorization.save()
        
        return JsonResponse({
            'message': 'Signature saved successfully! You can now use your e-signature to sign reports.',
            'signature_file': filename
        })
        
    except SignatoryAuthorization.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid setup link. Please contact your administrator.'
        }, status=404)
    except Exception as e:
        # Log the actual error for debugging
        print(f"❌ Save signature error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Failed to save signature: {str(e)}'
        }, status=500)