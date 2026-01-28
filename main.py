import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل مکالمه
REQUEST_CONTACT = 0

class TelegramBot:
    def __init__(self):
        # خواندن توکن از متغیر محیطی
        self.TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not self.TOKEN:
            logger.error("❌ TOKEN not found! Set TELEGRAM_BOT_TOKEN in environment variables.")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        # ساخت اپلیکیشن
        try:
            self.application = Application.builder().token(self.TOKEN).build()
            logger.info("✅ Application created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create application: {e}")
            raise
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ربات"""
        user = update.effective_user
        
        # ایجاد دکمه برای اشتراک‌گذاری مخاطب
        keyboard = [
            [KeyboardButton("📞 اشتراک‌گذاری مخاطب", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await update.message.reply_text(
            f"سلام {user.first_name}! 👋\n\n"
            "برای شروع، لطفاً یک مخاطب به اشتراک بگذارید:",
            reply_markup=reply_markup
        )
        
        return REQUEST_CONTACT
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت مخاطب"""
        contact = update.message.contact
        
        if contact:
            await update.message.reply_text(
                f"✅ مخاطب دریافت شد:\n"
                f"👤 نام: {contact.first_name}\n"
                f"📱 شماره: {contact.phone_number}"
            )
        
        # بازگرداندن به حالت عادی
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات"""
        await update.message.reply_text("عملیات لغو شد.")
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور help"""
        await update.message.reply_text(
            "📚 راهنما:\n"
            "/start - شروع ربات\n"
            "/help - نمایش این راهنما\n"
            "از دکمه 'اشتراک‌گذاری مخاطب' استفاده کنید."
        )
    
    def setup_handlers(self):
        """تنظیم هندلرها"""
        
        # مکالمه برای دریافت مخاطب
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                REQUEST_CONTACT: [
                    MessageHandler(filters.CONTACT, self.handle_contact)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        logger.info("✅ Handlers setup completed")
    
    def run(self):
        """اجرای ربات"""
        self.setup_handlers()
        
        # تنظیمات پورت برای رندر
        port = int(os.environ.get('PORT', 8443))
        webhook_url = os.environ.get('WEBHOOK_URL', '')
        
        if webhook_url:
            # استفاده از وب‌هوک در رندر
            logger.info(f"🌐 Using webhook: {webhook_url}")
            
            async def webhook_mode():
                await self.application.initialize()
                await self.application.bot.set_webhook(
                    url=f"{webhook_url}/{self.TOKEN}",
                    allowed_updates=Update.ALL_TYPES
                )
                await self.application.start()
                
                # نگه داشتن برنامه فعال
                import asyncio
                await asyncio.Event().wait()
            
            import asyncio
            asyncio.run(webhook_mode())
        else:
            # حالت توسعه (polling)
            logger.info("🔄 Using polling mode")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )

# نقطه ورود اصلی
if __name__ == '__main__':
    try:
        logger.info("🚀 Starting Telegram Bot...")
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
