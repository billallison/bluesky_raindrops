# Raindrop to Bluesky Reader Bot

This Python script automatically posts content from Raindrop.io to Bluesky based on specific tags. It's designed to run periodically, fetching the most recent Raindrop item tagged with "toskeet" and posting it to Bluesky.

## Features

- Fetches the latest Raindrop item tagged with "toskeet"
- Posts the Raindrop item's title, link, and custom content to Bluesky
- Removes the "toskeet" tag after successful posting
- Logs errors and sends email notifications on failure

## Prerequisites

- **For Docker deployment** (recommended):
  - Docker and Docker Compose installed
  - Raindrop.io account
  - Bluesky account
  - SMTP server for email notifications (optional)

- **For manual Python deployment**:
  - Python 3.7+
  - Raindrop.io account
  - Bluesky account
  - SMTP server for email notifications (optional)

## Installation

### Option 1: Docker Deployment (Recommended)

Docker deployment provides a self-contained, isolated environment that runs on any system with Docker installed.

1. Clone this repository:
   ```bash
   git clone https://github.com/billallison/bluesky_raindrops.git
   cd bluesky_raindrops
   ```

2. Create your `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your actual credentials:
   ```bash
   nano .env  # or use your preferred editor
   ```
   
   Fill in the following values:
   ```env
   RAINDROP_TOKEN=your_raindrop_api_token
   BLUESKY_IDENTIFIER=your.bluesky.handle
   BLUESKY_PASSWORD=your_bluesky_app_password
   ADMIN_EMAIL=your_admin_email@example.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=465
   SMTP_LOGIN=your_smtp_username@gmail.com
   SMTP_PASSWORD=your_smtp_app_password
   LOG_LEVEL=WARNING
   ```

4. Build and start the container:
   ```bash
   docker-compose up -d
   ```

5. Verify it's running:
   ```bash
   docker-compose logs -f
   ```

**Container Management Commands:**
```bash
# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Restart the container
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# View container status
docker-compose ps
```

The container will automatically:
- Run the script every 10 minutes (configurable via `CRON_SCHEDULE` in docker-compose.yml)
- Restart automatically if it crashes
- Persist logs to the `./logs` directory on your host

**Customizing the Schedule:**

To change the execution frequency, edit `docker-compose.yml`:
```yaml
environment:
  - CRON_SCHEDULE=*/5 * * * *  # Every 5 minutes
  # - CRON_SCHEDULE=0 * * * *  # Every hour
  # - CRON_SCHEDULE=0 */2 * * *  # Every 2 hours
```

Then restart: `docker-compose up -d`

---

### Option 2: Manual Python Installation

---

### Option 2: Manual Python Installation

For those who prefer to run the script directly without Docker:

1. Clone this repository:
   ```bash
   git clone https://github.com/billallison/bluesky_raindrops.git
   cd bluesky_raindrops
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

## Usage

### Docker Usage (Recommended)

Once deployed with `docker-compose up -d`, the container runs continuously and automatically executes the script every 10 minutes. No manual intervention needed!

**Manual execution inside the container:**
```bash
# Run the script immediately (for testing)
docker-compose exec bluesky-raindrops-bot python /app/raindrop_to_bluesky.py
```

**Accessing logs:**
```bash
# View live logs
docker-compose logs -f

# View application logs
tail -f logs/bluesky_raindrops.log

# View cron execution logs
docker-compose exec bluesky-raindrops-bot cat /app/logs/cron.log
```

### Manual Python Usage

### Manual Python Usage

If you're running the script directly with Python:

1. Ensure your virtual environment is activated.

2. Run the script manually:
   ```bash
   python raindrop_to_bluesky.py
   ```

3. To run the script automatically every 10 minutes, set up a cron job (Linux/macOS) or Task Scheduler (Windows) to execute the script.

   Example cron job (runs every 10 minutes):
   ```cron
   */10 * * * * /path/to/venv/bin/python /path/to/raindrop_to_bluesky.py
   ```

## Deployment Notes

### Timezone Configuration

The container defaults to `America/New_York` timezone. To change it, edit the `TZ` environment variable in `docker-compose.yml`:

```yaml
environment:
  - TZ=America/Los_Angeles  # Or your preferred timezone
```

### Security Considerations

- **Never commit `.env` file** to version control (it's already in `.gitignore`)
- Use **app-specific passwords** for Bluesky (not your main password)
- Consider using **Docker secrets** for production deployments
- The container runs as a **non-root user** for security

### Resource Usage

The container is lightweight:
- **Memory**: ~100-150MB
- **CPU**: Minimal (only active during execution)
- **Disk**: ~200MB for image, logs grow over time
- **Network**: Outbound only (to APIs)

### Monitoring & Troubleshooting

**Check if container is running:**
```bash
docker-compose ps
```

**View recent logs:**
```bash
docker-compose logs --tail=50
```

**Check cron schedule:**
```bash
docker-compose exec bluesky-raindrops-bot crontab -l
```

**Restart container:**
```bash
docker-compose restart
```

**Test immediately:**
```bash
docker-compose exec bluesky-raindrops-bot python /app/raindrop_to_bluesky.py
```

## How It Works

1. The script queries the Raindrop.io API for the most recent item tagged with "toskeet". (It's LIFO so the freshest saved links get posted first.)
2. If a saved URL in Raindrop is found, the program extracts the item's title, link, and any custom content from the note field. To add comments to the bluesky post, add them in this format:
```
[skeet_content:_put your commentary to post here_]
```
Anything outside the braces will remain private (not posted).

3. The script then posts this information to Bluesky using the provided credentials.
4. Upon successful posting, the "toskeet" tag is removed from the Raindrop item.
5. If an error occurs, it's logged and an email notification is sent to the admin.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Future enhancements
- Add genAI alt-text for better accessibility
- Add an option for a short genAI summary in place of the excerpt

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
