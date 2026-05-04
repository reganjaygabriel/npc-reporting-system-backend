"""
Django signals for automatic email workflow
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SignatoryAuthorizationRequest
from .serializers_security import trigger_email_workflow


@receiver(post_save, sender=SignatoryAuthorizationRequest)
def handle_authorization_request_created(sender, instance, created, **kwargs):
    """
    Signal handler that triggers email workflow when a new authorization request is created
    """
    if created:  # Only for new requests, not updates
        print(f"🔥 SIGNAL TRIGGERED: New authorization request created for {instance.signatory_name}")
        
        try:
            # Call the email workflow function
            success = trigger_email_workflow(instance)
            if success:
                print(f"✅ Signal-triggered email workflow completed for {instance.signatory_name}")
            else:
                print(f"❌ Signal-triggered email workflow failed for {instance.signatory_name}")
        except Exception as e:
            print(f"❌ Error in signal handler: {e}")
            import traceback
            traceback.print_exc()