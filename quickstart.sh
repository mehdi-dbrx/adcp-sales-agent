#!/bin/bash
# Quick Start (Evaluation) Script
# This script implements the Quick Start steps from the README

set -e

echo "🚀 AdCP Sales Agent - Quick Start (Evaluation)"
echo "=============================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    echo "Please install Docker Desktop or Docker Engine to continue."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not available"
    echo "Please ensure Docker Compose is installed (comes with Docker Desktop)."
    exit 1
fi

# Navigate to the salesagent directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Starting Docker Compose services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Wait for services to be healthy
echo "Checking service health..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:8000/health &> /dev/null 2>&1; then
        echo "✅ Services are ready!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "⚠️  Warning: Services may not be fully ready yet"
    echo "   You can check logs with: docker compose logs"
fi

echo ""
echo "🎯 Testing MCP interface..."
echo ""

# Check if uvx is available
if ! command -v uvx &> /dev/null; then
    echo "⚠️  Warning: uvx is not installed"
    echo "   Install it with: pip install uv"
    echo "   Or use: pipx install uv"
    echo ""
    echo "   Once installed, you can test manually with:"
    echo "   uvx adcp http://localhost:8000/mcp/ --auth test-token list_tools"
    echo "   uvx adcp http://localhost:8000/mcp/ --auth test-token get_products '{\"brief\":\"video\"}'"
else
    echo "Testing list_tools..."
    uvx adcp http://localhost:8000/mcp/ --auth test-token list_tools || {
        echo "⚠️  MCP test failed - services may still be starting"
        echo "   Try again in a few moments"
    }
    
    echo ""
    echo "Testing get_products..."
    uvx adcp http://localhost:8000/mcp/ --auth test-token get_products '{"brief":"video"}' || {
        echo "⚠️  MCP test failed - services may still be starting"
        echo "   Try again in a few moments"
    }
fi

echo ""
echo "✅ Quick Start Complete!"
echo ""
echo "Access services at http://localhost:8000:"
echo "  • Admin UI: http://localhost:8000/admin (test credentials: test123)"
echo "  • MCP Server: http://localhost:8000/mcp/"
echo "  • A2A Server: http://localhost:8000/a2a"
echo ""
echo "To stop services: docker compose down"
echo "To view logs: docker compose logs -f"
