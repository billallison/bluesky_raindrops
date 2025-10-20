# Docker Container Setup - Implementation Summary

## Files Created

This document summarizes the Docker containerization implementation for the Raindrop to Bluesky Bot.

### Core Docker Files

1. **`Dockerfile`**
   - Multi-stage Python 3.11 slim base image
   - Installs cron and Python dependencies
   - Creates non-root user (appuser) for security
   - Sets up health checks
   - Final image size: ~150-200MB

2. **`docker-compose.yml`**
   - Service definition for easy deployment
   - Volume mounts for .env and logs
   - Restart policy: unless-stopped
   - Configurable cron schedule via environment variable
   - Logging configuration (max 10MB, 3 files)

3. **`entrypoint.sh`**
   - Container initialization script
   - Sets up cron job for appuser
   - Runs initial execution on startup
   - Starts cron daemon in foreground
   - Ensures proper file permissions

4. **`.dockerignore`**
   - Excludes unnecessary files from build context
   - Reduces build time and image size
   - Excludes .git, docs, venv, logs, etc.

### Configuration Files

5. **`.env.example`**
   - Template for environment variables
   - Documented configuration options
   - Safe to commit (no secrets)

6. **`.gitignore`** (updated)
   - Enhanced with Docker-related ignores
   - Ensures .env is never committed
   - Excludes build artifacts and caches

### Documentation

7. **`README.md`** (updated)
   - Added comprehensive Docker deployment section
   - Docker vs manual installation options
   - Management commands and troubleshooting
   - Security and monitoring guidance

8. **`DOCKER_QUICKSTART.md`**
   - Step-by-step deployment guide
   - Common issues and solutions
   - Migration and backup instructions
   - Customization options

9. **`Makefile`**
   - Convenient shortcuts for Docker commands
   - 15+ common operations
   - Help documentation built-in

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│  ┌───────────────────────────────────┐  │
│  │   Cron Daemon (root)              │  │
│  │   - Runs every 10 minutes         │  │
│  │   - Executes run_script.sh        │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │   run_script.sh (appuser)        │  │
│  │   - Loads .env variables          │  │
│  │   - Calls Python script           │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │   raindrop_to_bluesky.py         │  │
│  │   - Fetches from Raindrop.io     │  │
│  │   - Posts to Bluesky             │  │
│  │   - Sends email alerts           │  │
│  └───────────────────────────────────┘  │
│                                          │
│  Volumes:                                │
│  - .env (read-only)                      │
│  - ./logs (read-write)                   │
└─────────────────────────────────────────┘
```

## Security Features

- **Non-root execution**: Python script runs as appuser (UID 1000)
- **Read-only .env mount**: Prevents accidental modification
- **No exposed ports**: Outbound connections only
- **Isolated environment**: Container has minimal attack surface
- **Health checks**: Monitors log file creation
- **App passwords recommended**: For Bluesky and SMTP

## Deployment Options

### Option A: Local Build (Implemented)
```bash
cd bluesky_raindrops
docker-compose up -d
```

Benefits:
- No external dependencies
- Fast iteration during development
- Complete control over build process

### Option B: GitHub Container Registry (Future)
Could be added with GitHub Actions workflow to:
- Auto-build on push to main
- Push to ghcr.io/billallison/bluesky_raindrops
- Version tagging (latest, v1.0.0, etc.)

## Configuration

### Environment Variables (in .env)
```
RAINDROP_TOKEN          - Raindrop.io API token
BLUESKY_IDENTIFIER      - Bluesky handle
BLUESKY_PASSWORD        - Bluesky app password
ADMIN_EMAIL             - Email for alerts
SMTP_SERVER             - SMTP server hostname
SMTP_PORT               - SMTP port (usually 465 or 587)
SMTP_LOGIN              - SMTP username
SMTP_PASSWORD           - SMTP password
LOG_LEVEL               - Logging verbosity
```

### Docker Compose Variables
```
CRON_SCHEDULE           - Cron expression (default: */10 * * * *)
TZ                      - Timezone (default: America/New_York)
```

## Volume Mounts

1. **`.env` → `/app/.env`** (read-only)
   - Contains secrets and configuration
   - Never committed to Git
   - Mounted as read-only for security

2. **`./logs` → `/app/logs`** (read-write)
   - Persists application logs
   - Accessible from host for monitoring
   - Survives container restarts

## Testing & Verification

### Manual Testing
```bash
# Test immediate execution
make test

# View logs
make logs-live

# Check cron schedule
make cron
```

### Automated Checks
```bash
# Container health
docker-compose ps

# Log verification
tail logs/bluesky_raindrops.log

# Cron execution log
docker-compose exec bluesky-raindrops-bot cat /app/logs/cron.log
```

## Resource Usage

- **CPU**: Minimal (spikes during execution, idle otherwise)
- **Memory**: ~100-150MB
- **Disk**: 
  - Image: ~150-200MB
  - Logs: Grows over time (configure log rotation if needed)
- **Network**: Outbound only to:
  - api.raindrop.io
  - bsky.social (Bluesky API)
  - Your SMTP server
  - Image CDNs

## Maintenance

### Updates
```bash
git pull
docker-compose up -d --build
```

### Logs Management
```bash
# View recent logs
make logs

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Backup
```bash
# Backup configuration
cp .env .env.backup

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Troubleshooting

See `DOCKER_QUICKSTART.md` for detailed troubleshooting steps.

Quick checks:
1. Container running? `docker-compose ps`
2. Logs clean? `docker-compose logs`
3. .env correct? `cat .env` (be careful with secrets!)
4. Cron working? `make cron`
5. Test execution? `make test`

## Next Steps (Optional Enhancements)

1. **GitHub Actions CI/CD**
   - Auto-build on push
   - Push to GHCR
   - Automated testing

2. **Monitoring Integration**
   - Prometheus metrics
   - Grafana dashboard
   - Uptime monitoring

3. **Log Rotation**
   - Automated log cleanup
   - Log shipping to central system

4. **Multi-architecture Support**
   - ARM64 builds for Raspberry Pi
   - AMD64 for servers

5. **Health Endpoint**
   - HTTP health check endpoint
   - Integration with monitoring systems

## Support

For issues or questions:
- GitHub Issues: https://github.com/billallison/bluesky_raindrops/issues
- Documentation: README.md, DOCKER_QUICKSTART.md
- Logs: `make logs-live`
