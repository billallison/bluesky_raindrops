#!/bin/bash
set -e

echo "Starting Raindrop to Bluesky Bot..."
echo "Container started at: $(date)"

# Ensure logs directory has correct permissions (only if we have permission)
if [ -w /app/logs ]; then
    chown -R appuser:appuser /app/logs 2>/dev/null || true
fi

# Create crontab for the appuser
# Run every 10 minutes
CRON_SCHEDULE="${CRON_SCHEDULE:-*/10 * * * *}"

# Create a shell script that will be called by cron
# This ensures the environment variables are available
cat > /app/run_script.sh << 'EOF'
#!/bin/bash
cd /app
# Export environment variables from .env, filtering out comments and empty lines
export $(grep -v '^#' /app/.env | grep -v '^$' | xargs)
/usr/local/bin/python /app/raindrop_to_bluesky.py >> /app/logs/cron.log 2>&1
EOF

chmod +x /app/run_script.sh
chown appuser:appuser /app/run_script.sh

# Set up cron job for appuser
echo "$CRON_SCHEDULE /app/run_script.sh" > /tmp/crontab.tmp
crontab -u appuser /tmp/crontab.tmp
rm /tmp/crontab.tmp

# Start cron in foreground
echo "Cron schedule: $CRON_SCHEDULE"
echo "Cron job installed for user: appuser"
crontab -u appuser -l

# Run the script once immediately on startup as appuser
echo "Running initial execution..."
su -s /bin/bash -c "cd /app && export \$(grep -v '^#' /app/.env | grep -v '^$' | xargs) && /usr/local/bin/python /app/raindrop_to_bluesky.py" appuser

# Start cron in the foreground
exec cron -f
