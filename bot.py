import os
import asyncio
import logging
from datetime import datetime
import pytz
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.environ.get("CHAT_ID", "")  # Will be set after /start

# IST Timezone
IST = pytz.timezone("Asia/Kolkata")

# ── Menu Data ──────────────────────────────────────────────────────────────────
# Each index = day of week (0=Monday ... 6=Sunday)
LUNCH_MENU = [
    {  # Monday
        "sabji":     {"name": "पालक पनीर",          "yt": "https://youtube.com/results?search_query=palak+paneer+recipe+marathi"},
        "dry_sabji": {"name": "बटाटा भाजी",          "yt": "https://youtube.com/results?search_query=batata+bhaji+recipe+marathi"},
    },
    {  # Tuesday
        "sabji":     {"name": "छोले मसाला",           "yt": "https://youtube.com/results?search_query=chole+masala+recipe+marathi"},
        "dry_sabji": {"name": "कोबी भाजी",            "yt": "https://youtube.com/results?search_query=kobi+bhaji+marathi"},
    },
    {  # Wednesday
        "sabji":     {"name": "राजमा करी",            "yt": "https://youtube.com/results?search_query=rajma+curry+recipe+marathi"},
        "dry_sabji": {"name": "गाजर मटार भाजी",       "yt": "https://youtube.com/results?search_query=gajar+matar+bhaji+marathi"},
    },
    {  # Thursday
        "sabji":     {"name": "मटर टोमॅटो रस्सा",     "yt": "https://youtube.com/results?search_query=matar+tomato+rassa+marathi"},
        "dry_sabji": {"name": "वांगी भरीत",           "yt": "https://youtube.com/results?search_query=vangi+bharit+marathi"},
    },
    {  # Friday
        "sabji":     {"name": "दाळ पालक",             "yt": "https://youtube.com/results?search_query=dal+palak+recipe+marathi"},
        "dry_sabji": {"name": "शेवग्याची शेंग भाजी",  "yt": "https://youtube.com/results?search_query=shevgyachi+bhaji+marathi"},
    },
    {  # Saturday
        "sabji":     {"name": "कडधान्य आमटी",          "yt": "https://youtube.com/results?search_query=kaddhanya+aamti+marathi"},
        "dry_sabji": {"name": "फ्लॉवर भाजी",           "yt": "https://youtube.com/results?search_query=flower+bhaji+marathi"},
    },
    {  # Sunday
        "sabji":     {"name": "पनीर मसाला",            "yt": "https://youtube.com/results?search_query=paneer+masala+recipe+marathi"},
        "dry_sabji": {"name": "बटाटा सिमला मिरची",     "yt": "https://youtube.com/results?search_query=aloo+shimla+mirch+marathi"},
    },
]

DINNER_MENU = [
    {  # Monday
        "sabji":     {"name": "मिक्स भाज्यांचा रस्सा", "yt": "https://youtube.com/results?search_query=mix+veg+curry+marathi"},
        "dry_sabji": {"name": "मेथी भाजी",              "yt": "https://youtube.com/results?search_query=methi+bhaji+marathi"},
    },
    {  # Tuesday
        "sabji":     {"name": "सोयाबीन करी",            "yt": "https://youtube.com/results?search_query=soyabean+curry+marathi"},
        "dry_sabji": {"name": "बटाटा कांदा भाजी",       "yt": "https://youtube.com/results?search_query=batata+kanda+bhaji+marathi"},
    },
    {  # Wednesday
        "sabji":     {"name": "छोले पालक",              "yt": "https://youtube.com/results?search_query=chhole+palak+marathi"},
        "dry_sabji": {"name": "भेंडी भाजी",              "yt": "https://youtube.com/results?search_query=bhendi+bhaji+marathi"},
    },
    {  # Thursday
        "sabji":     {"name": "मशरूम करी",              "yt": "https://youtube.com/results?search_query=mushroom+curry+marathi"},
        "dry_sabji": {"name": "कांदा टोमॅटो भाजी",      "yt": "https://youtube.com/results?search_query=kanda+tomato+bhaji+marathi"},
    },
    {  # Friday
        "sabji":     {"name": "वाटाणा करी",              "yt": "https://youtube.com/results?search_query=vatana+curry+marathi"},
        "dry_sabji": {"name": "दुधी भाजी",               "yt": "https://youtube.com/results?search_query=dudhi+bhaji+marathi"},
    },
    {  # Saturday
        "sabji":     {"name": "मूग डाळ करी",             "yt": "https://youtube.com/results?search_query=moong+dal+curry+marathi"},
        "dry_sabji": {"name": "शेपू भाजी",               "yt": "https://youtube.com/results?search_query=shepu+bhaji+marathi"},
    },
    {  # Sunday
        "sabji":     {"name": "टोमॅटो सार",              "yt": "https://youtube.com/results?search_query=tomato+saar+marathi"},
        "dry_sabji": {"name": "पापडी भाजी",              "yt": "https://youtube.com/results?search_query=papdi+bhaji+marathi"},
    },
]

DAYS_MR = ["सोमवार", "मंगळवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]

# ── Message Builder ────────────────────────────────────────────────────────────
def build_message():
    now = datetime.now(IST)
    day_idx = now.weekday()  # 0=Monday, 6=Sunday
    day_name = DAYS_MR[day_idx]
    date_str = now.strftime("%d/%m/%Y")

    l = LUNCH_MENU[day_idx]
    d = DINNER_MENU[day_idx]

    msg = f"""🍽️ *आजचे जेवण - {day_name} ({date_str})*
━━━━━━━━━━━━━━━━━━━

🌞 *दुपारचे जेवण*
• चपाती / भात / डाळ / कढी
• 🥘 सब्जी: *{l['sabji']['name']}*
  📹 [रेसिपी पाहा]({l['sabji']['yt']})
• 🥬 कोरडी भाजी: *{l['dry_sabji']['name']}*
  📹 [रेसिपी पाहा]({l['dry_sabji']['yt']})

━━━━━━━━━━━━━━━━━━━
🌙 *रात्रीचे जेवण*
• चपाती / भात / डाळ / कढी
• 🥘 सब्जी: *{d['sabji']['name']}*
  📹 [रेसिपी पाहा]({d['sabji']['yt']})
• 🥬 कोरडी भाजी: *{d['dry_sabji']['name']}*
  📹 [रेसिपी पाहा]({d['dry_sabji']['yt']})

━━━━━━━━━━━━━━━━━━━
✅ _सर्व साहित्य सहज मिळते. स्वयंपाक सुरू करण्यापूर्वी एकदा रेसिपी नक्की पाहा!_ 🙏"""
    return msg

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ Bot सुरू झाला!\n\n"
        f"तुमचा Chat ID: `{chat_id}`\n\n"
        f"हा Chat ID CHAT_ID environment variable मध्ये टाका.\n"
        f"रोज सकाळी ८ वाजता आजचे मेनू मिळेल! 🍽️",
        parse_mode="Markdown"
    )

async def today(update, context: ContextTypes.DEFAULT_TYPE):
    msg = build_message()
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

# ── Scheduler Job ──────────────────────────────────────────────────────────────
async def send_daily_menu(bot: Bot):
    if not CHAT_ID:
        logging.warning("CHAT_ID not set! Use /start to get it.")
        return
    msg = build_message()
    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    logging.info(f"Daily menu sent at {datetime.now(IST)}")

# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))

    scheduler = AsyncIOScheduler(timezone=IST)
    scheduler.add_job(
        send_daily_menu,
        trigger="cron",
        hour=8,
        minute=0,
        args=[app.bot]
    )
    scheduler.start()

    logging.info("Bot started. Waiting for messages...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
