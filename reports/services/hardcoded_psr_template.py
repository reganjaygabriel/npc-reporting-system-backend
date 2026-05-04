"""
Hardcoded PSR Template
Provides sample data structure for PSR reports before Excel generation
"""

from datetime import datetime, date
from decimal import Decimal


class HardcodedPSRTemplate:
    """
    Hardcoded PSR template with sample data for testing and development
    """
    
    def __init__(self, report_date=None):
        self.report_date = report_date or date.today()
        self.report_type = 'psr'
        
    def get_sample_data(self):
        """
        Returns hardcoded sample data structure matching the PSR format
        """
        return {
            'AGUS1': {
                1: {
                    'generation': 45678.50,
                    'operating_hours': 22.5,
                    'forced_outage': 0.0,
                    'scheduled_outage': 1.5,
                    'remarks': 'Normal operation'
                },
                2: {
                    'generation': 47234.75,
                    'operating_hours': 23.0,
                    'forced_outage': 0.0,
                    'scheduled_outage': 1.0,
                    'remarks': 'Normal operation'
                }
            },
            'AGUS2': {
                1: {
                    'generation': 48567.80,
                    'operating_hours': 23.5,
                    'forced_outage': 0.0,
                    'scheduled_outage': 0.5,
                    'remarks': 'Normal operation'
                }
            },
            'PULANGI4': {
                1: {
                    'generation': 12345.75,
                    'operating_hours': 18.5,
                    'forced_outage': 2.0,
                    'scheduled_outage': 3.5,
                    'remarks': 'Maintenance work on turbine'
                }
            }
        }
    
    def get_complete_report_data(self):
        """
        Returns complete hardcoded report data structure
        """
        return {
            'report_info': {
                'date': self.report_date,
                'type': self.report_type,
                'title': f'POWER SYSTEM REPORT - {self.report_date.strftime("%B %d, %Y").upper()}'
            },
            'plant_data': self.get_sample_data()
        }


# Utility function to get hardcoded data
def get_hardcoded_psr_data(report_date=None):
    """
    Convenience function to get hardcoded PSR data
    """
    template = HardcodedPSRTemplate(report_date)
    return template.get_complete_report_data()


if __name__ == "__main__":
    template = HardcodedPSRTemplate()
    data = template.get_complete_report_data()
    print("Hardcoded PSR Template created successfully!")
    print(f"Plants: {len(data['plant_data'])}")
    print(f"Report Date: {data['report_info']['date']}")