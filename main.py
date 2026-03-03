import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerChannel
import aiohttp

# ================= CONFIG =================
API_ID = 36767235
API_HASH = "6a36bf6c4b15e7eecdb20885a13fc2d7"
BOT_TOKEN = "8705272085:AAFdbGOdnFgcobP-mTbmEgUV9bHBurzaJ-Y"
LOGS_GROUP_ID = -1003769561519  # Groupe où les logs seront envoyés
OWNER_ID = 7891919458  # Seul qui peut voir les logs

# ================= CLIENT =================
bot = TelegramClient("anonbot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ================= VARIABLES =================
sessions = {}  # Pour stocker temporairement chaque étape par utilisateur

# ================= UTILS =================
def format_date(dt):
    mois = ["janvier","février","mars","avril","mai","juin","juillet",
            "août","septembre","octobre","novembre","décembre"]
    return f"{dt.day} {mois[dt.month-1]} - {dt.hour}:{dt.minute:02d} {dt.second}s"

# ================= COMMANDES =================
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply("Salut ! Je peux t'aider à envoyer des messages anonymes. Utilise /anonyme pour commencer.")

@bot.on(events.NewMessage(pattern="/anonyme"))
async def anonyme_start(event):
    uid = event.sender_id
    sessions[uid] = {"step": "texte"}
    await event.reply("Envoie-moi ton message texte. Tu peux inclure des mentions comme @pseudo.")

@bot.on(events.NewMessage)
async def process_message(event):
    uid = event.sender_id
    if uid not in sessions:
        return

    session = sessions[uid]

    # Étape texte
    if session["step"] == "texte":
        session["texte"] = event.text
        session["step"] = "media"
        await event.reply("Tu peux maintenant m'envoyer des médias (images/vidéos). Tu peux en envoyer plusieurs. Si tu n'en veux pas, écris 'none'.")
        return

    # Étape média
    if session["step"] == "media":
        media_list = []
        if event.text.lower() == "none":
            media_list = []
        elif event.media:
            media_list.append(event.media)
        else:
            await event.reply("Envoie un média ou écris 'none' si tu n'en veux pas.")
            return

        session["media"] = media_list
        session["step"] = "confirm"
        buttons = [Button.inline("✅", b"confirm"), Button.inline("❌", b"cancel")]
        await event.reply("Es-tu sûr de vouloir envoyer ce message anonymement ? 👀", buttons=buttons)
        return

# ================= BOUTONS =================
@bot.on(events.CallbackQuery)
async def callback(event):
    uid = event.sender_id
    if uid not in sessions:
        await event.answer("Session expirée ou invalide.", alert=True)
        return

    session = sessions[uid]

    if event.data == b"cancel":
        del sessions[uid]
        await event.edit("Envoi annulé.")
        return

    if event.data == b"confirm":
        session["step"] = "destination"
        await event.edit("Dans quel canal ou groupe veux-tu envoyer ce message anonyme ? (format @dugroupe/canal)")
        return

# ================= DESTINATION =================
@bot.on(events.NewMessage)
async def destination(event):
    uid = event.sender_id
    if uid not in sessions:
        return

    session = sessions[uid]

    if session.get("step") != "destination":
        return

    dest = event.text.strip()
    session["destination"] = dest

    # Envoi dans le canal
    try:
        entity = await bot.get_entity(dest)
    except:
        await event.reply("Impossible de trouver le canal/groupe. Vérifie le format (@nomducanal).")
        return

    texte = f"Quelqu’un a quelque chose à te dire {dest}\n\n{session['texte']}\n"
    media = session.get("media", [])
    if media:
        media_texts = "\n".join([f"📷 (média attaché)" for m in media])
        texte += f"\n{media_texts}"

    texte += "\n\nSauras-tu savoir qui a écrit ce message ? 👀"

    # Envoi dans le canal
    if media:
        # Envoi un media group si plusieurs
        await bot.send_file(entity, files=media, caption=texte)
    else:
        await bot.send_message(entity, texte)

    # Envoi des logs
    date_str = format_date(datetime.now())
    log_msg = f"**Logs des messages anonymes**\n\nUserID: {uid} / @{event.sender.username if event.sender.username else ''}\nChannel: {dest}\nDate: {date_str}\nMessage: {session['texte']}\nMedia: {len(media)} média(s) attaché(s)"
    await bot.send_message(LOGS_GROUP_ID, log_msg)

    del sessions[uid]
    await event.reply("Message envoyé anonymement ✅")

# ================= RUN =================
print("Bot anonyme en ligne...")
bot.run_until_disconnected()
