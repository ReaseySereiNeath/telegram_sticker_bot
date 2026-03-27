import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import BOT_TOKEN
from bot.handlers import start_handler, submission_handler
from bot.admin import (
    pending_handler, approve_handler, reject_handler,
    approveall_handler, block_handler, stats_handler, packlink_handler,
    createpack_handler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Telegram Sticker Bot...")

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return

    # Initialize PTB Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User Handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE | filters.Sticker.ALL, submission_handler))

    # Admin Handlers
    application.add_handler(CommandHandler("pending", pending_handler))
    application.add_handler(CommandHandler("approve", approve_handler))
    application.add_handler(CommandHandler("reject", reject_handler))
    application.add_handler(CommandHandler("approveall", approveall_handler))
    application.add_handler(CommandHandler("block", block_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("packlink", packlink_handler))
    application.add_handler(CommandHandler("createpack", createpack_handler))

    logger.info("Bot is running...")
    
    # Start polling using PTB's run_polling, but handle event loop carefully.
    # Since we are already inside an asyncio function `main()`, we can just 
    # run application.initialize/start/updater explicitly, OR use the simpler `run_polling()`
    # Actually `application.run_polling()` blocks, which is what we want.
    # But wait, run_polling handles its own loop when called synchronously. 
    # inside async, we must do:
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep the task alive until interrupted
    stop_signal = asyncio.Event()
    try:
        await stop_signal.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Stopping bot gracefully...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped gracefully.")
