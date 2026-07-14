import logging
import sqlite3
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
CHANNEL_USERNAME = '@skill2incomehub'
REQUIRED_REFERRALS = 3
LOOT_MESSAGE = "🎉 Congratulations! Here is your Secret UPI Loot: https://t.me/skill2incomehub"

logging.basicConfig(level=logging.INFO)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, referred_by INTEGER, ref_count INTEGER DEFAULT 0)''')
conn.commit()

bot = Bot(token=API_TOKEN or "dummy_token")
dp = Dispatcher()

async def is_member(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = None

    # Check if coming from pSEO page e.g. /start=loot_delhi
    if len(args) > 1 and not args[1].isdigit():
        payload = args[1]
        logging.info(f"User {user_id} joined via pSEO landing page: {payload}")

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        if len(args) > 1 and args[1].isdigit():
            referred_by = int(args[1])
            if referred_by != user_id:
                cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referred_by,))
                conn.commit()
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()

    if not await is_member(user_id):
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Join Channel 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        builder.row(InlineKeyboardButton(text="I have Joined ✅", callback_data="check_join"))
        return await message.answer(f"❌ Welcome! To unlock the secret loot, you must first join our channel {CHANNEL_USERNAME}!", reply_markup=builder.as_markup())

    cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if count >= REQUIRED_REFERRALS:
        await message.answer(f"🔥 YOU UNLOCKED THE LOOT!\n\n{LOOT_MESSAGE}")
    else:
        await message.answer(f"👋 Welcome to Skill2Income Hub!\n\n🎁 To unlock the secret ₹500 loot, invite {REQUIRED_REFERRALS} friends.\n\n📊 Your Referrals: {count}/{REQUIRED_REFERRALS}\n\n🔗 Link:\n{ref_link}")

@dp.callback_query(F.data == "check_join")
async def check_join(callback: types.CallbackQuery):
    if await is_member(callback.from_user.id):
        await callback.answer("✅ Verified!", show_alert=True)
        cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (callback.from_user.id,))
        count = cursor.fetchone()[0]
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
        if count >= REQUIRED_REFERRALS:
            await callback.message.answer(f"🔥 YOU UNLOCKED THE LOOT!\n\n{LOOT_MESSAGE}")
        else:
            await callback.message.answer(f"✅ Joined! Now invite {REQUIRED_REFERRALS} friends.\n\nLink: {ref_link}")
    else:
        await callback.answer("❌ Not joined yet!", show_alert=True)

async def handle_health_check(request):
    return web.Response(text="Bot is running smoothly 24/7 on Render!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Dummy web server started on port {port}")

async def main():
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
