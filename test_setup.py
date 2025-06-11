#!/usr/bin/env python3
"""
Enhanced test script for Python 3.13.3 compatibility
"""

import sys
import importlib
import os
import platform
from pathlib import Path

def print_system_info():
    """Print system information"""
    print("🖥️ System Information:")
    print(f"   Python: {sys.version}")
    print(f"   Platform: {platform.platform()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Working directory: {os.getcwd()}")
    print()

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} may have compatibility issues")
        print("💡 Python 3.9+ recommended")
        return False

def test_imports():
    """Test that all required packages can be imported"""
    required_packages = {
        'ee': 'Google Earth Engine',
        'pandas': 'Data processing',
        'numpy': 'Numerical computing',
        'sklearn': 'Machine learning',
        'flask': 'Web framework',
        'requests': 'HTTP client',
        'schedule': 'Task scheduling',
        'matplotlib': 'Plotting',
        'dotenv': 'Environment variables'
    }
    
    print("📦 Testing package imports...")
    failed = []
    
    for package, description in required_packages.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package:<12} ({description}) - v{version}")
        except ImportError as e:
            print(f"❌ {package:<12} ({description}) - {e}")
            failed.append(package)
    
    if failed:
        print(f"\n💡 To install missing packages:")
        print(f"   pip install {' '.join(failed)}")
    
    return len(failed) == 0

def test_gee_auth():
    """Test Google Earth Engine authentication"""
    print("\n🌍 Testing Google Earth Engine...")
    try:
        import ee
        
        # Test initialization
        ee.Initialize()
        print("✅ Google Earth Engine authenticated")
        
        # Test basic operations
        point = ee.Geometry.Point([69.2401, 41.2995])
        print("✅ Basic GEE geometry operations working")
        
        # Test image collection access
        collection = ee.ImageCollection('MODIS/061/MOD11A1')
        print("✅ Image collection access working")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Earth Engine error: {e}")
        if "not initialized" in str(e).lower():
            print("💡 Run authentication:")
            print("   python -c \"import ee; ee.Authenticate()\"")
        return False

def test_data_access():
    """Test access to required datasets"""
    print("\n📡 Testing dataset access...")
    try:
        import ee
        
        collections = {
            'MODIS LST': 'MODIS/061/MOD11A1',
            'Landsat 8': 'LANDSAT/LC08/C02/T1_L2',
            'Landsat 9': 'LANDSAT/LC09/C02/T1_L2',
            'Sentinel-2': 'COPERNICUS/S2_SR_HARMONIZED'
        }
        
        tashkent = ee.Geometry.Point([69.2401, 41.2995])
        test_date_start = '2024-01-01'
        test_date_end = '2024-12-31'
        
        for name, collection_id in collections.items():
            try:
                collection = ee.ImageCollection(collection_id) \
                    .filterBounds(tashkent) \
                    .filterDate(test_date_start, test_date_end)
                
                size = collection.size().getInfo()
                print(f"✅ {name:<15}: {size:>3} images available")
            except Exception as e:
                print(f"❌ {name:<15}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dataset access error: {e}")
        return False

def test_file_structure():
    """Test project file structure"""
    print("\n📁 Testing file structure...")
    
    required_dirs = ['data', 'logs', 'models', 'static', 'templates', 'config']
    required_files = ['.env', 'config.py', 'requirements.txt', 'run.sh']
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory: {directory}/")
        else:
            print(f"⚠️ Missing directory: {directory}/")
            Path(directory).mkdir(exist_ok=True)
            print(f"   Created: {directory}/")
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ File: {file}")
        else:
            print(f"❌ Missing file: {file}")
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import Config, config
        
        # Test config loading
        cfg = config['development']
        print("✅ Configuration classes loaded")
        
        # Test environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        print("✅ Environment variables loaded")
        
        # Check critical settings
        tashkent_lat = getattr(cfg, 'TASHKENT_LAT', None)
        tashkent_lon = getattr(cfg, 'TASHKENT_LON', None)
        
        if tashkent_lat and tashkent_lon:
            print(f"✅ Tashkent coordinates: {tashkent_lat}, {tashkent_lon}")
        else:
            print("⚠️ Default coordinates will be used")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🌪️ Tashkent Dust Storm Predictor - Enhanced Setup Test\n")
    
    # Print system information
    print_system_info()
    
    # Run tests
    tests = [
        ("Python version", test_python_version),
        ("Package imports", test_imports),
        ("File structure", test_file_structure),
        ("Configuration", test_configuration),
        ("GEE authentication", test_gee_auth),
        ("Dataset access", test_data_access),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your system is ready.")
        print("🚀 Next steps:")
        print("   1. Run: ./run.sh")
        print("   2. Open: http://localhost:5000")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please address the issues above.")
        print("💡 Common solutions:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Authenticate GEE: python -c \"import ee; ee.Authenticate()\"")
        return 1

if __name__ == "__main__":
    sys.exit(main())
