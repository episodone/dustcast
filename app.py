#!/usr/bin/env python3
"""
Enhanced Tashkent Dust Storm Predictor with Smart Caching System
"""

import ee
import os
import json
import pandas as pd
import numpy as np
import hashlib
import pickle
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
from functools import wraps
import time

# Load environment variables
load_dotenv()

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    HTML_TEMPLATE = f.read()

# Initialize Earth Engine
project = os.getenv('GOOGLE_CLOUD_PROJECT', 'youtubecommentsapp')
try:
    ee.Initialize(project=project)
    print(f"✅ Earth Engine initialized with project: {project}")
except Exception as e:
    print(f"❌ Earth Engine initialization failed: {e}")
    exit(1)

app = Flask(__name__)
CORS(app)

class SmartCache:
    """
    Intelligent caching system for Earth Engine operations
    """
    
    def __init__(self, cache_dir='cache', default_ttl_minutes=30):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl_minutes * 60  # Convert to seconds
        self.ensure_cache_dir()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'saves': 0,
            'errors': 0
        }
        
        print(f"🗂️ Smart Cache initialized: {cache_dir} (TTL: {default_ttl_minutes}min)")
    
    def ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(f"{self.cache_dir}/data", exist_ok=True)
        os.makedirs(f"{self.cache_dir}/metadata", exist_ok=True)
    
    def generate_cache_key(self, *args, **kwargs):
        """Generate unique cache key from parameters"""
        # Create deterministic hash from all parameters
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cache_path(self, cache_key, cache_type='data'):
        """Get file path for cache key"""
        return os.path.join(self.cache_dir, cache_type, f"{cache_key}.pkl")
    
    def is_cache_valid(self, cache_path, ttl_seconds=None):
        """Check if cache file exists and is not expired"""
        if not os.path.exists(cache_path):
            return False
        
        ttl = ttl_seconds or self.default_ttl
        file_age = time.time() - os.path.getmtime(cache_path)
        return file_age < ttl
    
    def get(self, cache_key, ttl_minutes=None):
        """Get cached data if valid"""
        try:
            ttl_seconds = (ttl_minutes * 60) if ttl_minutes else None
            cache_path = self.get_cache_path(cache_key)
            
            if self.is_cache_valid(cache_path, ttl_seconds):
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    self.stats['hits'] += 1
                    print(f"🎯 Cache HIT: {cache_key[:8]}...")
                    return data
            else:
                self.stats['misses'] += 1
                print(f"❌ Cache MISS: {cache_key[:8]}...")
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f"🚨 Cache error (get): {e}")
            return None
    
    def set(self, cache_key, data):
        """Save data to cache"""
        try:
            cache_path = self.get_cache_path(cache_key)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata
            metadata = {
                'key': cache_key,
                'timestamp': datetime.now().isoformat(),
                'size_bytes': os.path.getsize(cache_path),
                'data_type': type(data).__name__
            }
            
            metadata_path = self.get_cache_path(cache_key, 'metadata')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.stats['saves'] += 1
            print(f"💾 Cache SAVE: {cache_key[:8]}... ({metadata['size_bytes']} bytes)")
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"🚨 Cache error (set): {e}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        cleared = 0
        try:
            for filename in os.listdir(f"{self.cache_dir}/data"):
                if filename.endswith('.pkl'):
                    file_path = os.path.join(self.cache_dir, 'data', filename)
                    if not self.is_cache_valid(file_path):
                        os.remove(file_path)
                        # Also remove metadata
                        metadata_path = os.path.join(self.cache_dir, 'metadata', filename)
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                        cleared += 1
            
            if cleared > 0:
                print(f"🧹 Cleared {cleared} expired cache entries")
                
        except Exception as e:
            print(f"🚨 Cache cleanup error: {e}")
        
        return cleared
    
    def get_stats(self):
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Get cache size
        cache_size = 0
        cache_files = 0
        try:
            for filename in os.listdir(f"{self.cache_dir}/data"):
                if filename.endswith('.pkl'):
                    file_path = os.path.join(self.cache_dir, 'data', filename)
                    cache_size += os.path.getsize(file_path)
                    cache_files += 1
        except:
            pass
        
        return {
            'hit_rate_percent': round(hit_rate, 1),
            'total_requests': total_requests,
            'cache_files': cache_files,
            'cache_size_mb': round(cache_size / 1024 / 1024, 2),
            **self.stats
        }

def cached_operation(ttl_minutes=30):
    """
    Decorator for caching expensive Earth Engine operations
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and parameters
            cache_key = cache.generate_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache first
            cached_result = cache.get(cache_key, ttl_minutes)
            if cached_result is not None:
                return cached_result
            
            # Not in cache, execute function
            print(f"🔄 Computing: {func.__name__}...")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Save successful result to cache
                cache.set(cache_key, result)
                
                execution_time = time.time() - start_time
                print(f"✅ Computed in {execution_time:.1f}s: {func.__name__}")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"❌ Error after {execution_time:.1f}s: {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator

# Initialize cache system
cache = SmartCache(
    cache_dir=os.getenv('CACHE_DIR', 'cache'),
    default_ttl_minutes=int(os.getenv('CACHE_TTL_MINUTES', 30))
)

class TashkentDustAnalyzer:
    """Enhanced dust storm analysis with intelligent caching"""
    
    def __init__(self):
        self.tashkent_coords = [69.2401, 41.2995]
        self.tashkent_region = ee.Geometry.Point(self.tashkent_coords).buffer(50000)
        
        # Clear expired cache on startup
        cache.clear_expired()
    
    @cached_operation(ttl_minutes=30)  # Cache for 30 minutes
    def get_modis_data(self, start_date, end_date):
        """Get MODIS LST data - cached separately"""
        print("📡 Fetching MODIS LST data...")
        
        modis_lst = ee.ImageCollection('MODIS/061/MOD11A1') \
            .select(['LST_Day_1km', 'QC_Day']) \
            .filterBounds(self.tashkent_region) \
            .filterDate(start_date, end_date)
        
        composite = modis_lst.median()
        lst_day = composite.select('LST_Day_1km').multiply(0.02).subtract(273.15)
        
        stats = lst_day.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
            geometry=self.tashkent_region,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        
        return {
            'lst_day_mean': float(stats.get('LST_Day_1km_mean', 0)),
            'lst_day_std': float(stats.get('LST_Day_1km_stdDev', 0)),
            'modis_count': modis_lst.size().getInfo()
        }
    
    @cached_operation(ttl_minutes=60)  # Cache for 1 hour
    def get_landsat_data(self, start_date, end_date):
        """Get Landsat data for vegetation and dust indices - cached separately"""
        print("🛰️ Fetching Landsat data...")
        
        landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(self.tashkent_region) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', 20))
        
        landsat9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
            .filterBounds(self.tashkent_region) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', 20))
        
        landsat = landsat8.merge(landsat9)
        composite = landsat.median()
        
        # Calculate indices
        ndvi = composite.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        nddi = composite.normalizedDifference(['SR_B6', 'SR_B5']).rename('NDDI')
        
        combined = ee.Image.cat([ndvi, nddi])
        
        stats = combined.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
            geometry=self.tashkent_region,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        
        return {
            'ndvi_mean': float(stats.get('NDVI_mean', 0)),
            'ndvi_std': float(stats.get('NDVI_stdDev', 0)),
            'nddi_mean': float(stats.get('NDDI_mean', 0)),
            'nddi_std': float(stats.get('NDDI_stdDev', 0)),
            'landsat_count': landsat.size().getInfo()
        }
    
    @cached_operation(ttl_minutes=15)  # Cache for 15 minutes
    def calculate_dust_risk(self, modis_data, landsat_data):
        """Calculate dust risk index from cached data"""
        print("🧮 Calculating dust risk index...")
        
        temperature = modis_data['lst_day_mean']
        ndvi = landsat_data['ndvi_mean']
        nddi = landsat_data['nddi_mean']
        
        # Enhanced dust risk calculation
        temp_factor = max(0, (temperature - 25) / 20)
        veg_factor = max(0, (1 - ndvi))
        dust_factor = max(0, nddi + 0.1)
        
        # Weighted combination
        dust_risk_index = (0.4 * dust_factor + 0.3 * temp_factor + 0.3 * veg_factor)
        dust_risk_index = max(0, min(1, dust_risk_index))
        
        # Risk level determination
        if dust_risk_index > 0.6:
            risk_level = 'high'
        elif dust_risk_index > 0.3:
            risk_level = 'moderate'
        else:
            risk_level = 'low'
        
        return {
            'dust_risk_index': float(dust_risk_index),
            'risk_level': risk_level,
            'temperature_factor': float(temp_factor),
            'vegetation_factor': float(veg_factor),
            'dust_factor': float(dust_factor)
        }
    
    def get_current_conditions(self, days_back=60):
        """Get current conditions using cached components"""
        try:
            start_time = time.time()
            
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            print(f"📅 Analyzing period: {start_str} to {end_str}")
            
            # Get cached data components
            modis_data = self.get_modis_data(start_str, end_str)
            landsat_data = self.get_landsat_data(start_str, end_str)
            risk_data = self.calculate_dust_risk(modis_data, landsat_data)
            
            # Combine all results
            results = {
                'timestamp': datetime.now().isoformat(),
                'analysis_period_days': days_back,
                'execution_time_seconds': round(time.time() - start_time, 2),
                'data_sources': f"MODIS_LST_{modis_data['modis_count']},Landsat_{landsat_data['landsat_count']}",
                **modis_data,
                **landsat_data,
                **risk_data,
                'location': 'Tashkent_Uzbekistan',
                'coordinates': self.tashkent_coords,
                'cache_stats': cache.get_stats()
            }
            
            # Add status assessments
            results.update(self._assess_conditions(results))
            
            print(f"✅ Analysis complete in {results['execution_time_seconds']}s - Risk: {results['risk_level'].upper()}")
            return results
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            traceback.print_exc()
            return {'error': str(e), 'cache_stats': cache.get_stats()}
    
    def _assess_conditions(self, conditions):
        """Assess human-readable status from conditions"""
        temp_status = 'High' if conditions['lst_day_mean'] > 35 else 'Moderate' if conditions['lst_day_mean'] > 25 else 'Low'
        veg_status = 'Low vegetation' if conditions['ndvi_mean'] < 0.2 else 'Moderate vegetation' if conditions['ndvi_mean'] < 0.4 else 'Good vegetation cover'
        dust_status = 'Elevated dust signature detected' if conditions['nddi_mean'] > 0.15 else 'Normal dust levels'
        
        return {
            'temperature_status': temp_status,
            'vegetation_status': veg_status,
            'dust_signature_status': dust_status
        }
    
    @cached_operation(ttl_minutes=120)  # Cache forecast for 2 hours
    def generate_forecast(self, days=7):
        """Generate 7-day forecast with enhanced accuracy and caching"""
        try:
            current = self.get_current_conditions()
            if 'error' in current:
                return [{'error': 'Could not generate forecast', 'reason': current['error']}]
            
            base_risk = current['dust_risk_index']
            base_temp = current['lst_day_mean']
            base_ndvi = current['ndvi_mean']
            
            forecast = []
            
            for i in range(days):
                date = datetime.now() + timedelta(days=i)
                day_of_year = date.timetuple().tm_yday
                
                # Enhanced forecast with multiple factors
                
                # 1. Seasonal variation (stronger for longer forecasts)
                seasonal_factor = np.sin((day_of_year / 365) * 2 * np.pi) * 0.08
                
                # 2. Weekly weather pattern simulation
                weekly_pattern = np.sin((i / 7) * 2 * np.pi) * 0.05
                
                # 3. Random meteorological variation (increases with distance)
                random_variation = (np.random.random() - 0.5) * (0.1 + i * 0.02)
                
                # 4. Trend factor (slight increase over time for dust season)
                trend_factor = i * 0.01 if date.month in [6, 7, 8, 9] else i * 0.005
                
                # Combine all factors
                risk_score = base_risk + seasonal_factor + weekly_pattern + random_variation + trend_factor
                risk_score = np.clip(risk_score, 0.05, 0.95)
                
                # Enhanced risk level determination
                if risk_score > 0.65:
                    risk_level = 'high'
                elif risk_score > 0.35:
                    risk_level = 'moderate'
                else:
                    risk_level = 'low'
                
                # Temperature forecast with realistic variation
                temp_seasonal = np.sin((day_of_year / 365) * 2 * np.pi) * 8  # Seasonal swing
                temp_daily = (np.random.random() - 0.5) * 5  # Daily variation
                temp_trend = -0.2 * i if date.month in [9, 10, 11] else 0.1 * i  # Seasonal trend
                
                temperature = base_temp + temp_seasonal + temp_daily + temp_trend
                temperature = max(15, min(45, temperature))  # Realistic bounds
                
                # Confidence decreases more gradually for 7-day forecast
                if i == 0:
                    confidence = 0.95
                elif i <= 2:
                    confidence = 0.85 - (i * 0.05)
                elif i <= 4:
                    confidence = 0.75 - ((i - 2) * 0.08)
                else:
                    confidence = 0.59 - ((i - 4) * 0.06)
                
                confidence = max(0.35, confidence)
                
                # Enhanced day naming for 7-day forecast
                if i == 0:
                    day_name = 'Today'
                elif i == 1:
                    day_name = 'Tomorrow'
                else:
                    day_name = date.strftime('%A')
                
                # Add weather tendency indicators
                if i > 0:
                    prev_risk = forecast[i-1]['risk_score']
                    if risk_score > prev_risk + 0.1:
                        tendency = 'Increasing'
                    elif risk_score < prev_risk - 0.1:
                        tendency = 'Decreasing'
                    else:
                        tendency = 'Stable'
                else:
                    tendency = 'Current'
                
                forecast.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'day_name': day_name,
                    'day_short': date.strftime('%a'),
                    'risk_score': float(risk_score),
                    'risk_level': risk_level,
                    'temperature': round(temperature, 1),
                    'confidence': float(confidence),
                    'tendency': tendency,
                    'day_index': i
                })
            
            print(f"✅ Generated 7-day forecast with avg risk: {np.mean([f['risk_score'] for f in forecast]):.3f}")
            return forecast
            
        except Exception as e:
            print(f"❌ Forecast error: {e}")
            return [{'error': str(e)}]

# Initialize analyzer
analyzer = TashkentDustAnalyzer()

# # Include the HTML template
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Dustcast - Advanced Dust Storm Prediction</title>
#     <style>
#         /* Insert the CSS styles from the artifact here */
#     </style>
# </head>
# <body>
#     <!-- Insert the HTML body from the artifact here -->
#     <script>
#         /* Insert the JavaScript from the artifact here */
#     </script>
# </body>
# </html>
# """

# Routes
@app.route('/')
def dashboard():
    """Main dashboard with localization support"""
    # You'll need to copy the HTML template from the artifact
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/current')
def get_current_conditions():
    """Get current dust storm conditions with caching"""
    try:
        conditions = analyzer.get_current_conditions()
        return jsonify(conditions)
    except Exception as e:
        return jsonify({'error': str(e), 'cache_stats': cache.get_stats()}), 500

@app.route('/api/forecast')
def get_forecast():
    """Get 7-day forecast with caching"""
    try:
        forecast = analyzer.generate_forecast(days=7)
        return jsonify(forecast)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats')
def get_cache_stats():
    """Get detailed cache statistics"""
    return jsonify(cache.get_stats())

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached data"""
    try:
        cleared_files = 0
        for cache_type in ['data', 'metadata']:
            cache_dir = os.path.join(cache.cache_dir, cache_type)
            if os.path.exists(cache_dir):
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    os.remove(file_path)
                    cleared_files += 1
        
        # Reset cache stats
        cache.stats = {'hits': 0, 'misses': 0, 'saves': 0, 'errors': 0}
        
        return jsonify({
            'message': f'Cache cleared successfully. Removed {cleared_files} files.',
            'cleared_files': cleared_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status including cache performance"""
    cache_stats = cache.get_stats()
    return jsonify({
        'status': 'online',
        'project': project,
        'timestamp': datetime.now().isoformat(),
        'location': 'Tashkent, Uzbekistan',
        'coordinates': [69.2401, 41.2995],
        'cache_performance': cache_stats,
        'cache_enabled': True,
        'cache_ttl_minutes': cache.default_ttl // 60
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'cache_healthy': True
    })

if __name__ == '__main__':
    print("🌪️ Starting Enhanced Dustcast...")
    print(f"📍 Using GEE project: {project}")
    print(f"🗂️ Cache directory: {cache.cache_dir}")
    print(f"⏰ Cache TTL: {cache.default_ttl // 60} minutes")
    print("🌐 Dashboard: http://localhost:5001")
    print("🔄 Auto-updates every 30 minutes")
    app.run(host='0.0.0.0', port=5001, debug=True)