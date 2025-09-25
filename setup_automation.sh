#!/bin/bash
# Setup script for ODCV Automated Pipeline

echo "🏢 ODCV Automated Pipeline Setup"
echo "================================="

# Check Python version
python3 --version || {
    echo "❌ Python 3 is required but not found"
    exit 1
}

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements_automation.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

echo "✅ Dependencies installed"

# Create environment configuration template
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration template..."
    cat > .env << 'EOF'
# Database Configuration
# Required for automated pipeline
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_TYPE=postgresql

# Optional: Web server configuration
PORT=5000
DEBUG=false
EOF
    echo "✅ Created .env template - please configure your database settings"
else
    echo "⚠️  .env file already exists"
fi

# Make scripts executable
chmod +x automated_pipeline.py
chmod +x web_server.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your database settings in .env file"
echo "2. Test the command line interface:"
echo "   python3 automated_pipeline.py your_view_name"
echo ""
echo "3. Or start the web interface:"
echo "   python3 web_server.py"
echo "   Then open: http://localhost:5000"
echo ""
echo "Environment variables to set:"
echo "  DB_HOST     - Your database server hostname"
echo "  DB_NAME     - Database name containing sensor data"
echo "  DB_USER     - Database username"
echo "  DB_PASSWORD - Database password"
echo "  DB_PORT     - Database port (default: 5432)"
echo "  DB_TYPE     - Database type (default: postgresql)"