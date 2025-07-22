#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from dotenv import load_dotenv
from telegram import BotCommand, MenuButton, MenuButtonCommands
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from handlers import (
    start_command,
    menu_command,
    help_command,
    status_command,
    team_selection_callback,
    handle_gender_selection,
    handle_reason_input,
    handle_experience_input,
    handle_whatsapp_input,
    cancel_command,
    stats_command,
    broadcast_command,
    handle_broadcast_message,
    clear_applications_command,
    handle_admin_reply,
    handle_admin_decision,
    handle_end_conversation,
    handle_unknown_message,
    ASKING_GENDER,
    ASKING_REASON,
    ASKING_EXPERIENCE,
    ASKING_WHATSAPP,
    ASKING_BROADCAST_MESSAGE
)
from config import ADMIN_GROUP_ID, BOT_NAME, BOT_VERSION, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate required environment variables."""
    bot_token = os.getenv("BOT_TOKEN")
    admin_group_id = os.getenv("ADMIN_GROUP_ID")
    
    if not bot_token:
        logger.error("BOT_TOKEN environment variable is required!")
        return False
    
    if not admin_group_id:
        logger.error("ADMIN_GROUP_ID environment variable is required!")
        return False
    
    try:
        int(admin_group_id)
    except ValueError:
        logger.error("ADMIN_GROUP_ID must be a valid integer!")
        return False
    
    return True

async def setup_bot_commands(application):
    """Setup bot commands and menu button after bot is ready."""
    try:
        commands = [
            BotCommand("start", "بدء استخدام البوت والتقديم للتيمز"),
            BotCommand("menu", "عرض القائمة الرئيسية والخيارات المتاحة"),
            BotCommand("help", "عرض المساعدة المفصلة"),
            BotCommand("status", "عرض حالة طلباتك"),
            BotCommand("cancel", "إلغاء العملية الحالية"),
            BotCommand("stats", "إحصائيات التقديمات (للإدارة فقط)"),
            BotCommand("broadcast", "إرسال رسالة جماعية (للإدارة فقط)"),
            BotCommand("clear", "مسح جميع التقديمات (للإدارة فقط)")
        ]
        
        # Set commands
        await application.bot.set_my_commands(commands)
        
        # Set menu button
        menu_button = MenuButtonCommands()
        await application.bot.set_chat_menu_button(menu_button=menu_button)
        
        logger.info("Bot commands and menu button set successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup bot commands: {e}")

async def error_handler(update, context):
    """Handle errors that occur during bot operation."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Try to send error message to user if possible
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى أو التواصل مع الإدارة."
            )
        except Exception:
            pass

def main():
    """Start the bot."""
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION}")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Get bot token from environment
    bot_token = os.getenv("BOT_TOKEN")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Set post init callback
    application.post_init = setup_bot_commands
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Define conversation handler for team applications
    application_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(team_selection_callback, pattern="^team_")
        ],
        states={
            ASKING_GENDER: [
                CallbackQueryHandler(handle_gender_selection, pattern="^gender_")
            ],
            ASKING_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason_input)
            ],
            ASKING_EXPERIENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_experience_input)
            ],
            ASKING_WHATSAPP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_whatsapp_input)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command)
        ],
        allow_reentry=True
    )
    
    # Define conversation handler for broadcast
    broadcast_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("broadcast", broadcast_command)
        ],
        states={
            ASKING_BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=False
    )
    
    # Add handlers in order of priority
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("clear", clear_applications_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add conversation handlers
    application.add_handler(application_conversation)
    application.add_handler(broadcast_conversation)
    
    # Handle admin decision buttons
    application.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(accept_|reject_)"))
    
    # Handle end conversation button
    application.add_handler(CallbackQueryHandler(handle_end_conversation, pattern="^end_chat_"))
    
    # Add handlers for admin group messages (replies and media)
    application.add_handler(MessageHandler(
        filters.Chat(ADMIN_GROUP_ID) & (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.DOCUMENT | filters.VOICE | filters.VIDEO_NOTE),
        handle_admin_reply
    ))
    
    # Handle unknown messages (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    # Log startup
    logger.info(f"{BOT_NAME} started successfully!")
    logger.info(f"Admin Group ID: {ADMIN_GROUP_ID}")
    
    # Run the bot
    try:
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

