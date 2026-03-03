from telebot import TeleBot, types
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = input "8705272085:AAFdbGOdnFgcobP-mTbmEgUV9bHBurzaJ-Y"
LOGS_GROUP_ID = input -5196861891 
OWNER_ID = 7891919458

bot = TeleBot(BOT_TOKEN)

# Stockage temporaire des états des utilisateurs
user_state = {}

# ================= /start =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salut ! Je peux t'aider à envoyer des messages anonymes. Utilise /anonyme pour commencer.")

# ================= /anonyme =================
@bot.message_handler(commands=['anonyme'])
def anonyme(message):
    chat_id = message.chat.id
    user_state[chat_id] = {'step': 'ask_confirm'}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅", callback_data="confirm_yes"))
    markup.add(types.InlineKeyboardButton("❌", callback_data="confirm_no"))
    bot.send_message(chat_id, "Tu veux envoyer un message anonyme ?", reply_markup=markup)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if chat_id not in user_state:
        return

    if data == "confirm_no":
        bot.send_message(chat_id, "Action annulée.")
        user_state.pop(chat_id, None)
        return

    if data == "confirm_yes":
        bot.send_message(chat_id, "Envoie-moi ton message avec texte et/ou médias. N'oublie pas de mentionner le destinataire avec @ ou prénom.")
        user_state[chat_id]['step'] = 'waiting_message'
        bot.answer_callback_query(call.id)

# ================= RECEVOIR MESSAGE =================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'animation'])
def handle_message(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        return

    state = user_state[chat_id]

    if state['step'] == 'waiting_message':
        state['message_text'] = message.text or ""
        state['media'] = []

        # Stocker tous les médias
        if message.photo:
            for p in message.photo:
                state['media'].append({'type': 'photo', 'file_id': p.file_id})
        if message.video:
            state['media'].append({'type': 'video', 'file_id': message.video.file_id})
        if message.animation:
            state['media'].append({'type': 'animation', 'file_id': message.animation.file_id})
        if message.document:
            state['media'].append({'type': 'document', 'file_id': message.document.file_id})

        state['step'] = 'waiting_channel'
        bot.send_message(chat_id, "Dans quel canal ou groupe veux-tu envoyer ce message anonyme ? (format https://t.me/nomdugroupe)")

    elif state['step'] == 'waiting_channel':
        channel_link = message.text.strip()
        state['channel'] = channel_link

        # =============== ENVOI DU MESSAGE ANONYME ===============
        media_group = []

        # Si aucun média, on envoie juste le texte
        if not state['media']:
            bot.send_message(channel_link, f"Quelqu’un a quelque chose à te dire :\n{state['message_text']}\nSauras-tu savoir qui a écrit ce message ?👀")
        else:
            # Créer un media group pour envoyer tous les médias en un seul message
            for idx, media in enumerate(state['media']):
                if media['type'] == 'photo':
                    media_group.append(types.InputMediaPhoto(media['file_id'], caption=state['message_text'] if idx==0 else None))
                elif media['type'] == 'video':
                    media_group.append(types.InputMediaVideo(media['file_id'], caption=state['message_text'] if idx==0 else None))
                elif media['type'] == 'animation':
                    media_group.append(types.InputMediaAnimation(media['file_id'], caption=state['message_text'] if idx==0 else None))
                elif media['type'] == 'document':
                    media_group.append(types.InputMediaDocument(media['file_id'], caption=state['message_text'] if idx==0 else None))
            bot.send_media_group(channel_link, media_group)

        # =============== ENVOI DES LOGS ===============
        now = datetime.now()
        date_str = now.strftime("%d %B - %H:%M %Ss")
        log_msg = f"UserID: {message.from_user.id} / @{message.from_user.username if message.from_user.username else ''}\nChannel: {channel_link}\nDate: {date_str}\nMessage: {state['message_text']}\nMedia:"
        for media in state['media']:
            emoji = "📷" if media['type']=='photo' else "🎥" if media['type']=='video' else "🎞️" if media['type']=='animation' else "📄"
            log_msg += f"\n{emoji} {media['file_id']}"

        bot.send_message(LOGS_GROUP_ID, log_msg)

        bot.send_message(chat_id, "Ton message a été envoyé anonymement ! ✅")
        user_state.pop(chat_id, None)

# ================= RUN =================
bot.infinity_polling()
