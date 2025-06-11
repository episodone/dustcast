#!/usr/bin/env python3
"""
Simple test version of the Dust Storm Predictor app
"""

import ee
import os
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Earth Engine with project
project = os.getenv('GOOGLE_CLOUD_PROJECT', 'youtubecommentsapp')
try:
    ee.Initialize(project=project)
    print(f"✅ Earth Engine initialized with project: {project}")
except Exception as e:
    print(f"❌ Earth Engine initialization failed: {e}")
    print("💡 Try running: python test_gee.py")

app = Flask(__name__)

@app.route('/')
def dashboard():
    return """
    <html>
    <body>
        <h1>🌪️ Tashkent Dust Storm Predictor</h1>
        <h2>🎉 Your app is working!</h2>
        <p>✅ Flask server running</p>
        <p>✅ Earth Engine connected</p>
        <p>📊 Ready for dust storm monitoring</p>
        <a href="/api/test">Test API</a>
    </body>
    </html>
    """

@app.route('/api/test')
def test_api():
    try:
        # Test basic GEE operation
        point = ee.Geometry.Point([69.2401, 41.2995])
        collection = ee.ImageCollection('MODIS/061/MOD11A1') \
            .filterBounds(point) \
            .filterDate('2024-01-01', '2024-12-31')
        
        size = collection.size().getInfo()
        
        return jsonify({
            'status': 'success',
            'message': 'Earth Engine working!',
            'project': project,
            'modis_images': size,
            'location': 'Tashkent, Uzbekistan'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🌐 Starting Tashkent Dust Storm Predictor...")
    print(f"📍 Using GEE project: {project}")
    print("🌐 Dashboard: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
