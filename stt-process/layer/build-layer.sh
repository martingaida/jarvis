#!/bin/bash
set -eo pipefail

# Create a temporary directory for the layer
LAYER_DIR="python"

# Ensure the layer directory exists and is empty
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"

# Install packages into the layer directory
pip install -r requirements.txt -t "$LAYER_DIR"

# Remove unnecessary files to reduce layer size
find "$LAYER_DIR" -type d -name "tests" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "*.dist-info" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "*.egg-info" -exec rm -rf {} +

# Create the zip file
zip -r9 python.zip "$LAYER_DIR"

# Clean up
# rm -rf "$LAYER_DIR"

echo "Layer created at $(pwd)/python.zip"
echo "Contents of current directory after build:"