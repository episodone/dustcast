#!/usr/bin/env python3
"""
Enhanced monitoring script with Python 3.13 optimizations
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

class DustStormMonitor:
    """Enhanced monitoring class"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_health(self):
        """Check service health"""
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=10) as response:
                return response.status == 200
        except:
            return False
    
    async def check_api_status(self):
        """Check API endpoints"""
        endpoints = {
            'current': '/api/current',
            'forecast': '/api/forecast',
            'status': '/api/status'
        }
        
        results = {}
        for name, endpoint in endpoints.items():
            try:
                async with self.session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                    results[name] = response.status == 200
            except:
                results[name] = False
        
        return results
    
    async def get_current_data(self):
        """Get current dust storm data"""
        try:
            async with self.session.get(f"{self.base_url}/api/current", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
        except:
            pass
        return None

async def main():
    """Main monitoring function with async support"""
    print(f"🔍 Enhanced Dust Storm Monitor - {datetime.now()}")
    print(f"🐍 Python {sys.version}")
    print("-" * 50)
    
    async with DustStormMonitor() as monitor:
        # Check overall health
        health = await monitor.check_health()
        print(f"🏥 Service Health: {'✅ Healthy' if health else '❌ Unhealthy'}")
        
        if not health:
            print("💡 Make sure the application is running: ./run.sh")
            return 1
        
        # Check API endpoints
        api_status = await monitor.check_api_status()
        print("📡 API Endpoints:")
        for endpoint, status in api_status.items():
            print(f"   {endpoint:<10}: {'✅' if status else '❌'}")
        
        # Get current data
        current_data = await monitor.get_current_data()
        if current_data:
            print("\n📊 Current Conditions:")
            print(f"   Risk Level: {current_data.get('risk_level', 'unknown').upper()}")
            print(f"   Risk Index: {current_data.get('risk_index', 'N/A')}")
            print(f"   Temperature: {current_data.get('temperature', 'N/A')}°C")
            print(f"   NDVI: {current_data.get('ndvi', 'N/A')}")
            print(f"   NDDI: {current_data.get('nddi', 'N/A')}")
            
            # Risk assessment
            risk_index = current_data.get('risk_index', 0)
            if risk_index > 0.6:
                print("⚠️ HIGH RISK - Take precautionary measures!")
            elif risk_index > 0.3:
                print("⚡ MODERATE RISK - Monitor conditions")
            else:
                print("✅ LOW RISK - Conditions favorable")
        else:
            print("⚠️ Could not retrieve current conditions")
        
        # Performance metrics
        print(f"\n⏱️ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return 0

if __name__ == "__main__":
    if sys.version_info >= (3, 7):
        exit_code = asyncio.run(main())
    else:
        print("❌ Python 3.7+ required for async monitoring")
        exit_code = 1
    
    sys.exit(exit_code)
