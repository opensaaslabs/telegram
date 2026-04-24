"""Telegram bot with per-user AI agent sessions."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List

from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a helpful, concise AI assistant in a Telegram chat. "
    "Ask clarifying questions when needed and provide practical answers."
)


@dataclass
class UserAgentSession:
    """Conversation state scoped to one Telegram user."""

    messages: List[Dict[str, str]] = field(default_factory=list)

    def as_chat_messages(self, user_text: str) -> List[Dict[str, str]]:
        payload: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        payload.extend(self.messages)
        payload.append({"role": "user", "content": user_text})
        return payload

    def append_turn(self, user_text: str, assistant_text: str) -> None:
        self.messages.append({"role": "user", "content": user_text})
        self.messages.append({"role": "assistant", "content": assistant_text})


class TelegramAIAgentBot:
    """Manages Telegram handlers and per-user AI sessions."""

    def __init__(self, openai_client: AsyncOpenAI, model: str) -> None:
        self._openai = openai_client
        self._model = model
        self._sessions: Dict[int, UserAgentSession] = {}

    def _get_session(self, user_id: int) -> UserAgentSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserAgentSession()
        return self._sessions[user_id]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _ = context
        await update.message.reply_text(
            "Hi! I am your AI Telegram assistant. "
            "Each user has a separate AI memory. "
            "Send a message to begin, or use /reset to clear your memory."
        )

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _ = context
        user = update.effective_user
        if not user:
            return
        self._sessions[user.id] = UserAgentSession()
        await update.message.reply_text("Your AI session memory has been reset.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _ = context
        message = update.message
        user = update.effective_user
        if not message or not user or not message.text:
            return

        session = self._get_session(user.id)
        user_text = message.text.strip()

        await message.chat.send_action(action=ChatAction.TYPING)
        try:
            response = await self._openai.chat.completions.create(
                model=self._model,
                messages=session.as_chat_messages(user_text),
                temperature=0.7,
            )
            assistant_text = response.choices[0].message.content or "I couldn't generate a response."
            session.append_turn(user_text=user_text, assistant_text=assistant_text)
            await message.reply_text(assistant_text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error while generating AI response")
            await message.reply_text(
                "Sorry, I hit an error while contacting the AI service. "
                f"Please try again. ({type(exc).__name__})"
            )


def build_application() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    bot = TelegramAIAgentBot(openai_client=AsyncOpenAI(api_key=api_key), model=model)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("reset", bot.reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    return app


async def main() -> None:
    app = build_application()
    logger.info("Starting Telegram AI agent bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
