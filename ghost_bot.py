from telethon import TelegramClient, events
import random
import asyncio
import os

# --- CONFIGURATION ---
API_ID = os.getenv('API_ID', 'YOUR_API_ID') 
API_HASH = os.getenv('API_HASH', 'YOUR_API_HASH')

TARGET_GROUPS = ['@lootingzone', '@Lootpath', '@allgiftcode777', '@cashbacktime_official', '@reviewworks0'] 
KEYWORDS = ['earn', 'earning', 'loot', 'paisa', 'income', 'money', 'app', 'glitch']

GROUP_BAIT_MESSAGE = "Bhai, iska secret glitch mere paas hai. Group mein link allow nahi hai, isliye maine tumhe Direct Message (DM) kar diya hai, check kar lo! ✅"
PRIVATE_HOOK_MESSAGE = "Hey! Group mein tum loot ke baare mein pooch rahe the. Ye raha secret link: https://t.me/skill2incomehub \n\nJoin karke pinned message check karo!"

client = TelegramClient('ghost_session', API_ID, API_HASH)

print("🚀 Ghost DM Bot is starting... Scanning groups!")

@client.on(events.NewMessage(chats=TARGET_GROUPS))
async def handler(event):
    message_text = event.message.message.lower()
    if any(word in message_text for word in KEYWORDS):
        user = await event.get_sender()
        if not user or user.bot: return
        try:
            await client.send_message(user.id, PRIVATE_HOOK_MESSAGE)
            await asyncio.sleep(random.randint(3, 7))
            await event.reply(GROUP_BAIT_MESSAGE)
            print(f"✅ Success: DM sent to {user.id}")
        except Exception as e:
            print(f"❌ Error: {e}")

with client:
    client.run_until_disconnected()
