# Pre-Deployment Checklist

Use this checklist before deploying the containerized bot on your new home server.

## ✅ Repository Setup

- [ ] All files committed to Git
- [ ] `.env` is in `.gitignore` (should NOT be committed)
- [ ] `.env.example` is committed (safe template without secrets)
- [ ] Pushed to GitHub repository

## ✅ Server Prerequisites

- [ ] Docker installed and running
  ```bash
  docker --version
  docker info
  ```

- [ ] Docker Compose installed
  ```bash
  docker-compose --version
  ```

- [ ] User has Docker permissions
  ```bash
  docker ps
  # Should not require sudo
  ```

## ✅ Credentials Ready

- [ ] **Raindrop.io API Token**
  - Get from: https://app.raindrop.io/settings/integrations
  - Create new token if needed
  - Copy token value

- [ ] **Bluesky Credentials**
  - Your handle (e.g., yourname.bsky.social)
  - App password from: https://bsky.app/settings/app-passwords
  - DO NOT use your main password

- [ ] **SMTP Email Settings**
  - SMTP server address
  - SMTP port (465 for SSL, 587 for TLS)
  - SMTP username/login
  - SMTP password (app password if Gmail)

## ✅ Deployment Steps

- [ ] Clone repository to server
  ```bash
  git clone https://github.com/billallison/bluesky_raindrops.git
  cd bluesky_raindrops
  ```

- [ ] Create `.env` from template
  ```bash
  cp .env.example .env
  ```

- [ ] Edit `.env` with your credentials
  ```bash
  nano .env
  # Fill in all required values
  ```

- [ ] Verify .env is complete
  ```bash
  # Check all required variables are set (don't print secrets!)
  grep -E '^[A-Z_]+=.+' .env | cut -d= -f1
  # Should show all variable names
  ```

- [ ] Build and start container
  ```bash
  docker-compose up -d
  # Or: make deploy
  ```

## ✅ Post-Deployment Verification

- [ ] Container is running
  ```bash
  docker-compose ps
  # Status should be "Up"
  ```

- [ ] No errors in logs
  ```bash
  docker-compose logs
  # Should show initial execution
  ```

- [ ] Cron schedule is set
  ```bash
  docker-compose exec bluesky-raindrops-bot crontab -l
  # Should show: */10 * * * * /app/run_script.sh
  ```

- [ ] Logs directory created
  ```bash
  ls -la logs/
  # Should contain bluesky_raindrops.log
  ```

- [ ] Initial test execution
  ```bash
  make test
  # Should run without errors
  ```

- [ ] Test with actual Raindrop
  - [ ] Create a test bookmark in Raindrop.io
  - [ ] Tag it with "toskeet"
  - [ ] Wait for next cron run (up to 10 minutes)
  - [ ] Verify it posts to Bluesky
  - [ ] Verify "toskeet" tag is removed
  - [ ] Check logs for success message

## ✅ Optional Configuration

- [ ] Adjust timezone if needed
  - Edit `TZ` in docker-compose.yml
  - Restart: `docker-compose up -d`

- [ ] Adjust cron schedule if needed
  - Edit `CRON_SCHEDULE` in docker-compose.yml
  - Restart: `docker-compose up -d`

- [ ] Set up log monitoring (optional)
  - [ ] Configure external log aggregation
  - [ ] Set up alerts
  - [ ] Configure log rotation

## ✅ Backup & Documentation

- [ ] Backup `.env` file securely
  ```bash
  cp .env ~/.env.bluesky_raindrops.backup
  chmod 600 ~/.env.bluesky_raindrops.backup
  ```

- [ ] Document server location
  - Server hostname/IP: ________________
  - Container name: bluesky-raindrops-bot
  - Repository path: ________________

- [ ] Add to server documentation
  - [ ] List in server's service inventory
  - [ ] Add to backup procedures
  - [ ] Document in runbook

## ✅ Monitoring Setup

- [ ] Email alerts working
  - [ ] Trigger a test error
  - [ ] Verify email received

- [ ] Set up uptime monitoring (optional)
  - [ ] Add to monitoring tool
  - [ ] Configure alerts

- [ ] Regular log review scheduled
  - Frequency: ________________
  - Responsible: ________________

## 🚨 Troubleshooting Reminders

If something doesn't work:

1. **Check logs first**
   ```bash
   make logs-live
   ```

2. **Test manual execution**
   ```bash
   make test
   ```

3. **Verify .env configuration**
   ```bash
   # Check format (careful with secrets!)
   cat .env
   ```

4. **Check container status**
   ```bash
   docker-compose ps
   docker stats bluesky-raindrops-bot
   ```

5. **Review DOCKER_QUICKSTART.md**
   - Common issues section
   - Troubleshooting guide

## 📋 Maintenance Schedule

- [ ] **Weekly**: Review logs for errors
- [ ] **Monthly**: Update dependencies
  ```bash
  git pull
  make rebuild
  ```
- [ ] **Quarterly**: Review and rotate logs
- [ ] **Annually**: Rotate API tokens and passwords

## ✅ Migration Complete

- [ ] Old server bot disabled/stopped
- [ ] New server bot verified working
- [ ] Logs backed up from old server
- [ ] Old server bot removed (after testing period)

---

## Quick Reference Commands

```bash
# Start
make deploy

# Stop
docker-compose down

# View logs
make logs-live

# Test now
make test

# Restart
docker-compose restart

# Update
git pull && make rebuild

# Shell access
make shell
```

## Notes

Date deployed: ________________

Any custom configurations: ________________

Issues encountered: ________________

Resolution: ________________
