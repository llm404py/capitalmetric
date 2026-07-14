import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text

# --- CONFIGURATION ---
API_TOKEN = '8339426153:AAGTzWHQDCdEwG-lavYbkGyIvPAfPfYR_v8'
CHANNEL_USERNAME = '@skill2incomehub'
REQUIRED_REFERRALS = 3
LOOT_MESSAGE = "🎉 Congratulations! Here is your Secret UPI Loot: [Yahan apna loot link ya trick daalein]"

# Logging
logging.basicConfig(level=logging.INFO)

# Database Setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, referred_by INTEGER, ref_count INTEGER DEFAULT 0)''')
conn.commit()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def is_member(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # Register user in DB
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        referred_by = None
        if args and args.isdigit():
            referred_by = int(args)
            if referred_by != user_id:
                cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referred_by,))
                conn.commit()
        
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()

    # Check Membership
    if not await is_member(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            InlineKeyboardButton("I have Joined ✅", callback_data="check_join")
        )
        return await message.answer(f"❌ Welcome! To unlock the secret loot, you must first join our channel {CHANNEL_USERNAME}!", reply_markup=markup)

    # Show Referral Status
    cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    
    if count >= REQUIRED_REFERRALS:
        await message.answer(f"🔥 YOU UNLOCKED THE LOOT!\n\n{LOOT_MESSAGE}")
    else:
        text = (f"👋 Welcome to Skill2Income Hub!\n\n"
                f"🎁 To unlock the secret ₹500 loot, you need to invite {REQUIRED_REFERRALS} friends to this bot.\n\n"
                f"📊 Your Referrals: {count}/{REQUIRED_REFERRALS}\n\n"
                f"🔗 Your Referral Link:\n{ref_link}\n\n"
                f"Share this link with your friends!")
        await message.answer(text)

@dp.callback_query_handler(Text(equals="check_join"))
async def check_join(callback: types.CallbackQuery):
    if await is_member(callback.from_user.id):
        await callback.answer("✅ Membership Verified!", show_alert=True)
        # Trigger start logic again to show referrals
        await start_cmd(callback.message)
    else:
        await callback.answer("❌ You haven't joined yet!", show_alert=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
