#!/bin/bash
# Local Development Setup (without Docker)
# This script sets up PostgreSQL and prepares the environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Setting up local development environment..."
echo ""

# Add PostgreSQL to PATH
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

# Start PostgreSQL if not running
if ! pg_isready -h localhost > /dev/null 2>&1; then
    echo "📦 Starting PostgreSQL..."
    brew services start postgresql@17
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
    
    # Wait for PostgreSQL to be ready
    MAX_ATTEMPTS=10
    ATTEMPT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if pg_isready -h localhost > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            break
        fi
        ATTEMPT=$((ATTEMPT + 1))
        echo "   Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
        sleep 2
    done
else
    echo "✅ PostgreSQL is already running"
fi

# Create database and user if they don't exist
echo ""
echo "🗄️  Setting up database..."

# Try to create user (will fail if exists, that's OK)
psql -h localhost -U "$USER" -d postgres -c "CREATE USER adcp_user WITH PASSWORD 'secure_password_change_me';" 2>/dev/null || echo "User may already exist"

# Create database
psql -h localhost -U "$USER" -d postgres -c "CREATE DATABASE adcp OWNER adcp_user;" 2>/dev/null || echo "Database may already exist"

# Grant privileges
psql -h localhost -U "$USER" -d adcp -c "GRANT ALL PRIVILEGES ON DATABASE adcp TO adcp_user;" 2>/dev/null || true

echo "✅ Database setup complete"
echo ""

# Set up environment variables
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://adcp_user:secure_password_change_me@localhost:5432/adcp?sslmode=disable

# Server Configuration
ADCP_SALES_PORT=8080
ADCP_SALES_HOST=0.0.0.0

# Admin UI Configuration  
FLASK_ENV=development
FLASK_DEBUG=1

# Development settings
PYTHONPATH=/Users/mehdi.lamrani/code/tf1-agent/salesagent/.venv/lib/python3.12/site-packages
PYTHONUNBUFFERED=1

# Skip services not needed for local dev
SKIP_NGINX=true
SKIP_CRON=true
EOF
    echo "✅ Created .env file"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "✅ Local setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run migrations: uv run python scripts/ops/migrate.py"
echo "  2. Start the server: uv run python scripts/run_server.py"
echo "  3. Start admin UI (in another terminal): uv run python -m src.admin.server"
