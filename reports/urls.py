from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlantViewSet, UnitViewSet, UploadedFileViewSet, 
    GenerationReportViewSet, HistoricalDataViewSet, PlantCapacityViewSet,
    WaterNominationViewSet, ActualGenerationViewSet, TestimonialViewSet, AuditLogViewSet,
    ESignatureViewSet, ReportSignatureViewSet, MonthlyTargetViewSet
)
from .views_authorization import SignatoryAuthorizationViewSet
from .views_signature import DocumentViewSet, SignatureRequestViewSet, DigitalSignatureViewSet, SigningViewSet
from .auth_views_fixed import AuthViewSet, UserViewSet, PasswordResetRequestViewSet
from .views_scheduled import ScheduledReportViewSet, ReportExecutionViewSet
from .views_analytics import (
    PerformanceTrendsView, PlantComparisonView, PredictiveInsightsView,
    AnomalyDetectionView, EfficiencyAnalysisView, WaterNominationAnalysisView
)
from .signature_views import signature_setup_no_auth, save_signature_no_auth
from .health_views import health_check, ping

router = DefaultRouter()
router.register(r'plants', PlantViewSet, basename='plant')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'uploaded-files', UploadedFileViewSet, basename='uploadedfile')
router.register(r'generation-reports', GenerationReportViewSet, basename='generationreport')
router.register(r'historical-data', HistoricalDataViewSet, basename='historicaldata')
router.register(r'plant-capacity', PlantCapacityViewSet, basename='plantcapacity')
router.register(r'water-nominations', WaterNominationViewSet, basename='waternomination')
router.register(r'actual-generations', ActualGenerationViewSet, basename='actualgeneration')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'e-signatures', ESignatureViewSet, basename='esignature')
router.register(r'report-signatures', ReportSignatureViewSet, basename='reportsignature')
router.register(r'monthly-targets', MonthlyTargetViewSet, basename='monthlytarget')
router.register(r'signatory-authorizations', SignatoryAuthorizationViewSet, basename='signatoryauthorization')

# E-signature workflow routes
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'signature-requests', SignatureRequestViewSet, basename='signaturerequest')
router.register(r'digital-signatures', DigitalSignatureViewSet, basename='digitalsignature')
router.register(r'signing', SigningViewSet, basename='signing')

router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'password-reset-requests', PasswordResetRequestViewSet, basename='password-reset-request')
router.register(r'scheduled-reports', ScheduledReportViewSet, basename='scheduledreport')
router.register(r'report-executions', ReportExecutionViewSet, basename='reportexecution')

urlpatterns = [
    path('', include(router.urls)),
    # Health check endpoints (no authentication required)
    path('health/', health_check, name='health_check'),
    path('ping/', ping, name='ping'),
    # Analytics endpoints
    path('analytics/trends/', PerformanceTrendsView.as_view(), name='analytics-trends'),
    path('analytics/comparison/', PlantComparisonView.as_view(), name='analytics-comparison'),
    path('analytics/predictions/', PredictiveInsightsView.as_view(), name='analytics-predictions'),
    path('analytics/anomalies/', AnomalyDetectionView.as_view(), name='analytics-anomalies'),
    path('analytics/efficiency/', EfficiencyAnalysisView.as_view(), name='analytics-efficiency'),
    path('analytics/water-nomination/', WaterNominationAnalysisView.as_view(), name='analytics-water-nomination'),
    # Signature setup endpoints (no authentication required)
    path('signature-setup/<str:token>/', signature_setup_no_auth, name='signature-setup-no-auth'),
    path('save-signature/<str:token>/', save_signature_no_auth, name='save-signature-no-auth'),
]
