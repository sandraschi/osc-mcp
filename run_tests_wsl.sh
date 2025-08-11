#!/bin/bash

# Exit on error
set -e

# Change to the project directory (mounted at /mnt/d/Dev/repos/oscmcp in WSL)
cd /mnt/d/Dev/repos/oscmcp

# Create and activate a virtual environment
echo "Creating and activating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .[test]

# Install test dependencies
pip install pytest pytest-asyncio python-osc

# Run the tests
echo "Running tests..."
python -m pytest tests/ -v

# Deactivate virtual environment
deactivate

echo "Tests completed successfully!"
