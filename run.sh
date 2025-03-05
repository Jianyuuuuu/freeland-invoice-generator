#!/bin/bash

# Activate conda environment
source ~/miniconda3/bin/activate invoice-env

# Kill any existing Flask processes
pkill -f "python app.py" || true

# Run Flask application
echo "Starting Invoice Generator on http://localhost:5002"
python app.py 