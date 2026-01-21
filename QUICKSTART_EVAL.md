# Quick Start (Evaluation) - Implementation Guide

This document provides step-by-step instructions for the Quick Start (Evaluation) process.

## Prerequisites

- Docker and Docker Compose installed
- `uvx` command available (install with `pip install uv` or `pipx install uv`)

## Automated Setup

Run the provided script:

```bash
./quickstart.sh
```

This script will:
1. Check for Docker and Docker Compose
2. Start all services with `docker compose up -d`
3. Wait for services to be ready
4. Test the MCP interface with sample commands

## Manual Setup

If you prefer to run the steps manually:

### Step 1: Start Services

```bash
cd salesagent
docker compose up -d
```

This starts:
- PostgreSQL database
- AdCP Server (MCP/A2A endpoints)
- Admin UI
- Nginx proxy

### Step 2: Wait for Services

Wait a few moments for all services to start. Check health:

```bash
curl http://localhost:8000/health
```

### Step 3: Test MCP Interface

Test the MCP interface with the provided commands:

```bash
# List available tools
uvx adcp http://localhost:8000/mcp/ --auth test-token list_tools

# Get products matching a brief
uvx adcp http://localhost:8000/mcp/ --auth test-token get_products '{"brief":"video"}'
```

## Access Points

Once running, access services at http://localhost:8000:

- **Admin UI**: `/admin` or just click "Log in to Dashboard"
  - Test credentials: `test123`
- **MCP Server**: `/mcp/`
- **A2A Server**: `/a2a`

## Troubleshooting

### Services won't start

Check logs:
```bash
docker compose logs
```

### Port already in use

Change the port by setting `CONDUCTOR_PORT` environment variable:
```bash
CONDUCTOR_PORT=8001 docker compose up -d
```

### MCP tests fail

Services may still be starting. Wait a bit longer and try again:
```bash
sleep 10
uvx adcp http://localhost:8000/mcp/ --auth test-token list_tools
```

## Stopping Services

To stop all services:
```bash
docker compose down
```

To stop and remove volumes (clean slate):
```bash
docker compose down -v
```

## Next Steps

After successful Quick Start:
- Explore the Admin UI at http://localhost:8000/admin
- Review the [Development Guide](docs/development/README.md) for local development
- Check the [Deployment Guide](docs/quickstart.md) for production deployment
