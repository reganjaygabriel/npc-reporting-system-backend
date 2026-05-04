#!/usr/bin/env python3
"""
Keep Render service warm by making periodic requests
Run this as a cron job on Render
"""

import requests
import os
import time
from datetime import datetime

def keep_warm():
    """Make a request to keep the service warm"""
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
    
    try:
        response = requests.get(f"{base_url}/ping/", timeout=10)
        print(f"[{datetime.now()}] Keep-warm ping: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[{datetime.now()}] Keep-warm failed: {e}")
        return False

if __name__ == "__main__":
    keep_warm()