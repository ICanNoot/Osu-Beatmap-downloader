#!/bin/bash
# Build script for Linux/macOS
# Creates a standalone executable for osu! Beatmap Downloader

set -e

echo "============================================"
echo "  osu! Beatmap Downloader - Build Script"
echo "============================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ using your package manager"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Build the executable
echo
echo "Building executable..."
echo "This may take a few minutes..."
echo
pyinstaller osu_downloader.spec --clean

# Determine output filename based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OUTPUT_FILE="dist/OsuBeatmapDownloader"
    OUTPUT_NAME="OsuBeatmapDownloader (macOS)"
else
    OUTPUT_FILE="dist/OsuBeatmapDownloader"
    OUTPUT_NAME="OsuBeatmapDownloader (Linux)"
fi

# Check if build was successful
if [ -f "$OUTPUT_FILE" ]; then
    echo
    echo "============================================"
    echo "  BUILD SUCCESSFUL!"
    echo "============================================"
    echo
    echo "Executable created at: $OUTPUT_FILE"
    echo
    echo "You can now distribute this file to users."
    echo "They can run it without installing Python!"

    # Make it executable
    chmod +x "$OUTPUT_FILE"
else
    echo
    echo "============================================"
    echo "  BUILD FAILED"
    echo "============================================"
    echo
    echo "Check the output above for errors."
    exit 1
fi

# Deactivate virtual environment
deactivate

echo
echo "Done!"
