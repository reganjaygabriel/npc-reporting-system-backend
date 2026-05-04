"""
Email Notification Service
Handles all email notifications for the system
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None):
        """
        Send email with error handling
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def notify_upload_success(uploaded_file, user):
        """
        Notify user about successful file upload
        """
        subject = f"Upload Successful - {uploaded_file.plant.name}"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Your file "{uploaded_file.original_filename}" has been successfully uploaded and processed.
        
        Details:
        - Plant: {uploaded_file.plant.name}
        - Records Imported: {uploaded_file.records_imported}
        - Upload Date: {uploaded_file.uploaded_at.strftime('%Y-%m-%d %H:%M')}
        
        Thank you for using NPC Reporting System.
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email] if user.email else []
        )
    
    @staticmethod
    def notify_upload_failure(uploaded_file, user, error_message):
        """
        Notify user about failed file upload
        """
        subject = f"Upload Failed - {uploaded_file.plant.name}"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Unfortunately, your file "{uploaded_file.original_filename}" could not be processed.
        
        Error Details:
        {error_message}
        
        Please check your file format and try again. If the problem persists, contact support.
        
        Thank you for using NPC Reporting System.
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email] if user.email else []
        )
    
    @staticmethod
    def notify_nomination_submitted(nomination, user):
        """
        Notify managers about new water nomination submission
        """
        subject = f"New Water Nomination - {nomination.plant.name}"
        message = f"""
        A new water nomination has been submitted for approval.
        
        Details:
        - Plant: {nomination.plant.name}
        - Date: {nomination.nomination_date}
        - Type: {nomination.get_nomination_type_display()}
        - Submitted By: {user.get_full_name() or user.username}
        - Total Nominated: {nomination.total_nominated_mwh} MWh
        
        Please review and approve at your earliest convenience.
        """
        
        from django.db.models import Q
        
        # Get all managers and admins
        managers = User.objects.filter(
            is_active=True
        ).filter(
            Q(is_staff=True) | 
            Q(profile__role__in=['MANAGER', 'ADMIN'])
        )
        
        recipient_list = [m.email for m in managers if m.email]
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=recipient_list
        )
    
    @staticmethod
    def notify_nomination_approved(nomination, approved_by):
        """
        Notify submitter about nomination approval
        """
        if not nomination.submitted_by:
            return False
        
        subject = f"Nomination Approved - {nomination.plant.name}"
        message = f"""
        Hello {nomination.submitted_by.get_full_name() or nomination.submitted_by.username},
        
        Your water nomination has been approved.
        
        Details:
        - Plant: {nomination.plant.name}
        - Date: {nomination.nomination_date}
        - Approved By: {approved_by.get_full_name() or approved_by.username}
        - Total Nominated: {nomination.total_nominated_mwh} MWh
        
        Thank you for using NPC Reporting System.
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[nomination.submitted_by.email] if nomination.submitted_by.email else []
        )
    
    @staticmethod
    def notify_nomination_rejected(nomination, rejected_by, reason):
        """
        Notify submitter about nomination rejection
        """
        if not nomination.submitted_by:
            return False
        
        subject = f"Nomination Rejected - {nomination.plant.name}"
        message = f"""
        Hello {nomination.submitted_by.get_full_name() or nomination.submitted_by.username},
        
        Your water nomination has been rejected.
        
        Details:
        - Plant: {nomination.plant.name}
        - Date: {nomination.nomination_date}
        - Rejected By: {rejected_by.get_full_name() or rejected_by.username}
        - Reason: {reason}
        
        Please review and resubmit with corrections.
        
        Thank you for using NPC Reporting System.
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[nomination.submitted_by.email] if nomination.submitted_by.email else []
        )
    
    @staticmethod
    def notify_user_registered(user):
        """
        Welcome email for new users
        """
        subject = "Welcome to NPC Reporting System"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Welcome to the NPC Reporting System!
        
        Your account has been created successfully. You can now log in and start using the system.
        
        Username: {user.username}
        
        If you have any questions, please contact your system administrator.
        
        Best regards,
        NPC Reporting System Team
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email] if user.email else []
        )
    
    @staticmethod
    def notify_password_changed(user):
        """
        Notify user about password change
        """
        subject = "Password Changed - NPC Reporting System"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Your password has been changed successfully.
        
        If you did not make this change, please contact your administrator immediately.
        
        Best regards,
        NPC Reporting System Team
        """
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=[user.email] if user.email else []
        )
    
    @staticmethod
    def notify_daily_summary(date, summary_data):
        """
        Send daily summary report to managers
        """
        subject = f"Daily Generation Summary - {date}"
        message = f"""
        Daily Generation Summary for {date}
        
        Total Generation: {summary_data.get('total_generation', 0)} MWh
        Average Capacity Factor: {summary_data.get('avg_capacity_factor', 0)}%
        Plants Reporting: {summary_data.get('plants_reporting', 0)}
        
        Please log in to view detailed reports.
        """
        
        # Get all managers and admins
        managers = User.objects.filter(
            is_active=True,
            is_staff=True
        )
        
        recipient_list = [m.email for m in managers if m.email]
        
        return EmailService.send_email(
            subject=subject,
            message=message,
            recipient_list=recipient_list
        )


def send_password_reset_notification(reset_request):
    """
    Send email notification to admins about password reset request
    """
    subject = f"Password Reset Request - {reset_request.username}"
    message = f"""
    A password reset request has been submitted.
    
    Details:
    - Username: {reset_request.username}
    - Reason: {reset_request.reason or 'Not provided'}
    - Request Date: {reset_request.created_at.strftime('%Y-%m-%d %H:%M')}
    - IP Address: {reset_request.ip_address or 'Unknown'}
    
    Please review this request in the admin panel and contact the user to reset their password.
    
    Contact Information:
    Email: gpd.support@npc.gov.ph
    
    NPC Reporting System
    """
    
    # Get all admin users
    from django.contrib.auth.models import User
    from django.db.models import Q
    
    admins = User.objects.filter(
        is_active=True
    ).filter(
        Q(is_staff=True) | 
        Q(profile__role='ADMIN')
    )
    
    recipient_list = [admin.email for admin in admins if admin.email]
    
    # If no admin emails, use default support email
    if not recipient_list:
        recipient_list = ['gpd.support@npc.gov.ph']
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"Password reset notification sent for user: {reset_request.username}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset notification: {str(e)}")
        return False
