#!/bin/bash

# CSV Data Loading Script - Safe Mode
# Updates existing data without clearing anything

echo "CSV Data Loading Script (Safe Mode)"
echo "==================================="
echo ""
echo "DATABASE CONFIGURATION:"
echo "Set your DATABASE_URL using one of these methods:"
echo "1. Environment variable: export DATABASE_URL='postgresql://user:pass@host:port/db'"
echo "2. Create .env file: echo 'DATABASE_URL=postgresql://user:pass@host:port/db' > .env"
echo "3. Update app/core/config.py (not recommended for production)"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if required files exist
if [ ! -f "churches_with_denominations.csv" ] || [ ! -f "speakers.csv" ]; then
    echo "Error: Required CSV files not found"
    echo "Need: churches_with_denominations.csv and speakers.csv"
    exit 1
fi

# Run validation first
echo "Validating CSV files..."
python3 test_data_loading.py
if [ $? -ne 0 ]; then
    echo "Validation failed. Please fix the issues before proceeding."
    exit 1
fi

echo ""
echo "Loading data into database (safe mode - updates existing data)..."

# Load the data
python3 load_csv_data.py
if [ $? -eq 0 ]; then
    echo "✅ Data loading completed successfully!"
else
    echo "❌ Data loading failed."
    exit 1
fi
