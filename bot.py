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
LOOT_MESSAGE = (
    "🎉 **CONGRATULATIONS! YOU UNLOCKED THE SECRET LOOT!**\n\n"
    "⚡ **Your Exclusive Access Link:**\n"
    "👉 https://t.me/skill2incomehub/pinned\n\n"
    "💡 *Note: This link is unique to your Telegram ID and expires within 24 hours. Tap above immediately to claim your ₹500 instant UPI reward and Flipkart 90% off glitch checkout!*"
)

logging.basicConfig(level=logging.INFO)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    referred_by INTEGER, 
    ref_count INTEGER DEFAULT 0,
    source_campaign TEXT DEFAULT 'general'
)''')
conn.commit()

# Fallback to avoid complete app crash on Render if API_TOKEN is temporarily missing
bot_token = API_TOKEN if API_TOKEN else "123456789:ABCDefghIJKLmnopQRSTuvwxYZ"
bot = Bot(token=bot_token)
dp = Dispatcher()

async def is_member(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.warning(f"Failed membership check for {user_id}: {e}")
        return False

def get_progress_bar(count, total=REQUIRED_REFERRALS):
    percent = min(int((count / total) * 10), 10)
    filled = "█" * percent
    empty = "░" * (10 - percent)
    return f"[{filled}{empty}] ({count}/{total})"

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = None
    campaign = 'general'

    if len(args) > 1:
        payload = args[1]
        if payload.isdigit():
            referred_by = int(payload)
        else:
            campaign = payload
            logging.info(f"🎯 User {user_id} arrived via pSEO/Campaign: {campaign}")

    cursor.execute("SELECT user_id, ref_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        if referred_by and referred_by != user_id:
            cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referred_by,))
            conn.commit()
            # Try to notify referrer
            try:
                cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (referred_by,))
                new_count = cursor.fetchone()[0]
                if new_count >= REQUIRED_REFERRALS:
                    await bot.send_message(
                        referred_by, 
                        f"🔥 **BOOM! A friend joined via your link!**\n\n🎯 **Referrals Completed: {new_count}/{REQUIRED_REFERRALS}**\n\n🎉 You have officially unlocked the secret loot! Send `/start` to claim your link now!"
                    )
                else:
                    await bot.send_message(
                        referred_by, 
                        f"👤 **New Referral Verified!**\n\nYour friend joined via your exclusive link.\n📊 **Progress:** {get_progress_bar(new_count)}\n⚡ Just **{REQUIRED_REFERRALS - new_count} more invite(s)** left to unlock the ₹500 UPI cash and glitch deals!"
                    )
            except Exception:
                pass

        cursor.execute("INSERT INTO users (user_id, referred_by, source_campaign) VALUES (?, ?, ?)", (user_id, referred_by, campaign))
        conn.commit()
        count = 0
    else:
        count = row[1]

    # --- Step 1: Force Channel Join Check ---
    if not await is_member(user_id):
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📢 JOIN SKILL2INCOME HUB (REQUIRED)", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        builder.row(InlineKeyboardButton(text="⚡ I HAVE JOINED • VERIFY NOW ✅", callback_data="check_join"))
        
        welcome_msg = (
            f"🚨 **HUMAN VERIFICATION REQUIRED**\n\n"
            f"Welcome to **Skill2Income Hub** (`@skill2incomehub`) — India's #1 Verified Deals & Glitch Network.\n\n"
            f"To prevent automated bots from exhausting our limited ₹500 UPI promotional funds and 90% e-commerce glitch links, please complete 1-step verification:\n\n"
            f"👉 **Step 1:** Click the button below to join our official channel **{CHANNEL_USERNAME}**.\n"
            f"👉 **Step 2:** After joining, click **⚡ I HAVE JOINED • VERIFY NOW ✅**."
        )
        return await message.answer(welcome_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")

    # --- Step 2: Referral / Unlock Status ---
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if count >= REQUIRED_REFERRALS:
        await message.answer(LOOT_MESSAGE, parse_mode="Markdown")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📲 SHARE WITH FRIENDS (INSTANT)", url=f"https://t.me/share/url?url={ref_link}&text=🔥%20Get%20Daily%20₹200-₹500%20Free%20UPI%20Cash%20and%20Flipkart%2090%25%20OFF%20Glitch%20Deals!%20Join%20Skill2Income%20Hub%20now:"))
        builder.row(InlineKeyboardButton(text="🔄 REFRESH PROGRESS", callback_data="refresh_stats"))

        status_msg = (
            f"⚡ **OFFICIAL LOOT UNLOCKED STATUS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Welcome, **{message.from_user.first_name}**!\n"
            f"You have successfully verified your Telegram account. Now, unlock exclusive VIP access to today's **₹500 Direct UPI Cash Drop** and **Flipkart ₹99 Glitch Links**.\n\n"
            f"🎯 **YOUR UNLUCK PROGRESS:**\n"
            f"{get_progress_bar(count)}\n"
            f"👥 **Referrals:** `{count}/{REQUIRED_REFERRALS} Friends Verified`\n\n"
            f"🔗 **YOUR EXCLUSIVE INVITE LINK:**\n"
            f"`{ref_link}`\n\n"
            f"📌 **How to complete in 2 minutes:**\n"
            f"1️⃣ Copy your invite link above or tap **📲 SHARE WITH FRIENDS**.\n"
            f"2️⃣ Send it to just **{REQUIRED_REFERRALS - count} doston ko** (WhatsApp groups/Telegram/College friends).\n"
            f"3️⃣ As soon as {REQUIRED_REFERRALS} friends start the bot, your VIP loot link opens instantly!"
        )
        await message.answer(status_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_join")
async def check_join(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await is_member(user_id):
        await callback.answer("✅ Verification Successful! Access Granted.", show_alert=True)
        # Trigger full status display
        cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        count = row[0] if row else 0
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        if count >= REQUIRED_REFERRALS:
            await callback.message.edit_text(LOOT_MESSAGE, parse_mode="Markdown")
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="📲 SHARE WITH FRIENDS (INSTANT)", url=f"https://t.me/share/url?url={ref_link}&text=🔥%20Get%20Daily%20₹200-₹500%20Free%20UPI%20Cash%20and%20Flipkart%2090%25%20OFF%20Glitch%20Deals!%20Join%20Skill2Income%20Hub%20now:"))
            builder.row(InlineKeyboardButton(text="🔄 REFRESH PROGRESS", callback_data="refresh_stats"))

            status_msg = (
                f"⚡ **OFFICIAL LOOT UNLOCKED STATUS**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👋 Welcome, **{callback.from_user.first_name}**!\n"
                f"You have successfully verified your Telegram account. Now, unlock exclusive VIP access to today's **₹500 Direct UPI Cash Drop** and **Flipkart ₹99 Glitch Links**.\n\n"
                f"🎯 **YOUR UNLUCK PROGRESS:**\n"
                f"{get_progress_bar(count)}\n"
                f"👥 **Referrals:** `{count}/{REQUIRED_REFERRALS} Friends Verified`\n\n"
                f"🔗 **YOUR EXCLUSIVE INVITE LINK:**\n"
                f"`{ref_link}`\n\n"
                f"📌 **How to complete in 2 minutes:**\n"
                f"1️⃣ Copy your invite link above or tap **📲 SHARE WITH FRIENDS**.\n"
                f"2️⃣ Send it to just **{REQUIRED_REFERRALS - count} doston ko** (WhatsApp groups/Telegram/College friends).\n"
                f"3️⃣ As soon as {REQUIRED_REFERRALS} friends start the bot, your VIP loot link opens instantly!"
            )
            await callback.message.edit_text(status_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await callback.answer("❌ You haven't joined @skill2incomehub yet! Please join first.", show_alert=True)

@dp.callback_query(F.data == "refresh_stats")
async def refresh_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT ref_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    count = row[0] if row else 0
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if count >= REQUIRED_REFERRALS:
        await callback.message.edit_text(LOOT_MESSAGE, parse_mode="Markdown")
    else:
        await callback.answer(f"📊 Current Referrals: {count}/{REQUIRED_REFERRALS}. Invite {REQUIRED_REFERRALS - count} more!", show_alert=True)

# --- DUMMY WEB SERVER FOR RENDER (Fixes "No open ports detected" & 24/7 Uptime) ---
async def handle_health_check(request):
    return web.Response(text="🟢 Skill2Income Bot is running 24/7 on Render Port!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"🟢 Web Server listening on 0.0.0.0:{port}")

async def main():
    if not API_TOKEN or API_TOKEN.startswith("123456789:"):
        logging.error("❌ CRITICAL: API_TOKEN environment variable is not set with a real Telegram Token!")
        # We start the web server only so Render health check doesn't kill the container while user is adding the token in dashboard
        await start_web_server()
        while True:
            await asyncio.sleep(60)
            logging.warning("Waiting for valid API_TOKEN in Render environment settings...")
    else:
        await asyncio.gather(
            start_web_server(),
            dp.start_polling(bot)
        )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot shut down gracefully.")
