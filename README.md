# Task Manager Bot

A highly advanced, modular, multi-user Telegram Task Management Bot with financial management, task planning, Google Calendar & Gmail sync.

## Features

- 🧑‍💼 **Multi-user Support**: User profiles, preferences, timezones, and permissions system
- ✅ **Task Management**: Create, edit, complete tasks with priorities, tags, projects, reminders
- 📆 **Google Integration**: Sync with Google Calendar and Gmail
- 📊 **Finance Management**: Track income & expenses, budgets, financial reports
- 📈 **Stats & Analytics**: Task completion trends, financial insights, productivity metrics
- 💬 **Rich Telegram UX**: Inline keyboards, beautiful messages, command-less interaction

## Project Structure

```
project/
├── manage.py                # Entry point
├── config/                  # Application configuration
├── bot/                     # Telegram bot interface
│   ├── client.py            # Pyrogram client
│   ├── handlers/            # Message and callback handlers
│   ├── keyboards/           # UI keyboards
│   └── messages/            # Message templates
├── apps/                    # Business logic modules
│   ├── users/               # User management
│   ├── tasks/               # Task management
│   ├── finance/             # Financial tracking
│   └── shared/              # Shared utilities
├── database/                # Database models and connection
├── services/                # External services integration
└── utils/                   # Utility functions
```

## Tech Stack

- **Bot Framework**: Pyrogram
- **ORM**: Tortoise ORM
- **Database**: SQLite (dev), PostgreSQL (prod)
- **API Integration**: Google OAuth2
- **Charts**: Matplotlib & Plotly
- **Scheduling**: APScheduler

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/task-manager-bot.git
   cd task-manager-bot
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```
   cp .env.template .env
   ```

5. Edit the `.env` file and add your credentials:
   - Get Telegram API credentials from https://my.telegram.org
   - Get a bot token from @BotFather
   - Set up Google OAuth credentials in Google Developer Console

## Usage

1. Initialize the database:
   ```
   python manage.py init_db
   ```

2. Start the bot:
   ```
   python manage.py start
   ```

## Deployment

### Deploying with Docker

1. Build the Docker image:
   ```
   docker build -t task-manager-bot .
   ```

2. Run the container:
   ```
   docker run -d --name task-bot --env-file .env task-manager-bot
   ```

### Deploying on a VPS

1. Set up systemd service:
   ```
   sudo cp deployment/task-manager-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable task-manager-bot
   sudo systemctl start task-manager-bot
   ```

2. Check status:
   ```
   sudo systemctl status task-manager-bot
   ```

## Development

### Adding a New Feature

1. Create necessary models in the appropriate app module
2. Add service methods to interact with the models
3. Create handlers in the bot module
4. Register handlers in the bot client

### Running Tests

```
pytest
```

## License

MIT License

## Acknowledgements

- [Pyrogram](https://docs.pyrogram.org/)
- [Tortoise ORM](https://tortoise-orm.readthedocs.io/)
- [APScheduler](https://apscheduler.readthedocs.io/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a pull request