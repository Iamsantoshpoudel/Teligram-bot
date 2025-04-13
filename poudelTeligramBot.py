import os
import logging
import atexit
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# === CONFIGURATION ===
OPENROUTER_API_KEY = "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"
BOT_TOKEN = "7819848211:AAHZpkgaEmKKYHAu7gXvZ2pAmlKqtCZuPgo"
MODEL_NAME = "meta-llama/llama-4-maverick:free"
# ======================

# === SINGLE INSTANCE LOCK ===
pid_file = "bot.pid"
if os.path.exists(pid_file):
    print("Bot is already running! Exiting.")
    exit()
else:
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

@atexit.register
def cleanup():
    if os.path.exists(pid_file):
        os.remove(pid_file)
# =============================

# === LOGGING SETUP ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Hide polling spam
# ======================

# === OpenRouter CLIENT ===
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
# ==========================

# === AI REPLY FUNCTION ===
def ai_reply(message_text):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": message_text}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error("AI reply failed: %s", e)
        return "⚠️ Sorry, I couldn't generate a reply right now."
# =========================

# === TELEGRAM BOT HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Hello! I’m your AI assistant. Type anything and I’ll respond!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_msg = update.message.text
        logger.info(f"Message from {update.effective_user.first_name}: {user_msg}")
        response = ai_reply(user_msg)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error("Message handler error: %s", e)
        await update.message.reply_text("Something went wrong. Try again later.")
# ==============================

# === MAIN BOT FUNCTION ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
# ==========================

if __name__ == "__main__":
    main()
