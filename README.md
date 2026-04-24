# Telegram AI Agent Bot (Per-User Sessions)

This project creates a Telegram bot where **each Telegram user gets their own AI agent session**.

## Features

- Per-user conversation memory keyed by Telegram `user_id`
- `/start` welcome command
- `/reset` clears only the requesting user's memory
- Safe default system prompt
- Uses OpenAI Chat Completions API

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An OpenAI API key

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   ```bash
   export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   export OPENAI_API_KEY="your_openai_api_key"
   # Optional:
   export OPENAI_MODEL="gpt-4o-mini"
   ```

4. Run the bot:

   ```bash
   python telegram_ai_agent_bot.py
   ```

## How per-user AI agents work

- The bot stores a conversation state object for each Telegram user.
- Incoming messages from a user append to that user's own history.
- Replies are generated from that same user-scoped context.
- `/reset` only clears history for the user who runs the command.

## Notes

- This implementation uses in-memory storage. If the process restarts, memory resets.
- For production, replace memory storage with Redis/PostgreSQL and add observability/rate limits.
