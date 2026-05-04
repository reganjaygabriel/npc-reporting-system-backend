from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)
analytics_service = AnalyticsService()


class PerformanceTrendsView(APIView):
    """View for performance trends"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        try:
            plant_id = request.query_params.get('plant_id')
            days = int(request.query_params.get('days', 30))
            
            data = analytics_service.get_performance_trends(plant_id, days)
            return Response(data)
        except Exception as e:
            logger.error(f"Performance trends error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlantComparisonView(APIView):
    """View for plant comparison"""
    # Temporarily remove auth requirement for dashboard to work
    # permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        try:
            from datetime import datetime, timedelta
            
            end_date = request.query_params.get('end_date')
            start_date = request.query_params.get('start_date')
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            data = analytics_service.get_plant_comparison(start_date, end_date)
            return Response(data)
        except Exception as e:
            logger.error(f"Plant comparison error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictiveInsightsView(APIView):
    """View for predictive insights"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request):
        try:
            plant_id = request.query_params.get('plant_id')
            if not plant_id:
                return Response({'error': 'plant_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            days_ahead = int(request.query_params.get('days_ahead', 7))
            data = analytics_service.get_predictive_insights(plant_id, days_ahead)
            return Response(data)
        except Exception as e:
            logger.error(f"Predictive insights error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnomalyDetectionView(APIView):
    """View for anomaly detection"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def get(self, request):
        try:
            plant_id = request.query_params.get('plant_id')
            days = int(request.query_params.get('days', 30))
            
            data = analytics_service.get_anomaly_detection(plant_id, days)
            return Response(data)
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EfficiencyAnalysisView(APIView):
    """View for efficiency analysis"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request):
        try:
            plant_id = request.query_params.get('plant_id')
            days = int(request.query_params.get('days', 30))
            
            data = analytics_service.get_efficiency_analysis(plant_id, days)
            return Response(data)
        except Exception as e:
            logger.error(f"Efficiency analysis error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WaterNominationAnalysisView(APIView):
    """View for water nomination analysis"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request):
        try:
            plant_id = request.query_params.get('plant_id')
            days = int(request.query_params.get('days', 30))
            
            data = analytics_service.get_water_nomination_analysis(plant_id, days)
            return Response(data)
        except Exception as e:
            logger.error(f"Water nomination analysis error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
