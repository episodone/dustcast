"""
Configuration settings for Tashkent Dust Storm Predictor
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dust-storm-predictor-2025'
    
    # Earth Engine
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # OpenWeatherMap
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    
    # Flask settings
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Tashkent coordinates
    TASHKENT_LAT = float(os.environ.get('TASHKENT_LAT', 41.2995))
    TASHKENT_LON = float(os.environ.get('TASHKENT_LON', 69.2401))
    
    # Thresholds
    DUST_RISK_HIGH_THRESHOLD = float(os.environ.get('DUST_RISK_HIGH_THRESHOLD', 0.6))
    DUST_RISK_MODERATE_THRESHOLD = float(os.environ.get('DUST_RISK_MODERATE_THRESHOLD', 0.3))
    TEMPERATURE_HIGH_THRESHOLD = float(os.environ.get('TEMPERATURE_HIGH_THRESHOLD', 35))
    NDDI_ELEVATED_THRESHOLD = float(os.environ.get('NDDI_ELEVATED_THRESHOLD', 0.15))
    
    # Update intervals
    DATA_UPDATE_INTERVAL = int(os.environ.get('DATA_UPDATE_INTERVAL', 30))
    FORECAST_UPDATE_INTERVAL = int(os.environ.get('FORECAST_UPDATE_INTERVAL', 360))
    
    # Cache settings
    ENABLE_CACHE = os.environ.get('ENABLE_CACHE', 'True').lower() == 'true'
    CACHE_TTL_MINUTES = int(os.environ.get('CACHE_TTL_MINUTES', 30))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Google Earth Engine Project
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', 'youtubecommentsapp')
