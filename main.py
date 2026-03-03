from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
import datetime

# ================= CONFIG =================
BOT_TOKEN = "8705272085:AAFdbGOdnFgcobP-mTbmEgUV9bHBurzaJ-Y"
OWNER_ID = 7891919458  # ton ID pour recevoir les logs
TARGET_CHANNEL_ID = -1003696703161  # canal fixe pour envoyer les messages anonymes

# ================= VARIABLES =================
user_sessions = {}  # stocke l'état de chaque utilisateur

# ================= HELPERS =================
def format_date():
    now = datetime.datetime.now()
    return now.strftime("%d %B - %H:%M %Ss")  # exemple: 28 avril - 18:42 6s

# ================= COMMANDES =================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Salut ! Je peux t'aider à envoyer des messages anonymes. Utilise /anonyme pour commencer."
    )

def anonyme(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"text": "", "media": []}
    update.message.reply_text(
        "Quel est le texte de ton message anonyme ? (Tu peux mentionner quelqu’un avec @ ou mettre son prénom)"
    )

def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        return  # ignore les messages hors session

    session = user_sessions[user_id]

    if session["text"] == "":
        session["text"] = update.message.text
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Ajouter médias", callback_data="add_media")],
            [InlineKeyboardButton("❌ Aucun média", callback_data="no_media")]
        ])
        update.message.reply_text(
            "Veux-tu ajouter des médias (images, vidéos, documents) à ton message ?", reply_markup=keyboard
        )

def handle_media(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]

    media_list = session["media"]

    if update.message.photo:
        media_list.append(update.message.photo[-1].file_id)  # dernière résolution
    elif update.message.video:
        media_list.append(update.message.video.file_id)
    elif update.message.document:
        media_list.append(update.message.document.file_id)

# ================= CALLBACKS =================
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    session = user_sessions.get(user_id)
    if not session:
        query.answer()
        return

    if query.data == "add_media":
        query.edit_message_text(
            "Parfait ! Envoie-moi maintenant tes médias. Quand tu as fini, envoie /done"
        )
    elif query.data == "no_media":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅", callback_data="confirm")],
            [InlineKeyboardButton("❌", callback_data="cancel")]
        ])
        query.edit_message_text(
            "Es-tu sûr de vouloir envoyer ce message anonymement ? 👀", reply_markup=keyboard
        )
    elif query.data == "confirm":
        send_anonymous_message(user_id, context)
        query.edit_message_text("Ton message a été envoyé anonymement ! ✅")
        user_sessions.pop(user_id, None)
    elif query.data == "cancel":
        query.edit_message_text("Envoi annulé ❌")
        user_sessions.pop(user_id, None)
    query.answer()

def done(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅", callback_data="confirm")],
        [InlineKeyboardButton("❌", callback_data="cancel")]
    ])
    update.message.reply_text(
        "Es-tu sûr de vouloir envoyer ce message anonymement ? 👀", reply_markup=keyboard
    )

# ================= ENVOI MESSAGE =================
def send_anonymous_message(user_id, context: CallbackContext):
    session = user_sessions[user_id]
    text = session["text"]
    media_files = session["media"]

    media_group = []

    for file_id in media_files:
        # vérifier si c'est photo ou vidéo
        # ici on simplifie : on considère toutes les photos comme photos, sinon vidéo
        media_group.append(InputMediaPhoto(media=file_id))

    # construction du message final
    final_text = f"Quelqu’un a quelque chose à te dire\n\n{text}\n\nSauras-tu savoir qui a écrit ce message ? 👀"

    if media_group:
        # envoyer tous les médias en une seule fois
        context.bot.send_media_group(chat_id=TARGET_CHANNEL_ID, media=media_group)
        context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=final_text)
    else:
        context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=final_text)

    # ================= LOGS =================
    log_text = f"Logs des messages anonymes\n\nUserID: {user_id} / @{context.bot.get_chat(user_id).username}\nMessage: {text}\n"
    log_text += f"Media: {', '.join(media_files) if media_files else 'Aucun média'}\n"
    log_text += f"Date: {format_date()}\n"
    log_text += f"Channel: https://t.me/ahscwysksoaizvz"

    context.bot.send_message(chat_id=OWNER_ID, text=log_text)

# ================= MAIN =================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("anonyme", anonyme))
    dp.add_handler(CommandHandler("done", done))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video | Filters.document, handle_media))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
