# Raindrop to Bluesky Reader Bot

This Python script automatically posts content from Raindrop.io to Bluesky based on specific tags. It's designed to run periodically, fetching the most recent Raindrop item tagged with "toskeet" and posting it to Bluesky.

## Features

- Fetches the latest Raindrop item tagged with `toskeet` and posts it to Bluesky as a rich-text link card with an image embed
- Optional commentary via `[skeet_content: ...]` in the Raindrop note (see [How It Works](#how-it-works))
- Strips tracking query parameters (`utm_*`, `cmpid`, `gclid`, `fbclid`, etc.) from posted URLs for cleaner posts and to stay under Bluesky's character limit
- Respects Bluesky's 300-grapheme limit with proper Unicode counting and a safety-net retry if the rendered text overshoots
- Removes the `toskeet` tag after a successful post
- File-locked execution prevents overlapping cron runs from posting twice
- Local posted-ID tracker prevents duplicates if tag removal fails on a transient Raindrop API error
- Retries Raindrop and Bluesky calls with exponential backoff on `429`/`5xx`/timeout
- Logs errors and sends email notifications via SMTP

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

> **Note:** examples below use Docker Compose v1 (`docker-compose`). If you have Compose v2, the equivalent is `docker compose` (with a space). Both work.

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

1. The script queries the Raindrop.io API for the most recent item tagged with `toskeet`. (LIFO — the freshest saved link gets posted first.)
2. If a saved URL is found, the program extracts the item's title, link, and any custom content from the note field. To add commentary to the Bluesky post, write it in the note like this:
   ```
   [skeet_content: put your commentary to post here]
   ```
   Anything outside the brackets stays private (not posted).
3. Tracking query parameters (`utm_*`, `cmpid`, `gclid`, `fbclid`, etc.) are stripped from the URL before posting.
4. The post is built with atproto's rich-text builder so the link is clickable, and a cover-image embed is attached if available.
5. The text is checked against Bluesky's 300-grapheme limit; if the rendered post still overshoots after the URL is built, the body is shrunk and rebuilt.
6. The post is sent to Bluesky.
7. On success, the post is recorded in `logs/posted_raindrops.json` (so a tag-removal failure won't cause a double-post on the next run), and the `toskeet` tag is removed from Raindrop.
8. On failure, the error is logged and an email notification is sent to the admin.

## Development & Testing

The repo ships with two regression-test scripts under `scripts/` — they run as plain Python/Bash with no test runner required:

```bash
# Post-formatter tests (URL handling, grapheme limits, tracking-param stripping).
# Requires the project dependencies; install into a venv first:
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/test_formatter.py

# Entrypoint .env-loader tests (handles unquoted values like CRON_SCHEDULE=*/5 * * * *)
bash scripts/test_env_loader.sh
```

Both scripts exit non-zero on failure, so they can be wired into CI without modification.

## Contributing

Contributions are welcome — open an issue or PR. Please add a regression test under `scripts/` for any bug fix.

## Future enhancements

- GenAI-generated alt-text on the cover image for accessibility
- Optional GenAI summary in place of the Raindrop excerpt

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
