# Raindrop to Bluesky Poster

This Python script automatically posts content from Raindrop.io to Bluesky based on specific tags. It's designed to run periodically, fetching the most recent Raindrop item tagged with "toskeet" and posting it to Bluesky.

## Features

- Fetches the latest Raindrop item tagged with "toskeet"
- Posts the Raindrop item's title, link, and custom content to Bluesky
- Removes the "toskeet" tag after successful posting
- Logs errors and sends email notifications on failure

## Prerequisites

- Python 3.7+
- Raindrop.io account
- Bluesky account
- SMTP server for email notifications (optional)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/raindrop-to-bluesky.git
   cd raindrop-to-bluesky
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following content:
   ```
   RAINDROP_TOKEN=your_raindrop_api_token
   BLUESKY_IDENTIFIER=your_bluesky_identifier
   BLUESKY_PASSWORD=your_bluesky_password
   ADMIN_EMAIL=your_admin_email@example.com
   SMTP_SERVER=your_smtp_server
   SMTP_PORT=your_smtp_port
   SMTP_USERNAME=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   ```

## Usage

1. Ensure your virtual environment is activated.

2. Run the script manually:
   ```
   python raindrop_to_bluesky.py
   ```

3. To run the script automatically every 10 minutes, set up a cron job (Linux/macOS) or Task Scheduler (Windows) to execute the script.

   Example cron job (runs every 10 minutes):
   ```
   */10 * * * * /path/to/venv/bin/python /path/to/raindrop_to_bluesky.py
   ```

## How It Works

1. The script queries the Raindrop.io API for the most recent item tagged with "toskeet".
2. If found, it extracts the item's title, link, and any custom content from the note field.
3. The script then posts this information to Bluesky using the provided credentials.
4. Upon successful posting, the "toskeet" tag is removed from the Raindrop item.
5. If an error occurs, it's logged and an email notification is sent to the admin.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

This README provides a comprehensive overview of your project, including installation instructions, usage guidelines, and a brief explanation of how the script works. You may want to adjust some details based on your specific implementation and preferences.
