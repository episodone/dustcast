#!/bin/bash

# macOS Application Launcher
# This script can be used to create a macOS app bundle

echo "🍎 Launching Tashkent Dust Storm Predictor..."

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Set macOS specific environment
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Launch the application
./run.sh

# Keep terminal open if launched from Finder
read -p "Press Enter to close..."
