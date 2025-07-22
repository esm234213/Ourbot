#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
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

# Conversation states for broadcast
ASKING_BROADCAST_MESSAGE = 10

async def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command - show welcome message and team selection buttons."""
    user = update.effective_user
    
    try:
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
        
        # Ask for reason
        await query.edit_message_text(
            TEAM_SELECTION_MESSAGE.format(team_name=team_name)
        )
        
        logger.info(f"User {user.id} selected team {team_id}")
        return ASKING_REASON
        
    except Exception as e:
        logger.error(f"Error in team_selection_callback: {e}")
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
    """Handle user's experience input and complete application."""
    try:
        user_experience = update.message.text.strip()
        
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
        
        # Prepare application data
        application_data = {
            'user_info': context.user_data['user_info'],
            'selected_team': context.user_data['selected_team'],
            'team_name': context.user_data['team_name'],
            'reason': context.user_data['reason'],
            'experience': user_experience,
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
        logger.error(f"Error in handle_experience_input: {e}")
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
        
        # Create notification message
        notification_text = f"""
🆕 <b>طلب تقديم جديد!</b>

👤 <b>المتقدم:</b> {user_name} {username_text}
🆔 <b>معرف المستخدم:</b> {user_info['user_id']}
🎯 <b>التيم:</b> {application_data['team_name']}

❓ <b>سبب الانضمام:</b>
{application_data['reason']}

💼 <b>الخبرة:</b>
{application_data['experience']}

📅 <b>وقت التقديم:</b> {application_data['timestamp'][:19]}

💬 <b>للرد على المتقدم:</b> رد على هذه الرسالة وسيتم إرسال ردك إليه تلقائياً
"""
        
        # Create inline keyboard with accept/reject buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_info['user_id']}_{application_data['selected_team']}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_info['user_id']}_{application_data['selected_team']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=notification_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        # Store mapping for reply handling
        admin_message_to_user[sent_message.message_id] = user_info['user_id']
        
        logger.info(f"Admin notification sent for application {application_data.get('id', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Handle /stats command - show application statistics (admin only)."""
    try:
        # Check if message is from admin group
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text(NO_STATS_PERMISSION)
            return
        
        # Get statistics
        stats = data_manager.get_statistics()
        
        if stats['total_applications'] == 0:
            await update.message.reply_text(NO_APPLICATIONS_YET)
            return
        
        # Format statistics message
        stats_text = f"""
📊 <b>إحصائيات طلبات التقديم</b>

📈 <b>الإحصائيات العامة:</b>
• إجمالي الطلبات: {stats['total_applications']}
• عدد المتقدمين: {stats['total_users']}
• الطلبات الأخيرة (7 أيام): {stats['recent_applications']}
• المستخدمين النشطين: {stats['active_users']}

🎯 <b>التفاصيل حسب التيم:</b>
"""
        
        for team_id, team_name in TEAMS.items():
            count = stats['team_counts'].get(team_id, 0)
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
        
        await update.message.reply_text(BROADCAST_PROMPT, parse_mode='HTML')
        return ASKING_BROADCAST_MESSAGE
        
    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')
        return ConversationHandler.END

async def handle_broadcast_message(update: Update, context: CallbackContext) -> int:
    """Handle broadcast message input."""
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
        
        # Send broadcast message
        sent_count = 0
        failed_count = 0
        
        # Add header to broadcast message
        formatted_message = f"""
📢 <b>رسالة من فريق Our Goal</b>

{broadcast_text}

---
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        for user_id in all_users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=formatted_message,
                    parse_mode='HTML'
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
                failed_count += 1
        
        # Send confirmation to admin
        confirmation_text = BROADCAST_SENT.format(
            sent_count=sent_count,
            failed_count=failed_count,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        await update.message.reply_text(confirmation_text, parse_mode='HTML')
        
        logger.info(f"Broadcast sent to {sent_count} users, failed for {failed_count} users")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_message: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')
        return ConversationHandler.END

async def clear_applications_command(update: Update, context: CallbackContext) -> None:
    """Handle /clear command - clear all applications (admin only)."""
    try:
        # Check if user is admin
        if update.effective_chat.id != ADMIN_GROUP_ID:
            await update.message.reply_text("⚠️ هذا الأمر مخصص للإدارة فقط")
            return
        
        # Clear applications
        if data_manager.clear_applications():
            await update.message.reply_text("""
🗑️ <b>تم مسح جميع التقديمات بنجاح!</b>

✅ تم مسح جميع التقديمات والبيانات
✅ يمكن للمستخدمين الآن التقديم مرة أخرى
✅ تم إعادة تصفير الإحصائيات
✅ تم إنشاء نسخة احتياطية من البيانات

📊 <b>للتأكد من المسح، يمكنك استخدام الأمر /stats</b>
""", parse_mode='HTML')
            
            logger.info("All applications cleared by admin")
        else:
            await update.message.reply_text("❌ حدث خطأ أثناء مسح التقديمات")
            
    except Exception as e:
        logger.error(f"Error in clear_applications_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE, parse_mode='HTML')

async def cancel_command(update: Update, context: CallbackContext) -> int:
    """Handle /cancel command - cancel current conversation."""
    try:
        context.user_data.clear()
        await update.message.reply_text(CANCEL_MESSAGE)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in cancel_command: {e}")
        await update.message.reply_text(ERROR_MESSAGE)
        return ConversationHandler.END

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Handle admin replies to application notifications."""
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
        
        admin_id = update.effective_user.id
        
        # Start/update conversation tracking
        active_conversations[user_id] = {
            'admin_id': admin_id,
            'admin_name': admin_name,
            'active': True
        }
        
        # Format the reply message
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
        
        logger.info(f"Admin reply sent from {admin_id} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send admin reply: {e}")
        await update.message.reply_text("❌ فشل في إرسال الرد للمتقدم")

async def handle_admin_decision(update: Update, context: CallbackContext) -> None:
    """Handle admin accept/reject button clicks."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Check if message is from admin group
        if query.message.chat.id != ADMIN_GROUP_ID:
            await query.answer("هذا الأمر مخصص للإدارة فقط", show_alert=True)
            return
        
        # Parse callback data
        callback_data = query.data
        if not (callback_data.startswith("accept_") or callback_data.startswith("reject_")):
            return
        
        parts = callback_data.split("_")
        decision = parts[0]  # "accept" or "reject"
        user_id = int(parts[1])
        team_id = parts[2]
        team_name = TEAMS.get(team_id, "غير معروف")
        
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
            admin_confirmation = f"✅ تم قبول المتقدم وإرسال رسالة التهنئة"
        else:
            user_message = f"""
📝 <b>شكراً لك على اهتمامك</b>

نشكرك على تقديمك للانضمام لـ {team_name}.

للأسف، لم نتمكن من قبول طلبك في الوقت الحالي. هذا لا يعني أن طلبك لم يكن جيداً، لكن لدينا عدد محدود من الأماكن المتاحة.

نشجعك على المحاولة مرة أخرى في المستقبل أو التقديم لفريق آخر.

شكراً لك مرة أخرى! 🙏

---
❌ <b>تم الرفض بواسطة:</b> {admin_name}
📅 <b>تاريخ الرد:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            admin_confirmation = f"❌ تم رفض المتقدم وإرسال رسالة مهذبة"
        
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
        
        logger.info(f"Admin decision: {decision} for user {user_id} by {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to handle admin decision: {e}")
        await query.answer("حدث خطأ في معالجة القرار", show_alert=True)

async def handle_user_reply(update: Update, context: CallbackContext) -> None:
    """Handle user replies in active conversations."""
    user_id = update.effective_user.id
    
    try:
        # Check if user has an active conversation
        if user_id not in active_conversations or not active_conversations[user_id]['active']:
            return
        
        conversation = active_conversations[user_id]
        admin_name = conversation['admin_name']
        
        # Get user info
        user_name = update.effective_user.first_name
        if update.effective_user.last_name:
            user_name += f" {update.effective_user.last_name}"
        
        username_text = f"(@{update.effective_user.username})" if update.effective_user.username else "(لا يوجد username)"
        
        # Format message to admin
        admin_message = f"""
💬 <b>رد من المتقدم:</b>

{update.message.text}

---
👤 <b>من:</b> {user_name} {username_text}
🆔 <b>معرف المستخدم:</b> {user_id}
📅 <b>وقت الرد:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send to admin group
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=admin_message,
            parse_mode='HTML'
        )
        
        # Store mapping for potential replies
        admin_message_to_user[sent_message.message_id] = user_id
        
        # Confirm to user
        await update.message.reply_text("✅ تم إرسال رسالتك للإدارة")
        
        logger.info(f"User reply forwarded from {user_id} to admin group")
        
    except Exception as e:
        logger.error(f"Failed to handle user reply: {e}")
        await update.message.reply_text("❌ فشل في إرسال الرسالة")

async def handle_end_conversation(update: Update, context: CallbackContext) -> None:
    """Handle ending conversation between user and admin."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Check if message is from admin group
        if query.message.chat.id != ADMIN_GROUP_ID:
            await query.answer("هذا الأمر مخصص للإدارة فقط", show_alert=True)
            return
        
        # Parse callback data
        if not query.data.startswith("end_chat_"):
            return
        
        user_id = int(query.data.split("_")[2])
        
        # End the conversation
        if user_id in active_conversations:
            active_conversations[user_id]['active'] = False
        
        # Get admin info
        admin_name = query.from_user.first_name
        if query.from_user.last_name:
            admin_name += f" {query.from_user.last_name}"
        
        # Notify user that conversation ended
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
🔚 <b>تم إنهاء المحادثة</b>

تم إنهاء المحادثة من قبل الإدارة.

شكراً لك على تواصلك معنا! 🙏

---
🛑 <b>تم الإنهاء بواسطة:</b> {admin_name}
📅 <b>وقت الإنهاء:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""",
            parse_mode='HTML'
        )
        
        # Update admin message
        await query.edit_message_text(
            text=f"{query.message.text}\n\n🔚 تم إنهاء المحادثة بواسطة {admin_name}",
            parse_mode='HTML'
        )
        
        logger.info(f"Conversation ended between user {user_id} and admin {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        await query.answer("حدث خطأ في إنهاء المحادثة", show_alert=True)

async def handle_unknown_message(update: Update, context: CallbackContext) -> None:
    """Handle unknown messages outside of conversation."""
    user_id = update.effective_user.id
    
    try:
        # Check if user has an active conversation
        if user_id in active_conversations and active_conversations[user_id]['active']:
            await handle_user_reply(update, context)
        else:
            await update.message.reply_text(UNKNOWN_MESSAGE)
            
    except Exception as e:
        logger.error(f"Error in handle_unknown_message: {e}")
        await update.message.reply_text(ERROR_MESSAGE)

