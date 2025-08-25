import os
import json
from telegram import Update, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes, ConversationHandler
)

# ──────────────── CONFIG ────────────────
TOKEN = "TELEGRAM_BOT_TOKENw"   # Replace with your token
ADMIN_ID = CHAT-ID
WHITELIST_FILE = "whitelist.json"

WHITELISTED_IDS = []

if os.path.exists(WHITELIST_FILE):
    with open(WHITELIST_FILE, "r") as f:
        try:
            WHITELISTED_IDS = json.load(f)
        except json.JSONDecodeError:
            WHITELISTED_IDS = []

WAITING_FILE, WAITING_URL, ADMIN_PANEL = range(3)

# ──────────────── START ────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in WHITELISTED_IDS and user_id != ADMIN_ID:
        keyboard = [[InlineKeyboardButton("📞 Contact Owner", url="https://t.me/frenzy_yy")]]
        await update.message.reply_text(
            "⚠️ You are not whitelisted.\nContact the owner to get access.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    if user_id == ADMIN_ID:
        return await admin_panel(update, context)

    keyboard = [
        [InlineKeyboardButton("📂 Upload Combo List", callback_data="upload")],
        [InlineKeyboardButton("📞 Contact Owner", url="https://t.me/frenzy_yy")]
    ]
    await update.message.reply_text(
        "⚡️ //𝐆𝐞𝐧𝐞𝐬𝐢𝐬 𝐀𝐠𝐞𝐧𝐭 Online\n\nWelcome to the Core. Choose your first action:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_FILE

# ──────────────── ADMIN PANEL ────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ View Whitelist", callback_data="view_whitelist")],
        [InlineKeyboardButton("➕ Add Whitelist ID", callback_data="add_whitelist")],
        [InlineKeyboardButton("⛔ Remove ID", callback_data="remove_whitelist")],
        [InlineKeyboardButton("📂 Start Checking", callback_data="start_checking")]
    ]
    await update.message.reply_text(
        "⚡ Admin Panel\nSelect an action:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADMIN_PANEL

# ──────────────── BUTTON HANDLER ────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Admin buttons
    if user_id == ADMIN_ID:
        if query.data == "view_whitelist":
            text = "\n".join([str(uid) for uid in WHITELISTED_IDS]) if WHITELISTED_IDS else "Whitelist empty."
            await query.edit_message_text(f"✅ Current Whitelist:\n{text}")
        elif query.data == "add_whitelist":
            await query.edit_message_text("Send me the user ID to whitelist.")
            context.user_data["admin_action"] = "add"
            return ADMIN_PANEL
        elif query.data == "remove_whitelist":
            await query.edit_message_text("Send me the user ID to remove from whitelist.")
            context.user_data["admin_action"] = "remove"
            return ADMIN_PANEL
        elif query.data == "start_checking":
            await query.edit_message_text("Admin: start checking panel.")
        return ADMIN_PANEL

    # User buttons
    if query.data == "upload":
        await query.edit_message_text("📂 Send me your url:login:pass list as a .txt file.")
        return WAITING_FILE
    if query.data == "search":
        await query.edit_message_text("🔍 Send me the domain to search (e.g., coinbase.com).")
        return WAITING_URL

    return WAITING_FILE

# ──────────────── RECEIVE FILE ────────────────
async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.document:
        size_mb = update.message.document.file_size / 1024 / 1024
        if size_mb > 20:
            keyboard = [[InlineKeyboardButton("🔰 Get it here 🔰", url="https://gofile.io/d/rID0hD")]]
            await update.message.reply_text(
                "⚠️ File too big! Max allowed: 20MB.\nWe have an executable version for unlimited size.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FILE

        data_file = f"combo_list_{user_id}.txt"
        file = await update.message.document.get_file()
        await file.download_to_drive(data_file)

        keyboard = [[InlineKeyboardButton("🔍 Search Domain", callback_data="search")]]
        await update.message.reply_text(
            "✅ File uploaded successfully.\nProceed to next step:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_URL
    else:
        await update.message.reply_text("⚠️ Invalid file. Only .txt accepted.")
        return WAITING_FILE

# ──────────────── SEARCH DOMAIN ────────────────
async def search_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data_file = f"combo_list_{user_id}.txt"
    query_url = update.message.text.strip()
    output_file = f"result_{user_id}.txt"

    if not os.path.exists(data_file):
        await update.message.reply_text("⚠️ No combo list uploaded yet. Restart with /start.")
        return WAITING_FILE

    # Filter matches
    matches = [line.strip() for line in open(data_file, "r", encoding="utf-8", errors="ignore") if query_url in line.strip()]

    if not matches:
        await update.message.reply_text(f"❌ No matches found for {query_url}.")
        if os.path.exists(data_file):
            os.remove(data_file)
        return WAITING_FILE

    # Write results
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(matches))

    # Send results
    with open(output_file, "rb") as f:
        await update.message.reply_document(
            document=InputFile(f, filename=f"results_{user_id}.txt"),
            caption=f"🔍 Matches for {query_url}"
        )

    # Delete both combo and result files
    if os.path.exists(output_file):
        os.remove(output_file)
    if os.path.exists(data_file):
        os.remove(data_file)

    keyboard = [[InlineKeyboardButton("📂 Upload New List", callback_data="upload")]]
    await update.message.reply_text("⚡ Task complete. Choose your next action:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FILE

# ──────────────── ADMIN TEXT INPUT ────────────────
async def admin_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    action = context.user_data.get("admin_action")
    if not action:
        return

    try:
        target_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID format.")
        return ADMIN_PANEL

    if action == "add" and target_id not in WHITELISTED_IDS:
        WHITELISTED_IDS.append(target_id)
        with open(WHITELIST_FILE, "w") as f:
            json.dump(WHITELISTED_IDS, f)
        await update.message.reply_text(f"✅ Added {target_id} to whitelist.")
    elif action == "remove" and target_id in WHITELISTED_IDS:
        WHITELISTED_IDS.remove(target_id)
        with open(WHITELIST_FILE, "w") as f:
            json.dump(WHITELISTED_IDS, f)
        await update.message.reply_text(f"✅ Removed {target_id} from whitelist.")

    context.user_data["admin_action"] = None
    return await admin_panel(update, context)

# ──────────────── MAIN ────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FILE: [
                CallbackQueryHandler(button_handler, pattern="upload"),
                MessageHandler(filters.Document.ALL, receive_file),
            ],
            WAITING_URL: [
                CallbackQueryHandler(button_handler, pattern="search"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_url),
            ],
            ADMIN_PANEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_input),
                CallbackQueryHandler(button_handler),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("⚡️ //𝐆𝐞𝐧𝐞𝐬𝐢𝐬 𝐀𝐠𝐞𝐧𝐭 is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

