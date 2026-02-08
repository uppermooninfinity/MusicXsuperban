import asyncio
import base64
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.enums import ParseMode, ChatType

# Core Imports
from Oneforall import app
from Oneforall.core.mongo import mongodb
import Oneforall.core.userbot as userbot_module
from Oneforall.core.readable_time import get_readable_time
from Oneforall.misc import SUDOERS
from Oneforall.utils.functions import extract_user, extract_user_and_reason

# Config
from config import (
    SUPERBAN_CHAT_ID, 
    STORAGE_CHANNEL_ID,
    SUPERBAN_VIDEO_URL,
    LOGGER_ID, 
    BANNED_USERS,
    NETWORK_SUB_BOTS,
    AUTHORS
)

# Database
fedsdb = mongodb.federations
fedbansdb = mongodb.federation_bans

reason_storage = {}
next_reason_id = 1

# --- 1. PREMIUM FORMATTING ---

def format_text(text):
    mapping = {'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ', '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', ':': ':', '-': '-', '.': '.'}
    sc_text = "".join(mapping.get(c.lower(), c) for c in str(text))
    return f"<blockquote><b><i><u>{sc_text}</u></i></b></blockquote>"

# --- 2. THE CORE EXECUTION (SINGLE STRIKE + GLOBAL KICK) ---

async def execute_super_action(user_id, reason, approver, approver_id, action="ban"):
    start_time = datetime.utcnow()
    bot_hits, group_kicks = 0, 0
    
    # A. SINGLE FEDBAN/GBAN STRIKE (Anti-Spam)
    # Assistant sirf main chat mein ek baar command bhejega jaha se saare feds linked hain
    for client in userbot_module.userbot_clients:
        try:
            # Common command strike for Fed and Global sync
            strike_cmd = f"/{'fedban' if action=='ban' else 'unfedban'} {user_id} {reason}"
            gstrike_cmd = f"/{'gban' if action=='ban' else 'ungban'} {user_id} {reason}"
            
            await client.send_message(SUPERBAN_CHAT_ID, strike_cmd)
            await asyncio.sleep(0.3)
            await client.send_message(SUPERBAN_CHAT_ID, gstrike_cmd)
        except: pass
        break # Ek client se bhej diya matlab kaam ho gaya

    # B. GLOBAL DIRECT ACTION (PM + KICK)
    for client in userbot_module.userbot_clients:
        # 1. PM Strike to Sudo Bots
        if NETWORK_SUB_BOTS:
            for bot in NETWORK_SUB_BOTS:
                try:
                    await client.send_message(bot, f"/{'gban' if action=='ban' else 'ungban'} {user_id} {reason}")
                    bot_hits += 1
                except: continue
        
        # 2. Native Group Kick (No command spam)
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    if action == "ban":
                        await client.ban_chat_member(dialog.chat.id, user_id)
                    else:
                        await client.unban_chat_member(dialog.chat.id, user_id)
                    group_kicks += 1
                except: continue

    # C. DATABASE LOGGING
    if action == "ban":
        await fedbansdb.update_one({"user_id": user_id}, {"$set": {"reason": reason, "by": approver, "time": datetime.utcnow()}}, upsert=True)
    else:
        await fedbansdb.delete_many({"user_id": user_id})

    readable_time = get_readable_time(datetime.utcnow() - start_time)
    
    report = (
        f"🚀 sᴜᴘᴇʀʙᴀɴ {action.upper()} ᴇxᴇᴄᴜᴛᴇᴅ\n\n"
        f"👤 ᴛᴀʀɢᴇᴛ: `{user_id}`\n"
        f"🛡️ ᴀᴅᴍɪɴ: {approver}\n"
        f"📝 ʀᴇᴀsᴏɴ: {reason}\n"
        f"🌐 ꜰᴇᴅ sᴛᴀᴛᴜs: ɴᴇᴛᴡᴏʀᴋ sʏɴᴄᴇᴅ\n"
        f"🤖 ʙᴏᴛs ʜɪᴛ: {bot_hits}\n"
        f"🏘️ ɢʀᴏᴜᴘs ᴄʟᴇᴀɴᴇᴅ: {group_kicks}\n"
        f"🕒 ᴛɪᴍᴇ: {readable_time}"
    )
    return report

# --- 3. LOGGING & HANDLERS ---

async def send_super_logs(report_text):
    formatted_report = format_text(report_text)
    for log_id in [LOGGER_ID, STORAGE_CHANNEL_ID]:
        if not log_id: continue
        try:
            if SUPERBAN_VIDEO_URL:
                await app.send_video(log_id, video=SUPERBAN_VIDEO_URL, caption=formatted_report, parse_mode=ParseMode.HTML)
            else:
                await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
        except:
            try: await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
            except: pass

@app.on_message(filters.command(["superban", "unsuperban"]) & ~BANNED_USERS)
async def superban_handler(_, message: Message):
    cmd = message.command[0].lower()
    user_id, reason = await extract_user_and_reason(message)
    if not user_id: return await message.reply_text(format_text("ᴜsᴇʀ ID ᴛᴏ ᴅᴇ ʙʜᴀɪ."))

    if message.from_user.id in SUDOERS or message.from_user.id in AUTHORS:
        m = await message.reply_text(format_text("⚡ ʟᴀᴜɴᴄʜɪɴɢ ɢʟᴏʙᴀʟ sᴛʀɪᴋᴇ..."))
        report = await execute_super_action(user_id, reason or "ɴᴏ ʀᴇᴀsᴏɴ", message.from_user.first_name, message.from_user.id, action="ban" if cmd == "superban" else "unban")
        await m.edit_text(format_text(report), parse_mode=ParseMode.HTML)
        await send_super_logs(report)
    else:
        # Request Management
        global next_reason_id
        rid = next_reason_id
        reason_storage[rid] = reason or "ɴᴏ ʀᴇᴀsᴏɴ"
        next_reason_id += 1
        encoded_rid = base64.b64encode(str(rid).encode()).decode()
        await app.send_message(SUPERBAN_CHAT_ID, format_text(f"🚨 {cmd.upper()} ʀᴇǫᴜᴇsᴛ\n\nᴜsᴇʀ: `{user_id}`\nʙʏ: {message.from_user.first_name}"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"sb_{cmd}_{user_id}_{encoded_rid}")]]), parse_mode=ParseMode.HTML)
        await message.reply_text(format_text("ʀᴇǫᴜᴇsᴛ sᴇɴᴛ ᴛᴏ ʜɪɢʜ ᴄᴏᴍᴍᴀɴᴅ."))

@app.on_callback_query(filters.regex(r'^sb_(superban|unsuperban)_(\d+)_(.+)$'))
async def on_approve_cb(_, query: CallbackQuery):
    if query.from_user.id not in SUDOERS and query.from_user.id not in AUTHORS:
        return await query.answer("ᴀᴜǫᴀᴛ ᴍᴇɪɴ!", show_alert=True)
    action, user_id, encoded_rid = query.matches[0].groups()
    rid = int(base64.b64decode(encoded_rid).decode())
    await query.message.edit_text(format_text("⚡ ᴀᴘᴘʀᴏᴠᴇᴅ. ᴇxᴇᴄᴜᴛɪɴɢ..."))
    report = await execute_super_action(int(user_id), reason_storage.get(rid, "ᴀᴘᴘʀᴏᴠᴇᴅ"), query.from_user.first_name, query.from_user.id, action="ban" if action == "superban" else "unban")
    await query.message.edit_text(format_text(report), parse_mode=ParseMode.HTML)
    await send_super_logs(report)
        
