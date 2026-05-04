from datetime import datetime, timedelta
from django.db.models import Avg, Sum, Max, Min, Count, Q, F
from django.utils import timezone
from ..models import GenerationReport, Plant, HistoricalData, WaterNomination, ActualGeneration
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Advanced analytics and insights service"""
    
    def get_performance_trends(self, plant_id=None, days=30):
        """Get performance trends over time"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = GenerationReport.objects.filter(
            report_date__range=[start_date, end_date]
        )
        
        if plant_id:
            query = query.filter(plant_id=plant_id)
        
        # Daily aggregates
        daily_data = query.values('report_date').annotate(
            total_generation=Sum('generation_kwh'),
            avg_capacity_factor=Avg('capacity_factor'),
            avg_availability=Avg('availability_factor'),
            total_operating_hours=Sum('operating_hours'),
            total_forced_outage=Sum('forced_outage_hours')
        ).order_by('report_date')
        
        return {
            'period': {'start': start_date, 'end': end_date, 'days': days},
            'daily_trends': list(daily_data),
            'summary': self._calculate_trend_summary(daily_data)
        }
    
    def get_plant_comparison(self, start_date=None, end_date=None):
        """Compare performance across all plants using a single query"""
        
        # If no date range provided, use all available data
        if not end_date or not start_date:
            # Get the date range of available data
            date_range = GenerationReport.objects.aggregate(
                min_date=Min('report_date'),
                max_date=Max('report_date')
            )
            
            if date_range['min_date'] and date_range['max_date']:
                start_date = date_range['min_date']
                end_date = date_range['max_date']
            else:
                # Fallback to last 30 days if no data
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        
        # Optimized: Single aggregation query for all plants
        stats_query = GenerationReport.objects.filter(
            report_date__range=[start_date, end_date]
        ).values('plant_id').annotate(
            total_generation=Sum('generation_kwh'),
            avg_capacity_factor=Avg('capacity_factor'),
            avg_availability=Avg('availability_factor'),
            max_capacity_factor=Max('capacity_factor'),
            min_capacity_factor=Min('capacity_factor'),
            total_operating_hours=Sum('operating_hours'),
            total_forced_outage=Sum('forced_outage_hours'),
            report_count=Count('id')
        )
        
        # Create a lookup map for stats
        stats_map = {s['plant_id']: s for s in stats_query}
        
        plants = Plant.objects.filter(is_active=True)
        comparison = []
        
        for plant in plants:
            stats = stats_map.get(plant.id, {
                'total_generation': 0,
                'avg_capacity_factor': 0,
                'avg_availability': 0,
                'max_capacity_factor': 0,
                'min_capacity_factor': 0,
                'total_operating_hours': 0,
                'total_forced_outage': 0,
                'report_count': 0
            })
            
            comparison.append({
                'plant_id': plant.id,
                'plant_code': plant.code,
                'plant_name': plant.name,
                'capacity_mw': float(plant.capacity_mw),
                'total_generation_mwh': float(stats['total_generation'] or 0) / 1000,
                'avg_capacity_factor': float(stats['avg_capacity_factor'] or 0),
                'avg_availability': float(stats['avg_availability'] or 0),
                'max_capacity_factor': float(stats['max_capacity_factor'] or 0),
                'min_capacity_factor': float(stats['min_capacity_factor'] or 0),
                'total_operating_hours': float(stats['total_operating_hours'] or 0),
                'total_forced_outage_hours': float(stats['total_forced_outage'] or 0),
                'days_reported': stats['report_count'],
                'performance_score': self._calculate_performance_score(stats)
            })
        
        comparison.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'plants': comparison,
            'fleet_summary': self._calculate_fleet_summary(comparison)
        }
    
    def get_predictive_insights(self, plant_id, days_ahead=7):
        """Generate predictive insights based on historical patterns"""
        # Get historical data for pattern analysis
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        historical = GenerationReport.objects.filter(
            plant_id=plant_id,
            report_date__range=[start_date, end_date]
        ).values('report_date').annotate(
            daily_generation=Sum('generation_kwh'),
            daily_capacity_factor=Avg('capacity_factor')
        ).order_by('report_date')
        
        if not historical:
            return {'error': 'Insufficient data for predictions'}
        
        # Calculate moving averages
        data_list = list(historical)
        predictions = []
        
        for i in range(days_ahead):
            pred_date = end_date + timedelta(days=i+1)
            
            # Simple moving average prediction
            recent_data = data_list[-7:] if len(data_list) >= 7 else data_list
            avg_generation = sum(d['daily_generation'] for d in recent_data) / len(recent_data)
            avg_cf = sum(d['daily_capacity_factor'] for d in recent_data) / len(recent_data)
            
            predictions.append({
                'date': pred_date,
                'predicted_generation_kwh': float(avg_generation),
                'predicted_capacity_factor': float(avg_cf),
                'confidence': 'medium'
            })
        
        return {
            'plant_id': plant_id,
            'prediction_period': days_ahead,
            'predictions': predictions,
            'based_on_days': len(data_list)
        }
    
    def get_anomaly_detection(self, plant_id=None, days=30):
        """Detect anomalies in generation data"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = GenerationReport.objects.filter(
            report_date__range=[start_date, end_date]
        )
        
        if plant_id:
            query = query.filter(plant_id=plant_id)
        
        # Calculate statistics
        stats = query.aggregate(
            avg_cf=Avg('capacity_factor'),
            std_cf=Avg('capacity_factor'),  # Simplified - would need proper std dev
            avg_gen=Avg('generation_kwh')
        )
        
        # Find anomalies (simplified - values significantly different from average)
        threshold = 2  # Standard deviations
        anomalies = []
        
        reports = query.select_related('plant', 'unit')
        for report in reports:
            cf_diff = abs(float(report.capacity_factor or 0) - float(stats['avg_cf'] or 0))
            
            if cf_diff > 20:  # More than 20% difference
                anomalies.append({
                    'date': report.report_date,
                    'plant': report.plant.name,
                    'unit': report.unit.unit_number,
                    'capacity_factor': float(report.capacity_factor or 0),
                    'expected_range': [
                        float(stats['avg_cf'] or 0) - 20,
                        float(stats['avg_cf'] or 0) + 20
                    ],
                    'deviation': cf_diff,
                    'severity': 'high' if cf_diff > 30 else 'medium'
                })
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'anomalies_found': len(anomalies),
            'anomalies': anomalies[:50],  # Limit to 50
            'statistics': stats
        }
    
    def get_efficiency_analysis(self, plant_id=None, days=30):
        """Analyze operational efficiency"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = GenerationReport.objects.filter(
            report_date__range=[start_date, end_date]
        )
        
        if plant_id:
            query = query.filter(plant_id=plant_id)
        
        # Calculate efficiency metrics
        data = query.aggregate(
            total_generation=Sum('generation_kwh'),
            total_operating_hours=Sum('operating_hours'),
            total_availability_hours=Sum('availability_hours'),
            total_forced_outage=Sum('forced_outage_hours'),
            total_scheduled_outage=Sum('scheduled_outage_hours'),
            avg_capacity_factor=Avg('capacity_factor'),
            avg_availability_factor=Avg('availability_factor')
        )
        
        total_hours = days * 24
        operating_hours = float(data['total_operating_hours'] or 0)
        forced_outage = float(data['total_forced_outage'] or 0)
        scheduled_outage = float(data['total_scheduled_outage'] or 0)
        
        return {
            'period': {'start': start_date, 'end': end_date, 'days': days},
            'generation': {
                'total_mwh': float(data['total_generation'] or 0) / 1000,
                'avg_capacity_factor': float(data['avg_capacity_factor'] or 0),
                'avg_availability_factor': float(data['avg_availability_factor'] or 0)
            },
            'utilization': {
                'operating_hours': operating_hours,
                'operating_percentage': (operating_hours / total_hours * 100) if total_hours > 0 else 0,
                'forced_outage_hours': forced_outage,
                'forced_outage_percentage': (forced_outage / total_hours * 100) if total_hours > 0 else 0,
                'scheduled_outage_hours': scheduled_outage,
                'scheduled_outage_percentage': (scheduled_outage / total_hours * 100) if total_hours > 0 else 0
            },
            'efficiency_score': self._calculate_efficiency_score(data, total_hours)
        }
    
    def get_water_nomination_analysis(self, plant_id=None, days=30):
        """Analyze water nomination vs actual generation"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = WaterNomination.objects.filter(
            nomination_date__range=[start_date, end_date],
            status='APPROVED'
        )
        
        if plant_id:
            query = query.filter(plant_id=plant_id)
        
        analysis = []
        
        for nomination in query.select_related('plant'):
            # Get actual generation for same date
            try:
                actual = ActualGeneration.objects.get(
                    plant=nomination.plant,
                    generation_date=nomination.nomination_date
                )
                
                variance = float(actual.total_actual_mwh) - float(nomination.total_nominated_mwh)
                variance_pct = (variance / float(nomination.total_nominated_mwh) * 100) if nomination.total_nominated_mwh > 0 else 0
                
                analysis.append({
                    'date': nomination.nomination_date,
                    'plant': nomination.plant.name,
                    'nominated_mwh': float(nomination.total_nominated_mwh),
                    'actual_mwh': float(actual.total_actual_mwh),
                    'variance_mwh': variance,
                    'variance_percentage': variance_pct,
                    'accuracy': 100 - abs(variance_pct)
                })
            except ActualGeneration.DoesNotExist:
                pass
        
        # Calculate summary
        if analysis:
            avg_accuracy = sum(a['accuracy'] for a in analysis) / len(analysis)
            total_variance = sum(abs(a['variance_mwh']) for a in analysis)
        else:
            avg_accuracy = 0
            total_variance = 0
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'records_analyzed': len(analysis),
            'average_accuracy': avg_accuracy,
            'total_variance_mwh': total_variance,
            'details': analysis
        }
    
    def _calculate_trend_summary(self, daily_data):
        """Calculate summary statistics for trends"""
        data_list = list(daily_data)
        if not data_list:
            return {}
        
        generations = [d['total_generation'] for d in data_list]
        capacity_factors = [d['avg_capacity_factor'] for d in data_list if d['avg_capacity_factor']]
        
        return {
            'total_generation_mwh': sum(generations) / 1000,
            'avg_daily_generation_mwh': (sum(generations) / len(generations)) / 1000 if generations else 0,
            'avg_capacity_factor': sum(capacity_factors) / len(capacity_factors) if capacity_factors else 0,
            'max_daily_generation_mwh': max(generations) / 1000 if generations else 0,
            'min_daily_generation_mwh': min(generations) / 1000 if generations else 0
        }
    
    def _calculate_performance_score(self, stats):
        """Calculate overall performance score (0-100)"""
        cf = float(stats['avg_capacity_factor'] or 0)
        avail = float(stats['avg_availability'] or 0)
        
        # Weighted score: 60% capacity factor, 40% availability
        score = (cf * 0.6) + (avail * 0.4)
        return round(score, 2)
    
    def _calculate_fleet_summary(self, comparison):
        """Calculate fleet-wide summary"""
        if not comparison:
            return {}
        
        return {
            'total_plants': len(comparison),
            'total_capacity_mw': sum(p['capacity_mw'] for p in comparison),
            'total_generation_mwh': sum(p['total_generation_mwh'] for p in comparison),
            'fleet_avg_capacity_factor': sum(p['avg_capacity_factor'] for p in comparison) / len(comparison),
            'fleet_avg_availability': sum(p['avg_availability'] for p in comparison) / len(comparison),
            'best_performer': comparison[0]['plant_name'] if comparison else None,
            'fleet_performance_score': sum(p['performance_score'] for p in comparison) / len(comparison)
        }
    
    def _calculate_efficiency_score(self, data, total_hours):
        """Calculate efficiency score based on multiple factors"""
        cf = float(data['avg_capacity_factor'] or 0)
        avail = float(data['avg_availability_factor'] or 0)
        forced_outage = float(data['total_forced_outage'] or 0)
        
        # Penalize for forced outages
        forced_outage_penalty = (forced_outage / total_hours * 100) if total_hours > 0 else 0
        
        score = (cf * 0.5) + (avail * 0.4) - (forced_outage_penalty * 0.1)
        return max(0, min(100, round(score, 2)))
