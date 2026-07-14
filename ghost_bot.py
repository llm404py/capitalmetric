from telethon import TelegramClient, events
import random
import asyncio

# --- CONFIGURATION ---
API_ID = 'YOUR_API_ID' 
API_HASH = 'YOUR_API_HASH'
TARGET_GROUPS = ['@group1', '@group2', '@group3'] 
KEYWORDS = ['earn', 'earning', 'loot', 'paisa', 'income', 'money', 'app', 'glitch']

# Message that goes in the GROUP (No link here!)
GROUP_BAIT_MESSAGE = "Bhai, iska secret glitch mere paas hai. Group mein link allow nahi hai, isliye maine tumhe Direct Message (DM) kar diya hai, check kar lo! ✅"

# Message that goes in the PRIVATE DM (Link here!)
PRIVATE_HOOK_MESSAGE = "Hey! Group mein tum loot ke baare mein pooch rahe the. Ye raha secret link: https://t.me/skill2incomehub \n\nJoin karke pinned message check karo!"

client = TelegramClient('ghost_session', API_ID, API_HASH)

print("🚀 Ghost DM Bot is starting... Bypassing link filters!")

@client.on(events.NewMessage(chats=TARGET_GROUPS))
async def handler(event):
    message_text = event.message.message.lower()
    
    if any(word in message_text for word in KEYWORDS):
        user = await event.get_sender()
        if not user or user.bot:
            return

        print(f"🎯 Target found: {user.id}. Executing Ghost DM...")
        
        try:
            # Step 1: Send Private DM first (The actual link)
            await client.send_message(user.id, PRIVATE_HOOK_MESSAGE)
            
            # Small delay to look human
            await asyncio.sleep(random.randint(3, 7))
            
            # Step 2: Reply in group to let everyone know (The Bait)
            await event.reply(GROUP_BAIT_MESSAGE)
            
            print(f"✅ Success: DM sent and Bait posted for {user.id}")
        except Exception as e:
            print(f"❌ Error: {e} (Maybe user has private DMs closed)")

with client:
    client.run_until_disconnected()
