"""
NPC Live Data Client
Connects to NPC's live data sources (API, Database, Web Service, etc.)
Ready to use once NPC provides access credentials
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NPCLiveDataClient:
    """
    Client for fetching live data from NPC systems
    Supports multiple connection types: REST API, SOAP, Database, WebSocket
    """
    
    def __init__(self):
        # Load configuration from Django settings
        self.api_url = getattr(settings, 'NPC_API_URL', None)
        self.api_key = getattr(settings, 'NPC_API_KEY', None)
        self.username = getattr(settings, 'NPC_USERNAME', None)
        self.password = getattr(settings, 'NPC_PASSWORD', None)
        self.timeout = getattr(settings, 'NPC_API_TIMEOUT', 30)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NPC-Reporting-System/1.0',
            'Accept': 'application/json',
        })
        
        # Add API key if provided
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def test_connection(self) -> Dict:
        """
        Test connection to NPC live data source
        
        Returns:
            Dict with connection status and details
        """
        result = {
            'success': False,
            'message': '',
            'timestamp': datetime.now().isoformat(),
            'config_status': {}
        }
        
        # Check configuration
        result['config_status'] = {
            'api_url_configured': bool(self.api_url),
            'api_key_configured': bool(self.api_key),
            'username_configured': bool(self.username),
            'password_configured': bool(self.password),
        }
        
        if not self.api_url:
            result['message'] = 'NPC API URL not configured. Add NPC_API_URL to settings.'
            return result
        
        try:
            # Try to connect to the API
            response = self.session.get(
                f"{self.api_url}/health",  # Common health check endpoint
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result['success'] = True
                result['message'] = 'Successfully connected to NPC live data source'
            else:
                result['message'] = f'Connection failed with status code: {response.status_code}'
        
        except requests.exceptions.ConnectionError:
            result['message'] = 'Cannot connect to NPC API. Check URL and network connection.'
        except requests.exceptions.Timeout:
            result['message'] = f'Connection timeout after {self.timeout} seconds'
        except Exception as e:
            result['message'] = f'Connection error: {str(e)}'
        
        return result
    
    def fetch_plant_status(self, plant_codes: Optional[List[str]] = None) -> Dict:
        """
        Fetch live plant status from NPC
        
        Args:
            plant_codes: List of plant codes to fetch (None = all plants)
        
        Returns:
            Dict with plant status data
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'source': 'npc_live_api',
            'plants': [],
            'error': None
        }
        
        if not self.api_url:
            result['error'] = 'NPC API URL not configured'
            return result
        
        try:
            # Build request parameters
            params = {}
            if plant_codes:
                params['plants'] = ','.join(plant_codes)
            
            # Make API request
            response = self.session.get(
                f"{self.api_url}/plants/status",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response (adjust based on actual NPC API format)
            result['success'] = True
            result['plants'] = self._parse_plant_data(data)
        
        except requests.exceptions.RequestException as e:
            result['error'] = f'API request failed: {str(e)}'
            logger.error(f"NPC API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            result['error'] = f'Invalid JSON response: {str(e)}'
            logger.error(f"Invalid JSON from NPC API: {str(e)}")
        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
            logger.error(f"Unexpected error fetching NPC data: {str(e)}")
        
        return result
    
    def fetch_generation_data(self, plant_code: str, start_date: str, end_date: str) -> Dict:
        """
        Fetch generation data for a specific plant and date range
        
        Args:
            plant_code: Plant code (e.g., 'AGUS1')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict with generation data
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'plant_code': plant_code,
            'date_range': {'start': start_date, 'end': end_date},
            'data': [],
            'error': None
        }
        
        if not self.api_url:
            result['error'] = 'NPC API URL not configured'
            return result
        
        try:
            response = self.session.get(
                f"{self.api_url}/plants/{plant_code}/generation",
                params={'start_date': start_date, 'end_date': end_date},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            result['success'] = True
            result['data'] = data.get('generation_data', [])
        
        except Exception as e:
            result['error'] = f'Failed to fetch generation data: {str(e)}'
            logger.error(f"Failed to fetch generation data: {str(e)}")
        
        return result
    
    def fetch_water_levels(self, plant_codes: Optional[List[str]] = None) -> Dict:
        """
        Fetch current water levels for plants
        
        Args:
            plant_codes: List of plant codes (None = all plants)
        
        Returns:
            Dict with water level data
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'water_levels': [],
            'error': None
        }
        
        if not self.api_url:
            result['error'] = 'NPC API URL not configured'
            return result
        
        try:
            params = {}
            if plant_codes:
                params['plants'] = ','.join(plant_codes)
            
            response = self.session.get(
                f"{self.api_url}/water-levels",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            result['success'] = True
            result['water_levels'] = data.get('water_levels', [])
        
        except Exception as e:
            result['error'] = f'Failed to fetch water levels: {str(e)}'
            logger.error(f"Failed to fetch water levels: {str(e)}")
        
        return result
    
    def _parse_plant_data(self, data: Dict) -> List[Dict]:
        """
        Parse plant data from NPC API response
        Adjust this method based on actual NPC API format
        
        Args:
            data: Raw API response data
        
        Returns:
            List of parsed plant data dictionaries
        """
        plants = []
        
        # Example parsing - adjust based on actual API format
        if isinstance(data, dict) and 'plants' in data:
            for plant in data['plants']:
                plants.append({
                    'plant_code': plant.get('code'),
                    'plant_name': plant.get('name'),
                    'capacity_mw': plant.get('capacity'),
                    'current_generation_mw': plant.get('current_generation'),
                    'water_level': plant.get('water_level'),
                    'status': plant.get('status'),
                    'timestamp': plant.get('timestamp', datetime.now().isoformat())
                })
        
        return plants
    
    def sync_to_database(self, plant_data: List[Dict]) -> Dict:
        """
        Sync live data to local database
        
        Args:
            plant_data: List of plant data dictionaries
        
        Returns:
            Dict with sync results
        """
        from reports.models import Plant, GenerationReport, Unit
        from django.utils import timezone
        
        result = {
            'success': False,
            'synced_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        try:
            for plant_info in plant_data:
                try:
                    # Get or create plant
                    plant = Plant.objects.filter(
                        code=plant_info['plant_code']
                    ).first()
                    
                    if not plant:
                        result['errors'].append(
                            f"Plant {plant_info['plant_code']} not found in database"
                        )
                        result['failed_count'] += 1
                        continue
                    
                    # Here you would create GenerationReport entries
                    # This is a simplified example
                    result['synced_count'] += 1
                
                except Exception as e:
                    result['errors'].append(f"Error syncing {plant_info.get('plant_code')}: {str(e)}")
                    result['failed_count'] += 1
            
            result['success'] = result['synced_count'] > 0
        
        except Exception as e:
            result['errors'].append(f"Sync failed: {str(e)}")
        
        return result


# Singleton instance
_client = None

def get_npc_client() -> NPCLiveDataClient:
    """Get singleton instance of NPC client"""
    global _client
    if _client is None:
        _client = NPCLiveDataClient()
    return _client
