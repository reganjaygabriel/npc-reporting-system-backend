from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection
import time

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Lightweight health check endpoint for uptime monitoring
    Keeps Render server warm and checks database connectivity
    """
    start_time = time.time()
    
    try:
        # Quick database connectivity check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        db_status = "healthy"
        db_response_time = round((time.time() - start_time) * 1000, 2)
        
    except Exception as e:
        db_status = "unhealthy"
        db_response_time = None
    
    return JsonResponse({
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "database": {
            "status": db_status,
            "response_time_ms": db_response_time
        },
        "uptime_check": True
    })

@csrf_exempt
@require_http_methods(["GET"])
def ping(request):
    """Ultra-lightweight ping endpoint"""
    return JsonResponse({"pong": True, "timestamp": timezone.now().isoformat()})