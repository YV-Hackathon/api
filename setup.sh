#!/bin/bash

echo "🚀 Setting up FastAPI CMS..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp env.example .env
    echo "📝 Please edit .env file with your database credentials"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Create a PostgreSQL database"
echo "3. Run: python seed_data.py"
echo "4. Run: python run.py"
echo ""
echo "The API will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
