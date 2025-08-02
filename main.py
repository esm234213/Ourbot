#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys

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
    handle_broadcast_type,           # NEW: Add this import
    handle_broadcast_message,
    handle_broadcast_image,          # NEW: Add this import
    clear_applications_command,
    handle_admin_reply,
    handle_admin_decision,
    handle_end_conversation,
    handle_unknown_message,
    # Media handlers
    handle_admin_photo,
    handle_admin_video,
    handle_admin_audio,
    handle_user_photo,
    handle_user_video,
    handle_user_audio,
    ban_command,
    unban_command,
    ASKING_GENDER,
    ASKING_REASON,
    ASKING_EXPERIENCE,
    ASKING_WHATSAPP,
    ASKING_BROADCAST_TYPE,           # NEW: Add this import
    ASKING_BROADCAST_MESSAGE,
    ASKING_BROADCAST_IMAGE           # NEW: Add this import
)
from config import ADMIN_GROUP_ID, BOT_NAME, BOT_VERSION, LOG_LEVEL, LOG_FORMAT, BOT_TOKEN

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


def validate_environment():
    """Validate required environment variables."""
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
            BotCommand("broadcast", "إرسال رسالة جماعية مع دعم الصور (للإدارة فقط)"),  # Updated description
            BotCommand("ban", "حظر مستخدم (للإدارة فقط)"),
            BotCommand("unban", "إلغاء حظر مستخدم (للإدارة فقط)"),
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
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION} with Enhanced Media Support & Image Broadcast")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Get bot token from environment

    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
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
    
    # UPDATED: Enhanced broadcast conversation handler with image support
    broadcast_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("broadcast", broadcast_command)
        ],
        states={
            ASKING_BROADCAST_TYPE: [
                CallbackQueryHandler(handle_broadcast_type, pattern="^broadcast_")
            ],
            ASKING_BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)
            ],
            ASKING_BROADCAST_IMAGE: [
                MessageHandler(filters.PHOTO, handle_broadcast_image)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=False
    )
    
    # Add basic command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("clear", clear_applications_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add conversation handlers (order matters!)
    application.add_handler(application_conversation)
    application.add_handler(broadcast_conversation)
    
    # Handle admin decision buttons
    application.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(accept_|reject_)"))
    
    # Handle end conversation button
    application.add_handler(CallbackQueryHandler(handle_end_conversation, pattern="^end_chat_"))
    
    # Handle admin media messages (only from admin group)
    application.add_handler(MessageHandler(
        filters.PHOTO & filters.Chat(ADMIN_GROUP_ID), 
        handle_admin_photo
    ))
    
    application.add_handler(MessageHandler(
        filters.VIDEO & filters.Chat(ADMIN_GROUP_ID), 
        handle_admin_video
    ))
    
    application.add_handler(MessageHandler(
        (filters.AUDIO | filters.VOICE) & filters.Chat(ADMIN_GROUP_ID), 
        handle_admin_audio
    ))
    
    # Handle admin text replies (only from admin group)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(ADMIN_GROUP_ID), 
        handle_admin_reply
    ))
    
    # Handle user media messages (not from admin group)
    application.add_handler(MessageHandler(
        filters.PHOTO & ~filters.Chat(ADMIN_GROUP_ID), 
        handle_user_photo
    ))
    
    application.add_handler(MessageHandler(
        filters.VIDEO & ~filters.Chat(ADMIN_GROUP_ID), 
        handle_user_video
    ))
    
    application.add_handler(MessageHandler(
        (filters.AUDIO | filters.VOICE) & ~filters.Chat(ADMIN_GROUP_ID), 
        handle_user_audio
    ))
    
    # Handle unknown text messages (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    # Log startup information
    logger.info(f"{BOT_NAME} started successfully with enhanced media support & image broadcast!")
    logger.info(f"Admin Group ID: {ADMIN_GROUP_ID}")
    logger.info("🚀 Features enabled:")
    logger.info("  📱 Media types: Photos, Videos, Audio, Voice messages")
    logger.info("  📢 Broadcast types: Text-only, Image with text")
    logger.info("  💬 Admin-User conversations with media support")
    logger.info("  🛡️ User ban/unban functionality")
    logger.info("  📊 Statistics and data management")
    logger.info("  🔄 Application status tracking")
    
    # Run the bot
    try:
        logger.info("🤖 Bot is now polling for updates...")
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Bot crashed with error: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Bot shutdown complete")

if __name__ == "__main__":
    main()

