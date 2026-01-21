# Installing Docker for Quick Start

Docker is required to run the AdCP Sales Agent. Here's how to install it on macOS:

## Option 1: Docker Desktop (Recommended)

1. **Download Docker Desktop**:
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download Docker Desktop for Mac (Apple Silicon or Intel)

2. **Install**:
   - Open the downloaded `.dmg` file
   - Drag Docker to Applications folder
   - Launch Docker Desktop from Applications

3. **Verify Installation**:
   ```bash
   docker --version
   docker compose version
   ```

4. **Start Docker Desktop**:
   - Make sure Docker Desktop is running (check the menu bar for the Docker icon)
   - Wait for it to fully start (the icon should be steady, not animating)

## Option 2: Homebrew

```bash
brew install --cask docker
```

Then launch Docker Desktop from Applications.

## After Installation

Once Docker is installed and running, you can start the Quick Start:

```bash
cd salesagent
./quickstart.sh
```

Or manually:

```bash
cd salesagent
docker compose up -d
```

## Troubleshooting

- **Docker not found**: Make sure Docker Desktop is running
- **Permission denied**: You may need to add your user to the docker group or restart your terminal
- **Port conflicts**: If port 8000 is in use, set `CONDUCTOR_PORT=8001` before running docker compose
