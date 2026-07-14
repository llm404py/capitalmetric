import logging
import sqlite3
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIGURATION ---
# Render Environment Variables use ho rahe hain
API_TOKEN = os.getenv('API_TOKEN', '8339426153:AAGTzWHQDCdEwG-lavYbkGyIvPAfPfYR_v8')
CHANNEL_USERNAME = '@skill2incomehub'
REQUIRED_REFERRALS = 3
LOOT_MESSAGE = "🎉 Congratulations! Here is your Secret UPI Loot: [Yahan apna loot link ya trick daalein]"

logging.basicConfig(level=logging.INFO)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, referred_by INTEGER, ref_count INTEGER DEFAULT 0)''')
conn.commit()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def is_member(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception: return False

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = None

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
        # Trigger start logic
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

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
