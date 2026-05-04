from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from .models_scheduled import ScheduledReport, ReportExecution
from .serializers_scheduled import ScheduledReportSerializer, ReportExecutionSerializer
from .services.automated_reports import AutomatedReportService
from .utils import get_location_from_ip, get_client_ip
import logging

logger = logging.getLogger(__name__)


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scheduled reports"""
    queryset = ScheduledReport.objects.all()
    serializer_class = ScheduledReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports based on user permissions"""
        user = self.request.user
        
        # Admins and managers see all reports
        if user.is_staff or (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'MANAGER']):
            return ScheduledReport.objects.all()
        
        # Others see reports they created or are recipients of
        return ScheduledReport.objects.filter(
            models.Q(created_by=user) | models.Q(recipients=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Set created_by when creating report"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Manually trigger report execution"""
        try:
            scheduled_report = self.get_object()
            logger.info(f"Manual execution requested for report: {scheduled_report.name}")
            
            service = AutomatedReportService()
            service.execute_report(scheduled_report)
            
            # Create audit log for manual report execution
            from .models import AuditLog
            ip_address = get_client_ip(request)
            location = get_location_from_ip(ip_address)
            
            AuditLog.objects.create(
                user=request.user,
                action='EXPORT',
                model_name='ScheduledReport',
                description=f'Manually executed scheduled report: {scheduled_report.name} ({scheduled_report.report_type})',
                ip_address=ip_address,
                location=location
            )
            
            return Response({
                'success': True,
                'message': 'Report generated successfully!',
                'report_id': scheduled_report.id,
                'report_name': scheduled_report.name
            })
                
        except Exception as e:
            logger.error(f"Manual report execution error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'Report execution failed: {str(e)}',
                'details': 'Check backend logs for more information'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get execution history for a report"""
        try:
            scheduled_report = self.get_object()
            executions = ReportExecution.objects.filter(
                scheduled_report=scheduled_report
            ).order_by('-started_at')[:50]
            
            serializer = ReportExecutionSerializer(executions, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Get executions error: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportExecutionViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and managing report execution history"""
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter executions based on user permissions"""
        user = self.request.user
        
        # Admins and managers see all executions
        if user.is_staff or (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'MANAGER']):
            return ReportExecution.objects.all()
        
        # Others see executions of reports they have access to
        return ReportExecution.objects.filter(
            models.Q(scheduled_report__created_by=user) | 
            models.Q(scheduled_report__recipients=user)
        ).distinct()
    
    def destroy(self, request, *args, **kwargs):
        """Delete execution record and associated file"""
        import os
        
        try:
            execution = self.get_object()
            scheduled_report = execution.scheduled_report
            
            # Delete the physical file if it exists
            if execution.file_path:
                file_path = execution.file_path.replace('\\', '/')
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Could not delete file {file_path}: {e}")
            
            # Delete the database record
            execution.delete()
            
            # Update the run_count on the scheduled report
            # Count remaining executions
            remaining_count = ReportExecution.objects.filter(
                scheduled_report=scheduled_report
            ).count()
            scheduled_report.run_count = remaining_count
            scheduled_report.save(update_fields=['run_count'])
            
            return Response({
                'message': 'Execution deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete execution: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the generated report file"""
        from django.http import FileResponse
        import os
        
        try:
            execution = self.get_object()
            
            if not execution.file_path:
                return Response({
                    'error': 'No file available for this execution'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Normalize path (convert backslashes to forward slashes)
            file_path = execution.file_path.replace('\\', '/')
            
            # Check if file exists
            if not os.path.exists(file_path):
                return Response({
                    'error': f'File not found: {file_path}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get filename from path
            filename = os.path.basename(file_path)
            
            # Serve file
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}", exc_info=True)
            return Response({
                'error': f'Download failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
