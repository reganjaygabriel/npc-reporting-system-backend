"""Utility functions for the reports app"""
import requests
from django.core.cache import cache


def get_location_from_ip(ip_address):
    """
    Get approximate location from IP address using ip-api.com
    Returns a string like "City, Region, Country" or "Unknown"
    Results are cached for 24 hours to avoid excessive API calls
    """
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return 'Local Network'
    
    # Check cache first
    cache_key = f'ip_location_{ip_address}'
    cached_location = cache.get(cache_key)
    if cached_location:
        return cached_location
    
    try:
        # Use ip-api.com free API (no key required, 45 requests/minute limit)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', '')
                region = data.get('regionName', '')
                country = data.get('country', '')
                
                # Build location string
                parts = [p for p in [city, region, country] if p]
                location = ', '.join(parts) if parts else 'Unknown'
                
                # Cache for 24 hours (86400 seconds)
                cache.set(cache_key, location, 86400)
                return location
    except Exception as e:
        print(f"Error getting location for IP {ip_address}: {e}")
    
    return 'Unknown'


def get_client_ip(request):
    """
    Extract client IP address from request
    Handles proxy headers like X-Forwarded-For
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip
