# Docker Quick Start Guide

This guide will help you deploy the Raindrop to Bluesky Bot using Docker on your home server.

## Quick Deployment (5 minutes)

### Step 1: Prerequisites

Make sure you have Docker and Docker Compose installed:

```bash
# Check if Docker is installed
docker --version

# Check if Docker Compose is installed
docker-compose --version
```

If not installed, visit: https://docs.docker.com/get-docker/

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/billallison/bluesky_raindrops.git
cd bluesky_raindrops

# Create your environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

### Step 3: Configure Your Credentials

Edit `.env` and fill in these values:

```env
# Get from: https://app.raindrop.io/settings/integrations
RAINDROP_TOKEN=your_token_here

# Your Bluesky handle (e.g., yourname.bsky.social)
BLUESKY_IDENTIFIER=your.handle.bsky.social

# Create an app password at: https://bsky.app/settings/app-passwords
BLUESKY_PASSWORD=your_app_password_here

# Your email for error notifications
ADMIN_EMAIL=you@example.com

# SMTP settings (example for Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_LOGIN=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Logging level
LOG_LEVEL=WARNING
```

### Step 4: Deploy

```bash
# Build and start the container
docker-compose up -d

# Watch the logs to verify it's working
docker-compose logs -f
```

That's it! The bot is now running and will check for new Raindrops every 10 minutes.

## Using the Makefile (Optional)

For convenience, you can use the included Makefile:

```bash
# Deploy everything
make deploy

# View logs
make logs-live

# Test immediately
make test

# See all available commands
make help
```

## Verification Checklist

After deployment, verify:

- ✅ Container is running: `docker-compose ps`
- ✅ Logs show no errors: `docker-compose logs`
- ✅ Cron schedule is correct: `make cron` or `docker-compose exec bluesky-raindrops-bot crontab -l`
- ✅ Test execution works: `make test`

## Common Issues

### Container won't start

**Check logs:**
```bash
docker-compose logs
```

**Common causes:**
- Missing `.env` file
- Invalid credentials in `.env`
- Port conflicts (unlikely - this container doesn't expose ports)

### Not posting to Bluesky

**Test manually:**
```bash
make test
# Or
docker-compose exec bluesky-raindrops-bot python /app/raindrop_to_bluesky.py
```

**Check:**
- Raindrop has items tagged with "toskeet"
- Bluesky credentials are correct (try logging in to app)
- API tokens haven't expired

### Email notifications not working

**Check SMTP settings in `.env`:**
- For Gmail, you need an "App Password" (not your regular password)
- Enable "Less secure app access" if required by your provider
- Verify SMTP server and port are correct

## Updating the Bot

When you pull new code from GitHub:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Or using Makefile
make rebuild
```

## Customizing the Schedule

Default is every 10 minutes. To change, edit `docker-compose.yml`:

```yaml
environment:
  - CRON_SCHEDULE=*/10 * * * *  # Current: every 10 minutes
```

Examples:
- Every 5 minutes: `*/5 * * * *`
- Every hour: `0 * * * *`
- Every 2 hours: `0 */2 * * *`
- Every day at 9 AM: `0 9 * * *`

After changing, restart:
```bash
docker-compose up -d
```

## Stopping the Bot

```bash
# Stop but keep container
docker-compose stop

# Stop and remove container
docker-compose down

# Stop and remove everything including images
make clean
```

## Backup and Migration

### Backup your configuration

```bash
# Backup .env file (contains secrets!)
cp .env .env.backup

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Migrate to new server

```bash
# On new server:
git clone https://github.com/billallison/bluesky_raindrops.git
cd bluesky_raindrops

# Copy your .env file from old server
scp old-server:/path/to/.env .

# Deploy
make deploy
```

## Monitoring

### View live logs
```bash
make logs-live
```

### Check last execution
```bash
tail logs/bluesky_raindrops.log
```

### Check cron execution log
```bash
docker-compose exec bluesky-raindrops-bot cat /app/logs/cron.log
```

## Support

If you encounter issues:

1. Check the logs: `make logs-live`
2. Test manual execution: `make test`
3. Verify .env configuration
4. Check GitHub issues: https://github.com/billallison/bluesky_raindrops/issues

## Timezone Configuration

Default is `America/New_York`. To change, edit `docker-compose.yml`:

```yaml
environment:
  - TZ=America/Los_Angeles  # Your timezone
```

Find your timezone: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
