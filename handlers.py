#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from config import *
from data_manager import DataManager

logger = logging.getLogger(__name__)

# Initialize data manager
data_manager = DataManager()

# Store mapping of admin messages to original user IDs
# Format: {admin_message_id: user_id}
admin_message_to_user = {}

# Store active conversations between users and admins
# Format: {user_id: {'admin_id': admin_id, 'active': True}}
active_conversations = {}

# Conversation states
ASKING_GENDER = 1
ASKING_REASON = 2
ASKING_EXPERIENCE = 3
ASKING_WHATSAPP = 4

# Conversation states for broadcast
ASKING_BROADCAST_TYPE = 9
ASKING_BROADCAST_MESSAGE = 10
ASKING_BROADCAST_IMAGE = 11

# Media directories
MEDIA_DIR = "media"
IMAGES_DIR = os.path.join(MEDIA_DIR, "images")
VIDEOS_DIR = os.path.join(MEDIA_DIR, "videos")
AUDIO_DIR = os.path.join(MEDIA_DIR, "audio")

# Create media directories if they don't exist
for directory in [MEDIA_DIR, IMAGES_DIR, VIDEOS_DIR, AUDIO_DIR]:
    os.makedirs(directory, exist_ok=True)

async def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command - show welcome message and team selection buttons."""
    user = update.effective_user
    
    try:
        if data_manager.is_user_banned(user.id):
            await update.message.reply_text("لقد تم حظرك من استخدام البوت.")
            logger.info(f"Banned user {user.id} tried to start the bot.")
            return

        # Create inline keyboard with team options
        keyboard = []
        row = []
        
        for team_id, team_name in TEAMS.items():
            row.append(InlineKeyboardButton(team_name, callback_data=team_id))
            
            # Create rows of 2 buttons each
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Add remaining button if any
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"User {user.id} ({user.first_name}) started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def menu_command(update: Update, context: CallbackContext) -> None:
    """Handle /menu command - show main menu options."""
    try:
        menu_text = """
📋 <b>القائمة الرئيسية - Our Goal Bot</b>

🎯 <b>الخيارات المتاحة:</b>

• /start - بدء التقديم للتيمز
• /menu - عرض هذه القائمة
• /help - مساعدة مفصلة
• /status - عرض حالة طلباتك
• /cancel - إلغاء العملية الحالية

💡 <b>كيفية الاستخدام:</b>
1. اضغط على /start للبدء
2. اختر التيم المناسب
3. اجب على الأسئلة المطلوبة
4. سيتم إرسال طلبك للإدارة

🔄 يمكنك الضغط على /start في أي وقت للتقديم على تيم جديد

📱 <b>الميزات الجديدة:</b>
• دعم الرد بالصور والفيديو والصوت
• تفاعل محسن مع الإدارة
"""
        
        await update.message.reply_text(menu_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in menu_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command - show detailed help."""
    try:
        await update.message.reply_text(HELP_MESSAGE, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def status_command(update: Update, context: CallbackContext) -> None:
    """Handle /status command - show user's application status."""
    user = update.effective_user
    
    try:
        user_status = data_manager.get_user_status(user.id)
        
        if user_status['total_applications'] == 0:
            await update.message.reply_text(
                "📋 لم تقدم على أي تيم بعد.\n\nيمكنك الضغط على /start للبدء في التقديم.",
                parse_mode='HTML'
            )
            return
        
        # Format user name
        user_name = user.first_name
        if user.last_name:
            user_name += f" {user.last_name}"
        
        # Format applications list
        applications_list = ""
        for i, app in enumerate(user_status['applications'], 1):
            app_time = app['timestamp'][:19].replace('T', ' ')
            applications_list += f"{i}. {app['team_name']} - {app_time}\n"
        
        status_text = STATUS_MESSAGE.format(
            user_name=user_name,
            user_id=user.id,
            total_applications=user_status['total_applications'],
            applications_list=applications_list
        )
        
        await update.message.reply_text(status_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in status_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def team_selection_callback(update: Update, context: CallbackContext) -> int:
    """Handle team selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    team_id = query.data
    team_name = TEAMS.get(team_id, "غير معروف")
    
    try:
        # Check if user already applied to this team
        if data_manager.has_user_applied(user.id, team_id):
            # Check if user can reapply (after cooldown)
            if not data_manager.can_user_reapply(user.id, team_id):
                await query.edit_message_text(
                    ALREADY_APPLIED.format(team_name=team_name)
                )
                return ConversationHandler.END
        
        # Store team selection in context
        context.user_data['selected_team'] = team_id
        context.user_data['team_name'] = team_name
        context.user_data['user_info'] = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'username': user.username or '',
            'timestamp': datetime.now().isoformat()
        }
        
        # Ask for gender first
        gender_keyboard = [
            [
                InlineKeyboardButton("👨 ذكر", callback_data=f"gender_male_{team_id}"),
                InlineKeyboardButton("👩 أنثى", callback_data=f"gender_female_{team_id}")
            ]
        ]
        gender_reply_markup = InlineKeyboardMarkup(gender_keyboard)
        
        await query.edit_message_text(
            TEAM_SELECTION_MESSAGE.format(team_name=team_name),
            reply_markup=gender_reply_markup
        )
        
        logger.info(f"User {user.id} selected team {team_id}")
        return ASKING_GENDER
        
    except Exception as e:
        logger.error(f"Error in team_selection_callback: {e}")
        await query.edit_message_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_gender_selection(update: Update, context: CallbackContext) -> int:
    """Handle gender selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Parse callback data: gender_male_team_id or gender_female_team_id
        callback_parts = query.data.split("_")
        gender = callback_parts[1]  # male or female
        team_id = callback_parts[2]  # team_id
        
        # Store gender in context
        context.user_data['gender'] = "ذكر" if gender == "male" else "أنثى"
        
        # Get team name
        team_name = context.user_data.get('team_name', TEAMS.get(team_id, "غير معروف"))
        
        # Ask for reason
        await query.edit_message_text(
            GENDER_QUESTION.format(team_name=team_name)
        )
        
        logger.info(f"User {update.effective_user.id} selected gender: {context.user_data['gender']}")
        return ASKING_REASON
        
    except Exception as e:
        logger.error(f"Error in handle_gender_selection: {e}")
        await query.edit_message_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_reason_input(update: Update, context: CallbackContext) -> int:
    """Handle user's reason for joining the team."""
    try:
        user_reason = update.message.text.strip()
        team_name = context.user_data.get('team_name', 'غير معروف')
        
        # Validate input length
        if len(user_reason) < 10:
            await update.message.reply_text(
                "⚠️ الرجاء كتابة إجابة أكثر تفصيلاً (على الأقل 10 أحرف).\n\nليه عايز تنضم لـ {}؟".format(team_name)
            )
            return ASKING_REASON
        
        if len(user_reason) > 1000:
            await update.message.reply_text(
                "⚠️ الإجابة طويلة جداً. الرجاء اختصارها (أقل من 1000 حرف)."
            )
            return ASKING_REASON
        
        # Store reason in context
        context.user_data['reason'] = user_reason
        
        # Ask for experience
        await update.message.reply_text(
            EXPERIENCE_QUESTION.format(team_name=team_name)
        )
        
        return ASKING_EXPERIENCE
        
    except Exception as e:
        logger.error(f"Error in handle_reason_input: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_experience_input(update: Update, context: CallbackContext) -> int:
    """Handle user's experience input and check if WhatsApp number is needed."""
    try:
        user_experience = update.message.text.strip()
        user = update.effective_user
        
        # Validate input length
        if len(user_experience) < 5:
            await update.message.reply_text(
                "⚠️ الرجاء كتابة إجابة أكثر تفصيلاً (على الأقل 5 أحرف).\n\nما هي خبرتك؟"
            )
            return ASKING_EXPERIENCE
        
        if len(user_experience) > 1000:
            await update.message.reply_text(
                "⚠️ الإجابة طويلة جداً. الرجاء اختصارها (أقل من 1000 حرف)."
            )
            return ASKING_EXPERIENCE
        
        # Store experience in context
        context.user_data['experience'] = user_experience
        
        # Check if user has username
        if not user.username:
            # User doesn't have username, ask for WhatsApp number
            await update.message.reply_text(WHATSAPP_QUESTION)
            return ASKING_WHATSAPP
        else:
            # User has username, complete application
            return await complete_application(update, context)
        
    except Exception as e:
        logger.error(f"Error in handle_experience_input: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_whatsapp_input(update: Update, context: CallbackContext) -> int:
    """Handle WhatsApp number input and complete application."""
    try:
        whatsapp_number = update.message.text.strip()
        
        # Validate WhatsApp number format
        if not validate_whatsapp_number(whatsapp_number):
            await update.message.reply_text(
                "⚠️ رقم الواتساب غير صحيح. يرجى كتابة الرقم بالتنسيق الصحيح.\n\n🇪🇬 مصر: +201234567890 أو 01234567890\n🇸🇦 السعودية: +966512345678 أو 0512345678"
            )
            return ASKING_WHATSAPP
        
        # Store WhatsApp number in context
        context.user_data['whatsapp_number'] = whatsapp_number
        
        # Complete application
        return await complete_application(update, context)
        
    except Exception as e:
        logger.error(f"Error in handle_whatsapp_input: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

def validate_whatsapp_number(number: str) -> bool:
    """Validate WhatsApp number format for Egyptian and Saudi numbers."""
    import re
    
    # Remove spaces and common separators
    clean_number = re.sub(r'[\s\-\(\)]', '', number)
    
    # Check if it's a valid Egyptian or Saudi phone number format
    # Egyptian mobile numbers: +201xxxxxxxx, 01xxxxxxxx (010, 011, 012, 015)
    # Saudi mobile numbers: +9665xxxxxxxx, 05xxxxxxxx (050-059)
    patterns = [
        # Egyptian numbers
        r'^(\+?20(1[0125]|10|11|12|15)[0-9]{8}|0(1[0125]|10|11|12|15)[0-9]{8})$',
        # Saudi numbers  
        r'^(\+?966(5[0-9])[0-9]{7}|0(5[0-9])[0-9]{7})$'
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_number):
            return True
    
    return False

async def complete_application(update: Update, context: CallbackContext) -> int:
    """Complete the application process."""
    try:
        # Prepare application data
        application_data = {
            'user_info': context.user_data['user_info'],
            'selected_team': context.user_data['selected_team'],
            'team_name': context.user_data['team_name'],
            'gender': context.user_data['gender'],
            'reason': context.user_data['reason'],
            'experience': context.user_data['experience'],
            'whatsapp_number': context.user_data.get('whatsapp_number', None),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save application
        if data_manager.save_application(application_data):
            # Send notification to admin group
            await send_admin_notification(context, application_data)
            
            # Confirm to user
            await update.message.reply_text(
                APPLICATION_SUBMITTED.format(team_name=context.user_data['team_name'])
            )
            
            logger.info(f"Application submitted successfully for user {application_data['user_info']['user_id']}")
        else:
            await update.message.reply_text(
                "❌ حدث خطأ في حفظ طلبك. يرجى المحاولة مرة أخرى."
            )
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in complete_application: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def send_admin_notification(context: CallbackContext, application_data: dict) -> None:
    """Send application notification to admin group."""
    try:
        user_info = application_data['user_info']
        
        # Format user name
        user_name = user_info['first_name']
        if user_info['last_name']:
            user_name += f" {user_info['last_name']}"
        
        username_text = f"(@{user_info['username']})" if user_info['username'] else "(لا يوجد username)"
        
        # Add WhatsApp number if available
        whatsapp_info = ""
        if application_data.get('whatsapp_number'):
            whatsapp_info = f"\n📱 <b>رقم الواتساب:</b> {application_data['whatsapp_number']}"
        
        # Create notification message
        notification_text = f"""
🆕 <b>طلب تقديم جديد!</b>

👤 <b>المتقدم:</b> {user_name} {username_text}
🆔 <b>معرف المستخدم:</b> {user_info['user_id']}{whatsapp_info}
👫 <b>الجنس:</b> {application_data['gender']}
🎯 <b>التيم:</b> {application_data['team_name']}

❓ <b>سبب الانضمام:</b>
{application_data['reason']}

💼 <b>الخبرة:</b>
{application_data['experience']}

📅 <b>وقت التقديم:</b> {application_data['timestamp'][:19]}

💬 <b>للرد على المتقدم:</b> رد على هذه الرسالة وسيتم إرسال ردك إليه تلقائياً
📷 <b>يمكنك الرد بالصور والفيديو والصوت أيضاً!</b>
"""
        
        # Create inline keyboard with accept/reject buttons
        # Include team_name in callback data to preserve it
        keyboard = [
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_info['user_id']}_{application_data['selected_team']}_{application_data['team_name']}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_info['user_id']}_{application_data['selected_team']}_{application_data['team_name']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=notification_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Store mapping for admin replies
        admin_message_to_user[sent_message.message_id] = user_info['user_id']
        
        logger.info(f"Admin notification sent for user {user_info['user_id']}")
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Handle /stats command - show application statistics (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text(NO_STATS_PERMISSION)
            return
        
        stats = data_manager.get_stats()
        
        if stats['total_applications'] == 0:
            await update.message.reply_text(NO_APPLICATIONS_YET)
            return
        
        stats_text = STATS_HEADER.format(
            total_applications=stats['total_applications'],
            total_users=stats['total_users']
        )
        
        # Add team breakdown
        for team_id, count in stats['teams'].items():
            team_name = TEAMS.get(team_id, team_id)
            percentage = (count / stats['total_applications'] * 100) if stats['total_applications'] > 0 else 0
            stats_text += f"• {team_name}: {count} طلب ({percentage:.1f}%)\n"
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def broadcast_command(update: Update, context: CallbackContext) -> int:
    """Handle /broadcast command - send message to all users (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text("⚠️ هذا الأمر مخصص للإدارة فقط")
            return ConversationHandler.END
        
        # Ask for broadcast type
        keyboard = [
            [
                InlineKeyboardButton("📝 نص فقط", callback_data="broadcast_text"),
                InlineKeyboardButton("🖼️ صورة مع نص", callback_data="broadcast_image")
            ],
            [InlineKeyboardButton("❌ إلغاء", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📢 <b>اختر نوع الرسالة الإذاعية:</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ASKING_BROADCAST_TYPE
        
    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')
        return ConversationHandler.END

async def handle_broadcast_type(update: Update, context: CallbackContext) -> int:
    """Handle broadcast type selection."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "broadcast_cancel":
            await query.edit_message_text("❌ تم إلغاء الإرسال الإذاعي.")
            return ConversationHandler.END
        
        elif query.data == "broadcast_text":
            context.user_data['broadcast_type'] = 'text'
            await query.edit_message_text(BROADCAST_PROMPT, parse_mode='HTML')
            return ASKING_BROADCAST_MESSAGE
        
        elif query.data == "broadcast_image":
            context.user_data['broadcast_type'] = 'image'
            await query.edit_message_text(
                "🖼️ <b>أرسل الصورة التي تريد إرسالها في الرسالة الإذاعية:</b>\n\n"
                "💡 يمكنك إضافة نص مع الصورة كتعليق (caption)",
                parse_mode='HTML'
            )
            return ASKING_BROADCAST_IMAGE
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_type: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')
        return ConversationHandler.END

async def handle_broadcast_message(update: Update, context: CallbackContext) -> int:
    """Handle broadcast text message input with improved error handling."""
    try:
        broadcast_text = update.message.text.strip()
        
        if len(broadcast_text) < 5:
            await update.message.reply_text("⚠️ الرسالة قصيرة جداً. يرجى كتابة رسالة أطول.")
            return ASKING_BROADCAST_MESSAGE
        
        # Get all users
        all_users = data_manager.get_all_users()
        
        if not all_users:
            await update.message.reply_text("❌ لا يوجد مستخدمين لإرسال الرسالة إليهم.")
            return ConversationHandler.END
        
        # Send broadcast message with improved error handling
        sent_count = 0
        failed_count = 0
        
        # Add header to broadcast message
        formatted_message = f"""
📢 <b>رسالة من فريق Our Goal</b>

{broadcast_text}

---
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send to all users with individual error handling
        for user_id in all_users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=formatted_message,
                    parse_mode='HTML'
                )
                sent_count += 1
                logger.info(f"Broadcast message sent successfully to user {user_id}")
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast message to user {user_id}: {e}")
                # Continue to next user instead of stopping
                continue
        
        # Send confirmation to admin
        confirmation_text = f"""
✅ <b>تم إرسال الرسالة الإذاعية بنجاح!</b>

📊 <b>الإحصائيات:</b>
• تم الإرسال بنجاح: {sent_count} مستخدم
• فشل الإرسال: {failed_count} مستخدم
• إجمالي المحاولات: {sent_count + failed_count}

📅 <b>وقت الإرسال:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 <b>نوع الرسالة:</b> نص فقط
"""
        
        await update.message.reply_text(confirmation_text, parse_mode='HTML')
        
        context.user_data.clear()
        
        logger.info(f"Broadcast message sent to {sent_count} users, failed for {failed_count} users")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_message: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء إرسال الرسالة الإذاعية. يرجى المحاولة مرة أخرى أو التواصل مع المطور."
        )
        return ConversationHandler.END

async def handle_broadcast_image(update: Update, context: CallbackContext) -> int:
    """Handle broadcast image input with improved error handling."""
    try:
        if not update.message.photo:
            await update.message.reply_text(
                "⚠️ يرجى إرسال صورة صالحة.\n\n"
                "💡 يمكنك إضافة نص مع الصورة كتعليق"
            )
            return ASKING_BROADCAST_IMAGE
        
        # Save the image
        photo = update.message.photo[-1]  # Get highest resolution
        file_path = await save_media_file(photo, "photo", update.effective_user.id)
        
        if not file_path:
            await update.message.reply_text("❌ فشل في حفظ الصورة. يرجى المحاولة مرة أخرى.")
            return ASKING_BROADCAST_IMAGE
        
        # Store image info
        context.user_data['broadcast_image_path'] = file_path
        context.user_data['broadcast_caption'] = update.message.caption or ""
        
        # Get all users
        all_users = data_manager.get_all_users()
        
        if not all_users:
            await update.message.reply_text("❌ لا يوجد مستخدمين لإرسال الرسالة إليهم.")
            return ConversationHandler.END
        
        # Send broadcast image with improved error handling
        sent_count = 0
        failed_count = 0
        
        # Prepare caption
        caption = context.user_data['broadcast_caption']
        if caption:
            formatted_caption = f"""
📢 <b>رسالة من فريق Our Goal</b>

{caption}

---
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            formatted_caption = f"""
📢 <b>رسالة من فريق Our Goal</b>

---
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send to all users with individual error handling
        for user_id in all_users:
            try:
                with open(file_path, 'rb') as photo_file:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=photo_file,
                        caption=formatted_caption,
                        parse_mode='HTML'
                    )
                sent_count += 1
                logger.info(f"Broadcast image sent successfully to user {user_id}")
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast image to user {user_id}: {e}")
                # Continue to next user instead of stopping
                continue
        
        # Send confirmation to admin
        confirmation_text = f"""
✅ <b>تم إرسال الرسالة الإذاعية بالصورة بنجاح!</b>

📊 <b>الإحصائيات:</b>
• تم الإرسال بنجاح: {sent_count} مستخدم
• فشل الإرسال: {failed_count} مستخدم
• إجمالي المحاولات: {sent_count + failed_count}

📅 <b>وقت الإرسال:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🖼️ <b>نوع الرسالة:</b> صورة مع نص
"""
        
        await update.message.reply_text(confirmation_text, parse_mode='HTML')
        
        # Clean up
        try:
            os.remove(file_path)
        except:
            pass
        
        context.user_data.clear()
        
        logger.info(f"Broadcast image sent to {sent_count} users, failed for {failed_count} users")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_image: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء إرسال الرسالة الإذاعية بالصورة. يرجى المحاولة مرة أخرى أو التواصل مع المطور."
        )
        return ConversationHandler.END

# Enhanced media handling functions
async def save_media_file(file, media_type: str, user_id: int) -> str:
    """Save media file and return the file path."""
    try:
        # Get file info
        file_info = await file.get_file()
        
        # Determine file extension
        file_extension = os.path.splitext(file_info.file_path)[1]
        if not file_extension:
            if media_type == "photo":
                file_extension = ".jpg"
            elif media_type == "video":
                file_extension = ".mp4"
            elif media_type == "audio":
                file_extension = ".ogg"
            elif media_type == "voice":
                file_extension = ".ogg"
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}{file_extension}"
        
        # Determine directory based on media type
        if media_type == "photo":
            directory = IMAGES_DIR
        elif media_type == "video":
            directory = VIDEOS_DIR
        elif media_type in ["audio", "voice"]:
            directory = AUDIO_DIR
        else:
            directory = MEDIA_DIR
        
        # Full file path
        file_path = os.path.join(directory, filename)
        
        # Download and save file
        await file_info.download_to_drive(file_path)
        
        logger.info(f"Media file saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save media file: {e}")
        return None

async def cancel_command(update: Update, context: CallbackContext) -> int:
    """Handle /cancel command - cancel current conversation."""
    try:
        await update.message.reply_text(CANCEL_MESSAGE)
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in cancel_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_admin_decision(update: Update, context: CallbackContext) -> None:
    """Handle admin decision buttons (accept/reject)."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Parse callback data: accept_user_id_team_id_team_name or reject_user_id_team_id_team_name
        callback_parts = query.data.split("_", 3)  # Split into max 4 parts
        decision = callback_parts[0]  # accept or reject
        user_id = int(callback_parts[1])
        team_id = callback_parts[2]
        
        # Extract team_name (might contain underscores)
        team_name = "غير معروف"
        if len(callback_parts) > 3:
            team_name = callback_parts[3]
        else:
            # Fallback: try to get team name from TEAMS dict or user applications
            team_name = TEAMS.get(team_id, "غير معروف")
            
            # If still not found, search in user applications
            if team_name == "غير معروف":
                user_applications = data_manager.get_user_applications(user_id)
                for app in user_applications:
                    if app.get('selected_team') == team_id:
                        team_name = app.get('team_name', 'غير معروف')
                        break
                
                # If still not found, search in all applications
                if not team_name or team_name == "غير معروف":
                    all_applications = data_manager.applications
                    for app in all_applications:
                        if (app.get('user_info', {}).get('user_id') == user_id and 
                            app.get('selected_team') == team_id):
                            team_name = app.get('team_name', 'غير معروف')
                            break
            
            # If still not found, use a fallback based on team_id
            if not team_name or team_name == "غير معروف":
                team_name_map = {
                    "team_exams": "تيم الاختبارات",
                    "team_collections": "تيم التجميعات", 
                    "team_support": "تيم الدعم الفني"
                }
                team_name = team_name_map.get(team_id, f"التيم ({team_id})")
        
        # Get admin info
        admin_name = query.from_user.first_name
        if query.from_user.last_name:
            admin_name += f" {query.from_user.last_name}"
        
        # Prepare message based on decision
        if decision == "accept":
            user_message = f"""
🎉 <b>تهانينا! تم قبول طلبك</b>

مرحباً بك في {team_name}! 🎯

تم قبول طلبك للانضمام لفريقنا. نحن متحمسون لوجودك معنا!

سيتم التواصل معك قريباً من قبل مسؤول الفريق لإعطائك التفاصيل والخطوات التالية.

نتطلع للعمل معك! 🤝

---
✅ <b>تم الموافقة بواسطة:</b> {admin_name}
📅 <b>تاريخ القبول:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            admin_confirmation = f"✅ تم قبول المتقدم في {team_name} وإرسال رسالة التهنئة"
        else:
            user_message = f"""
📝 <b>شكراً لك على اهتمامك</b>

نشكرك على تقديمك للانضمام لـ {team_name}.

للأسف، لم نتمكن من قبول طلبك في الوقت الحالي. هذا لا يعني أن طلبك لم يكن جيداً، لكن لدينا عدد محدود من الأماكن المتاحة.

نشجعك على المحاولة مرة أخرى في المستقبل أو التقديم لفريق آخر.

شكراً لك مرة أخرى!

---
❌ <b>تم الرفض بواسطة:</b> {admin_name}
📅 <b>تاريخ الرد:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            admin_confirmation = f"❌ تم رفض المتقدم من {team_name} وإرسال رسالة مهذبة"
        
        # Send message to user
        await context.bot.send_message(
            chat_id=user_id,
            text=user_message,
            parse_mode='HTML'
        )
        
        # Update admin message to show decision was made
        original_text = query.message.text
        updated_text = f"{original_text}\n\n{admin_confirmation}"
        
        await query.edit_message_text(
            text=updated_text,
            parse_mode='HTML'
        )
        
        logger.info(f"Admin decision: {decision} for user {user_id} in team {team_name} by {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to handle admin decision: {e}")
        await query.answer("حدث خطأ في معالجة القرار", show_alert=True)

async def clear_applications_command(update: Update, context: CallbackContext) -> None:
    """Handle /clear command - clear all applications (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text("⚠️ هذا الأمر مخصص للإدارة فقط")
            return
        
        # Clear all applications
        if data_manager.clear_all_applications():
            await update.message.reply_text("✅ تم مسح جميع التقديمات بنجاح!")
            logger.info(f"All applications cleared by admin {update.effective_user.id}")
        else:
            await update.message.reply_text("❌ فشل في مسح التقديمات")
        
    except Exception as e:
        logger.error(f"Error in clear_applications_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE)

async def ban_command(update: Update, context: CallbackContext) -> None:
    """Handle /ban command - ban a user (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text("⚠️ هذا الأمر مخصص للإدارة فقط")
            return
        
        # Check if user ID is provided
        if not context.args:
            await update.message.reply_text("⚠️ يرجى تحديد معرف المستخدم\n\nمثال: /ban 123456789")
            return
        
        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⚠️ معرف المستخدم يجب أن يكون رقماً")
            return
        
        # Ban the user
        if data_manager.ban_user(user_id):
            await update.message.reply_text(f"✅ تم حظر المستخدم {user_id} بنجاح")
            logger.info(f"User {user_id} banned by admin {update.effective_user.id}")
        else:
            await update.message.reply_text("❌ فشل في حظر المستخدم")
        
    except Exception as e:
        logger.error(f"Error in ban_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE)

async def unban_command(update: Update, context: CallbackContext) -> None:
    """Handle /unban command - unban a user (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text("⚠️ هذا الأمر مخصص للإدارة فقط")
            return
        
        # Check if user ID is provided
        if not context.args:
            await update.message.reply_text("⚠️ يرجى تحديد معرف المستخدم\n\nمثال: /unban 123456789")
            return
        
        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("⚠️ معرف المستخدم يجب أن يكون رقماً")
            return
        
        # Unban the user
        if data_manager.unban_user(user_id):
            await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {user_id} بنجاح")
            logger.info(f"User {user_id} unbanned by admin {update.effective_user.id}")
        else:
            await update.message.reply_text("❌ فشل في إلغاء حظر المستخدم")
        
    except Exception as e:
        logger.error(f"Error in unban_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE)

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Handle admin text replies to user applications."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            return
        
        # Check if this is a reply to a bot message
        if not update.message.reply_to_message:
            return
        
        replied_message_id = update.message.reply_to_message.message_id
        
        # Check if we have a mapping for this message
        if replied_message_id not in admin_message_to_user:
            return
        
        # Get the original user ID
        user_id = admin_message_to_user[replied_message_id]
        
        # Get admin info
        admin_name = update.effective_user.first_name
        if update.effective_user.last_name:
            admin_name += f" {update.effective_user.last_name}"
        
        # Prepare reply message
        reply_text = f"""
📩 <b>رد من فريق Our Goal:</b>

{update.message.text}

---
📅 <b>وقت الرد:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 <b>يمكنك الرد على هذه الرسالة وسيتم توصيلها للإدارة</b>
"""
        
        # Send reply to the original user
        await context.bot.send_message(
            chat_id=user_id,
            text=reply_text,
            parse_mode='HTML'
        )
        
        # React to the admin message to show it was sent
        await update.message.reply_text("✅ تم إرسال الرد للمتقدم بنجاح")
        
        logger.info(f"Admin reply sent from {update.effective_user.id} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send admin reply: {e}")
        await update.message.reply_text("❌ فشل في إرسال الرد للمتقدم")

async def handle_end_conversation(update: Update, context: CallbackContext) -> None:
    """Handle end conversation button."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Parse callback data: end_chat_user_id
        user_id = int(query.data.split("_")[2])
        
        # Remove from active conversations
        if user_id in active_conversations:
            del active_conversations[user_id]
        
        # Update the message
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ تم إنهاء المحادثة مع المستخدم {user_id}"
        )
        
        # Notify user
        await context.bot.send_message(
            chat_id=user_id,
            text="📝 تم إنهاء المحادثة مع الإدارة. شكراً لك!"
        )
        
        logger.info(f"Conversation ended with user {user_id} by admin {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        await query.answer("حدث خطأ في إنهاء المحادثة", show_alert=True)

async def handle_unknown_message(update: Update, context: CallbackContext) -> None:
    """Handle unknown text messages."""
    try:
        await update.message.reply_text(UNKNOWN_MESSAGE, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in handle_unknown_message: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

# Media handlers for users (placeholder functions)
async def handle_user_photo(update: Update, context: CallbackContext) -> None:
    """Handle photo messages from users."""
    pass

async def handle_user_video(update: Update, context: CallbackContext) -> None:
    """Handle video messages from users."""
    pass

async def handle_user_audio(update: Update, context: CallbackContext) -> None:
    """Handle audio messages from users."""
    pass

# Media handlers for admins (placeholder functions)
async def handle_admin_photo(update: Update, context: CallbackContext) -> None:
    """Handle photo messages from admin."""
    pass

async def handle_admin_video(update: Update, context: CallbackContext) -> None:
    """Handle video messages from admin."""
    pass

async def handle_admin_audio(update: Update, context: CallbackContext) -> None:
    """Handle audio messages from admin."""
    pass

