import requests
import io
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8379242623:AAHhaMkyNLJgwwV0roeVkMNrU4QShh0M9t8"
HUGGING_FACE_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# --- STATES ---
ASK_NAME, ASK_PHONE, ASK_OTP, ASK_PROMPT = range(4)

# --- IMAGE GENERATION FUNCTION ---
def generate_image(prompt: str) -> bytes | None:
    headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error from API: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# --- TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Please enter your name:")
    return ASK_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📱 Please enter your 10-digit mobile number:")
    return ASK_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not (phone.isdigit() and len(phone) == 10):
        await update.message.reply_text("❌ Invalid! Please enter a valid 10-digit number:")
        return ASK_PHONE

    context.user_data["phone"] = phone

    # Generate OTP
    otp = str(random.randint(1000, 9999))
    context.user_data["otp"] = otp

    # Print to your terminal
    print(f"[NEW USER] Name: {context.user_data['name']}, Phone: {phone}, OTP: {otp}")

    # Send OTP to user
    await update.message.reply_text(f"🔑 Your OTP is: {otp}\nPlease type it here to verify.")
    return ASK_OTP

async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entered = update.message.text.strip()
    if entered == context.user_data.get("otp"):
        await update.message.reply_text("✅ OTP Verified! Now send me a description of the image you want 🖼️")
        return ASK_PROMPT
    else:
        await update.message.reply_text("❌ Incorrect OTP. Try again:")
        return ASK_OTP

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text.strip()
    if not user_prompt:
        return

    await update.message.reply_text("🎨 Generating your image, please wait...")

    image_bytes = generate_image(user_prompt)

    if image_bytes:
        photo_file = io.BytesIO(image_bytes)
        await update.message.reply_photo(photo=photo_file, caption=f"Here is your image for: '{user_prompt}'")
    else:
        await update.message.reply_text(
            "😥 Sorry, I couldn't create an image.\nPlease try again later."
        )
    return ASK_PROMPT  # Stay in prompt state so user can generate more

# --- MAIN FUNCTION TO RUN THE BOT ---
def main():
    print("Bot is starting...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ASK_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_otp)],
            ASK_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()
    print("Bot has stopped.")

if __name__ == "__main__":
    main()


