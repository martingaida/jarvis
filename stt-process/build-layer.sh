#!/bin/bash
set -eo pipefail

# Create layer directory if it doesn't exist
if [ ! -d "layer/python" ]; then
    echo "Creating layer/python directory..."
    mkdir -p layer/python
else
    echo "layer/python directory found."
fi

# Install packages into the layer directory
pip install -r requirements.txt -t layer/python

# Remove unnecessary files to reduce layer size
find layer/python -type d -name "tests" -exec rm -rf {} +
rm -rf layer/python/*.dist-info
rm -rf layer/python/*.egg-info