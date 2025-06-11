#!/bin/bash

echo "🚀 Starting Tashkent Dust Storm Predictor..."

# Check if we're in the right directory
if [[ ! -d "dust_predictor_env" ]]; then
    echo "❌ Error: dust_predictor_env not found. Run this script from the project directory."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source dust_predictor_env/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version)
echo "🐍 Using: $PYTHON_VERSION"

# Check if Earth Engine is authenticated
echo "🌍 Checking Earth Engine authentication..."
python -c "import ee; ee.Initialize()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "🔐 Earth Engine authentication required..."
    echo ""
    echo "Choose authentication method:"
    echo "1. Interactive authentication (recommended for development)"
    echo "2. Service account (recommended for production)"
    echo ""
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1)
            echo "🔓 Starting interactive authentication..."
            python -c "import ee; ee.Authenticate()"
            python -c "import ee; ee.Initialize()"
            ;;
        2)
            echo "🔑 For service account authentication:"
            echo "1. Download your service account key from Google Cloud Console"
            echo "2. Set GOOGLE_APPLICATION_CREDENTIALS in .env file"
            echo "3. Restart this script"
            exit 1
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

echo "✅ Earth Engine authenticated successfully"

# Check if required files exist
if [[ ! -f "app.py" ]]; then
    echo "❌ Error: app.py not found. Please ensure all files are in place."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export FLASK_ENV=development
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Start the Flask application
echo "🌐 Starting web server..."
echo "📱 Dashboard will be available at: http://localhost:5000"
echo "🔄 Press Ctrl+C to stop the server"
echo ""

# Run with error handling
python app.py || {
    echo ""
    echo "❌ Application failed to start. Check the error messages above."
    echo "💡 Try running: python test_setup.py"
    exit 1
}
