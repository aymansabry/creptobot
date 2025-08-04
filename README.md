# Customer Support Telegram Bot

A Telegram bot for handling customer support messages with conversation logging to a PostgreSQL database.

## Features

- Automatic response to customer messages
- Conversation logging to database
- Admin panel for viewing conversations
- PostgreSQL database integration

## Setup

1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Create a `.env` file with your configuration (see `.env.example`)
4. Run the bot: `python bot.py`

## Database Setup

The bot uses PostgreSQL. You can deploy it on Railway or any other hosting service.

### Railway Setup

1. Create a new project on Railway
2. Add a PostgreSQL service
3. Get the database URL and add it to your `.env` file
4. Deploy your bot

## Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/admin` - Admin panel (for admins only)
