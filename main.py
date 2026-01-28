import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Contact
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from dotenv import load_dotenv

# فعال‌سازی لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل کانورسیشن
REQUEST_CONTACT, PROCESS_CONTACTS = range(2)

class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.application = Application.builder().token(self.TOKEN).build()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ربات و درخواست دسترسی به مخاطبین"""
        user = update.effective_user
        
        # ایجاد دکمه برای اشتراک‌گذاری مخاطب
        keyboard = [
            [KeyboardButton("📞 اشتراک‌گذاری مخاطبین", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await update.message.reply_text(
            f"سلام {user.first_name}! 👋\n\n"
            "برای استفاده از قابلیت‌های ربات، لطفاً دسترسی به مخاطبین را اجازه دهید.\n"
            "روی دکمه زیر کلیک کنید:",
            reply_markup=reply_markup
        )
        
        return REQUEST_CONTACT
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت مخاطب از کاربر"""
        contact = update.message.contact
        
        if contact:
            # ذخیره اطلاعات مخاطب
            contact_info = {
                'phone_number': contact.phone_number,
                'first_name': contact.first_name,
                'last_name': contact.last_name if contact.last_name else '',
                'user_id': contact.user_id
            }
            
            # ذخیره در context
            if 'contacts' not in context.user_data:
                context.user_data['contacts'] = []
            context.user_data['contacts'].append(contact_info)
            
            # پرسش برای ادامه
            keyboard = [
                ["✅ ارسال مخاطب دیگر"],
                ["⏹️ پایان و مشاهده مخاطبین"]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await update.message.reply_text(
                f"✅ مخاطب {contact.first_name} ذخیره شد.\n"
                "آیا مخاطب دیگری دارید؟",
                reply_markup=reply_markup
            )
            
            return PROCESS_CONTACTS
    
    async def process_contacts_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش انتخاب کاربر"""
        choice = update.message.text
        
        if choice == "✅ ارسال مخاطب دیگر":
            # بازگشت به مرحله دریافت مخاطب
            keyboard = [
                [KeyboardButton("📞 اشتراک‌گذاری مخاطب", request_contact=True)]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await update.message.reply_text(
                "لطفاً مخاطب بعدی را ارسال کنید:",
                reply_markup=reply_markup
            )
            return REQUEST_CONTACT
            
        elif choice == "⏹️ پایان و مشاهده مخاطبین":
            # نمایش همه مخاطبین
            contacts = context.user_data.get('contacts', [])
            
            if not contacts:
                await update.message.reply_text(
                    "هنوز هیچ مخاطبی ذخیره نکرده‌اید.",
                    reply_markup=None
                )
            else:
                # ارسال هر مخاطب به صورت جداگانه
                await update.message.reply_text(
                    f"📞 شما {len(contacts)} مخاطب دارید:\n"
                    "────────────────────"
                )
                
                for i, contact in enumerate(contacts, 1):
                    contact_message = (
                        f"{i}. 👤 **{contact['first_name']}**\n"
                        f"   📱: `{contact['phone_number']}`"
                    )
                    if contact['last_name']:
                        contact_message += f"\n   👥: {contact['last_name']}"
                    
                    await update.message.reply_text(
                        contact_message,
                        parse_mode='Markdown'
                    )
                
                # دکمه‌های عملیاتی
                keyboard = [
                    ["🔄 شروع مجدد"],
                    ["📤 خروج"]
                ]
                reply_markup = ReplyKeyboardMarkup(
                    keyboard, 
                    resize_keyboard=True
                )
                
                await update.message.reply_text(
                    "چه کاری انجام دهیم؟",
                    reply_markup=reply_markup
                )
            
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text(
            "عملیات لغو شد.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش راهنما"""
        help_text = """
        🚀 **دستورات ربات:**
        
        /start - شروع ربات و درخواست مخاطبین
        /help - نمایش این راهنما
        /contacts - مشاهده مخاطبین ذخیره شده
        
        🔧 **نحوه استفاده:**
        1. روی /start کلیک کنید
        2. دکمه "اشتراک‌گذاری مخاطبین" را بزنید
        3. مخاطبین خود را یک‌به‌یک ارسال کنید
        4. در پایان همه مخاطبین را مشاهده کنید
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def show_saved_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش مخاطبین ذخیره شده"""
        contacts = context.user_data.get('contacts', [])
        
        if not contacts:
            await update.message.reply_text("📭 هنوز هیچ مخاطبی ذخیره نکرده‌اید.")
        else:
            await update.message.reply_text(f"📖 شما {len(contacts)} مخاطب ذخیره کرده‌اید.")
            for contact in contacts:
                await update.message.reply_text(
                    f"👤 {contact['first_name']}\n📱 {contact['phone_number']}"
                )
    
    def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        
        # کانورسیشن هندلر برای دریافت مخاطبین
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                REQUEST_CONTACT: [
                    MessageHandler(filters.CONTACT, self.handle_contact)
                ],
                PROCESS_CONTACTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_contacts_choice)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # ثبت هندلرها
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.show_help))
        self.application.add_handler(CommandHandler("contacts", self.show_saved_contacts))
    
    def run(self):
        """اجرای ربات"""
        self.setup_handlers()
        
        # روی رندر از وب هوک استفاده می‌کنیم
        PORT = int(os.environ.get('PORT', 8443))
        WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
        
        if WEBHOOK_URL:
            # تنظیم وب هوک برای رندر
            self.application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=self.TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{self.TOKEN}"
            )
        else:
            # اجرای محلی با polling
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
