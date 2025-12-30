"""
Главный модуль запуска Telegram бота.
Использует aiogram 3.x и асинхронную архитектуру.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

# Локальные импорты
from app.bot.handler import main_router
from app.bot.data.config import BOT_TOKEN

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    logger.info("Logging system initialized")


class BotApplication:
    def __init__(self, token: str):
        self.token = token
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None

    async def setup_bot(self) -> None:
        default = DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            protect_content=False,
        )

        self.bot = Bot(token=self.token, default=default)
        logger.debug("Bot instance created")

    async def setup_dispatcher(self) -> None:
        storage = MemoryStorage()
        self.dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)
        self._setup_routers()
        logger.debug("Dispatcher configured")

    def _setup_routers(self) -> None:
        self.dp.include_router(main_router)
        logger.debug("Routers registered")

    async def setup(self) -> None:
        await self.setup_bot()
        await self.setup_dispatcher()
        logger.info("Application setup completed")

    async def run(self) -> None:
        if not self.bot or not self.dp:
            raise RuntimeError("Application not properly initialized")

        logger.info("Starting bot in polling mode...")

        # На Windows add_signal_handler недоступен -> используем try/except и штатную остановку
        try:
            if sys.platform != "win32":
                loop = asyncio.get_running_loop()
                stop_event = asyncio.Event()

                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(sig, stop_event.set)

                polling_task = asyncio.create_task(
                    self.dp.start_polling(
                        self.bot,
                        allowed_updates=self.dp.resolve_used_update_types(),
                        handle_signals=False,
                        polling_timeout=30,
                        close_bot_session=False,
                    )
                )

                await stop_event.wait()
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task
            else:
                # Windows: просто запускаем polling, остановка через Ctrl+C
                await self.dp.start_polling(
                    self.bot,
                    allowed_updates=self.dp.resolve_used_update_types(),
                    polling_timeout=30,
                    close_bot_session=False,
                )

        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
        except asyncio.CancelledError:
            logger.warning("Polling task was cancelled")
        except Exception as e:
            logger.error(f"Error in polling: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        logger.info("Shutting down application...")

        if self.dp:
            await self.dp.storage.close()
            logger.debug("Dispatcher storage closed")

        if self.bot:
            await self.bot.session.close()
            logger.debug("Bot session closed")

        logger.info("Application shutdown completed")


@asynccontextmanager
async def bot_lifespan():
    logger.info("Starting bot lifespan")
    try:
        yield
    finally:
        logger.info("Ending bot lifespan")


async def main() -> None:
    setup_logging()

    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN not configured")
        sys.exit(1)

    logger.info("Initializing Telegram bot...")

    async with bot_lifespan():
        app = BotApplication(BOT_TOKEN)
        await app.setup()
        await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
