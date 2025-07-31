#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0"))

# Conversation states
ASKING_GENDER = 1
ASKING_REASON = 2
ASKING_EXPERIENCE = 3
ASKING_WHATSAPP = 4

# Team definitions
TEAMS = {
    "team_exams": "تيم الاختبارات",
    "team_collections": "تيم التجميعات", 
    "team_support": "تيم الدعم الفني"
}

# Data files
APPLICATIONS_FILE = "applications.json"
USERS_FILE = "users.json"
STATS_FILE = "stats.json"

# Bot settings
BOT_NAME = "Our Goal Bot Enhanced"
BOT_VERSION = "2.1"
BOT_DESCRIPTION = "بوت التقديم لتيمز Our Goal مع دعم الوسائط المتعددة"

# Rate limiting settings
MAX_APPLICATIONS_PER_USER = 4  # Maximum applications per user (one per team)
COOLDOWN_HOURS = 24  # Hours to wait before reapplying to same team

# Media settings
MAX_FILE_SIZE_MB = 50  # Maximum file size in MB
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Messages in Arabic (Egyptian dialect)
WELCOME_MESSAGE = """
مرحباً بك في بوت التقديم لتيمز Our Goal! 🎯

يسعدنا إنك حابب تكون جزء من فريقنا وتشاركنا في تحقيق النجاح.

اختار التيم اللي حابب تنضم له من الأزرار اللي تحت:

💡 <b>نصيحة:</b> يمكنك استخدام /menu لعرض القائمة الرئيسية في أي وقت

🆕 <b>جديد:</b> يمكنك الآن التفاعل مع الإدارة بالصور والفيديو والصوت!
"""

TEAM_SELECTION_MESSAGE = """
ممتاز! اختارك لـ {team_name} 👏

عشان نقدر نقيم طلبك بشكل أفضل، محتاجين نسألك كام سؤال:

السؤال الأول: ما هو جنسك؟ 
اختر من الأزرار اللي تحت:
"""

GENDER_QUESTION = """
شكراً لإجابتك!

السؤال التاني: ليه عايز تنضم لـ {team_name}؟ 
إيه اللي خلاك تختار التيم دا تحديداً؟

"""

EXPERIENCE_QUESTION = """
شكراً لإجابتك!

السؤال الثالث: عندك أي خبرة أو مهارات متعلقة بشغل {team_name}؟

لو عندك خبرة، اكتب عنها بالتفصيل.
"""

WHATSAPP_QUESTION = """
السؤال الأخير: الرجاء كتابة رقم الواتساب الخاص بك 📱

نحتاج رقم الواتساب للتواصل معك بسبب عدم وجود اسم مستخدم (username) في حسابك على تليجرام.

يرجى كتابة الرقم بالتنسيق التالي:
🇪🇬 مصر: +201234567890 أو 01234567890
🇸🇦 السعودية: +966512345678 أو 0512345678

⚠️ تأكد من صحة الرقم لأنه سيتم استخدامه للتواصل معك!
"""

APPLICATION_SUBMITTED = """
تم تسليم طلبك بنجاح! 🎉

شكراً ليك على اهتمامك بالانضمام لـ {team_name}. 
هيتم مراجعة طلبك وهنرد عليك قريباً إن شاء الله.

نتمنى نشوفك معانا في التيم! 🤝

يمكنك الضغط على /start للتقديم على تيم تاني لو عايز.

📱 <b>ملاحظة:</b> يمكنك الآن إرسال صور وفيديوهات ورسائل صوتية للإدارة!
"""

ALREADY_APPLIED = """
أنت قدمت على {team_name} قبل كدا! 😊

يمكنك الضغط على /start لتقديم على تيم تاني.
"""

CANCEL_MESSAGE = """
تم إلغاء طلب التقديم. 

يمكنك الضغط على /start للبدء من جديد.
"""

UNKNOWN_MESSAGE = """
مرحبا بك في Our Goal! 🎯

يمكنك الضغط على /start للبدء من جديد أو /menu لعرض القائمة الرئيسية.

📱 <b>نصيحة:</b> يمكنك إرسال صور وفيديوهات ورسائل صوتية عند التفاعل مع الإدارة!
"""

NO_STATS_PERMISSION = """
معذرة، الأمر دا مخصص للادمن بس.
"""

STATS_HEADER = """
📊 إحصائيات طلبات التقديم

إجمالي الطلبات: {total_applications}
عدد المتقدمين: {total_users}

التفاصيل حسب التيم:
"""

STATS_TEAM_FORMAT = """
🔹 {team_name}: {count} طلب
"""

NO_APPLICATIONS_YET = """
لسه مفيش طلبات تقديم.
"""

# Enhanced messages for media features
HELP_MESSAGE = """
📋 <b>مساعدة - Our Goal Bot Enhanced</b>

🎯 <b>الأوامر المتاحة:</b>

• /start - بدء التقديم للتيمز
• /menu - عرض القائمة الرئيسية
• /help - عرض هذه المساعدة
• /cancel - إلغاء العملية الحالية
• /status - عرض حالة طلباتك

<b>للإدارة فقط:</b>
• /stats - إحصائيات التقديمات
• /clear - مسح جميع التقديمات
• /broadcast - إرسال رسالة جماعية

💡 <b>كيفية الاستخدام:</b>
1. اضغط على /start للبدء
2. اختر التيم المناسب
3. اجب على الأسئلة المطلوبة
4. سيتم إرسال طلبك للإدارة

🔄 يمكنك التقديم على أكثر من تيم

📱 <b>الميزات الجديدة:</b>
• إرسال الصور 📷
• إرسال الفيديوهات 🎥
• إرسال الرسائل الصوتية 🎤
• إرسال الملفات الصوتية 🎵
• تفاعل محسن مع الإدارة

🎯 <b>كيفية استخدام الوسائط:</b>
• بعد التقديم، يمكنك إرسال أي نوع من الوسائط للإدارة
• الإدارة يمكنها الرد عليك بنفس أنواع الوسائط
• جميع الملفات يتم حفظها بشكل آمن
"""

STATUS_MESSAGE = """
📋 <b>حالة طلباتك</b>

👤 <b>المستخدم:</b> {user_name}
🆔 <b>معرف المستخدم:</b> {user_id}

📊 <b>إجمالي الطلبات:</b> {total_applications}

<b>تفاصيل الطلبات:</b>
{applications_list}

💡 يمكنك التقديم على تيمز أخرى باستخدام /start
📱 يمكنك إرسال صور وفيديوهات ورسائل صوتية للإدارة!
"""

BROADCAST_PROMPT = """
📢 <b>إرسال رسالة جماعية</b>

أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:

⚠️ <b>تنبيه:</b> سيتم إرسال الرسالة لجميع المستخدمين الذين تفاعلوا مع البوت

📱 <b>ملاحظة:</b> يمكنك إرسال نص فقط في الرسائل الجماعية
"""

BROADCAST_SENT = """
✅ <b>تم إرسال الرسالة الجماعية بنجاح!</b>

📊 <b>الإحصائيات:</b>
• تم الإرسال لـ {sent_count} مستخدم
• فشل الإرسال لـ {failed_count} مستخدم

📅 <b>وقت الإرسال:</b> {timestamp}
"""

ERROR_MESSAGE = """
❌ <b>حدث خطأ</b>

عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.

إذا استمر الخطأ، يرجى التواصل مع الإدارة.
"""

MAINTENANCE_MESSAGE = """
🔧 <b>البوت تحت الصيانة</b>

عذراً، البوت غير متاح حالياً بسبب أعمال الصيانة.

يرجى المحاولة مرة أخرى لاحقاً.
"""

# New messages for media features
MEDIA_RECEIVED_MESSAGE = """
✅ <b>تم استلام الوسائط بنجاح!</b>

تم إرسال {media_type} للإدارة وسيتم الرد عليك قريباً.

📱 يمكنك إرسال المزيد من الوسائط أو الرسائل النصية.
"""

MEDIA_ERROR_MESSAGE = """
❌ <b>خطأ في الوسائط</b>

عذراً، حدث خطأ أثناء معالجة الملف المرسل.

يرجى التأكد من:
• حجم الملف أقل من {max_size} ميجابايت
• نوع الملف مدعوم
• جودة الاتصال بالإنترنت

يمكنك المحاولة مرة أخرى أو إرسال رسالة نصية.
"""

ADMIN_MEDIA_SENT_MESSAGE = """
✅ <b>تم إرسال الوسائط بنجاح!</b>

تم إرسال {media_type} للمتقدم بنجاح.

يمكنك الاستمرار في المحادثة أو إنهاؤها.
"""

ADMIN_MEDIA_ERROR_MESSAGE = """
❌ <b>فشل في إرسال الوسائط</b>

حدث خطأ أثناء إرسال {media_type} للمتقدم.

يرجى المحاولة مرة أخرى أو إرسال رسالة نصية.
"""

# Media type translations
MEDIA_TYPES = {
    'photo': 'الصورة',
    'video': 'الفيديو', 
    'audio': 'الملف الصوتي',
    'voice': 'الرسالة الصوتية'
}

# File size limits (in bytes)
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB  
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
