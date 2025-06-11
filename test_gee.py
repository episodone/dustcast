#!/usr/bin/env python3
"""
Quick GEE test with project parameter
"""

import ee

def test_gee_with_project():
    """Test GEE with different project options"""
    projects_to_try = [
        'earthengine-legacy',
        'youtubecommentsapp', 
        None  # Try without project as fallback
    ]
    
    for project in projects_to_try:
        try:
            if project:
                ee.Initialize(project=project)
                print(f"✅ GEE initialized successfully with project: {project}")
            else:
                ee.Initialize()
                print("✅ GEE initialized successfully without project")
            
            # Test basic operations
            point = ee.Geometry.Point([69.2401, 41.2995])
            print("✅ Basic GEE operations working")
            
            # Test data access
            collection = ee.ImageCollection('MODIS/061/MOD11A1') \
                .filterBounds(point) \
                .filterDate('2024-01-01', '2024-12-31')
            
            size = collection.size().getInfo()
            print(f"✅ MODIS LST collection access: {size} images")
            
            return project
            
        except Exception as e:
            print(f"❌ Failed with project '{project}': {e}")
            continue
    
    return None

if __name__ == "__main__":
    working_project = test_gee_with_project()
    if working_project:
        print(f"\n🎉 Use this project: {working_project}")
        print(f"💡 Add to .env file: GOOGLE_CLOUD_PROJECT={working_project}")
    else:
        print("\n❌ No working project found")
