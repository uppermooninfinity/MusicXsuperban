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

from config import (
    SUPERBAN_CHAT_ID, 
    STORAGE_CHANNEL_ID,
    SUPERBAN_VIDEO_URL,
    LOGGER_ID, 
    AUTHORS, 
    BANNED_USERS
)

# Database
fedsdb = mongodb.federations
fedbansdb = mongodb.federation_bans

MUSIC_BOTS = ["snowy_x_musicbot", "superban_probot", "roohi_queen_bot"]
reason_storage = {}
next_reason_id = 1

# --- 1. PREMIUM FORMATTING & ANIMATIONS ---

def format_text(text):
    mapping = {'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ', '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', ':': ':', '-': '-', '.': '.'}
    sc_text = "".join(mapping.get(c.lower(), c) for c in str(text))
    return f"<blockquote><b><i><u>{sc_text}</u></i></b></blockquote>"

async def run_animation(msg: Message):
    steps = ["⚙️ ɪɴɪᴛɪᴀʟɪᴢɪɴɢ...", "📡 sʏɴᴄɪɴɢ ʙᴏᴛ ɴᴇᴛᴡᴏʀᴋ...", "🛰️ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴍᴜsɪᴄ ᴄᴏʀᴇ...", "⚔️ ᴅᴇᴘʟᴏʏɪɴɢ ɢʟᴏʙᴀʟ ᴀᴄᴛɪᴏɴ..."]
    for step in steps:
        try:
            await msg.edit_text(format_text(step), parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.7)
        except: pass

# --- 2. CORE EXECUTION LOGIC ---

async def execute_super_action(user_id, reason, approver, approver_id, action="ban"):
    start_time = datetime.utcnow()
    m_gbans, r_bridge = 0, 0
    is_sudo = approver_id in SUDOERS or approver_id in AUTHORS

    for client in userbot_module.userbot_clients:
        # Music Bot Sync
        if is_sudo:
            for bot in MUSIC_BOTS:
                try:
                    await client.send_message(bot, f"/{'gban' if action=='ban' else 'ungban'} {user_id} {reason}")
                    m_gbans += 1
                except: continue
        
        # Rose & Global Bridge
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    await client.send_message(dialog.chat.id, f"/{'fedban' if action=='ban' else 'unfedban'} {user_id} {reason}")
                    if action == "ban": await client.ban_chat_member(dialog.chat.id, user_id)
                    else: await client.unban_chat_member(dialog.chat.id, user_id)
                    r_bridge += 1
                except: continue
    
    if action == "ban":
        await fedbansdb.update_one({"user_id": user_id}, {"$set": {"reason": reason, "by": approver, "by_id": approver_id, "time": datetime.utcnow()}}, upsert=True)
    else:
        await fedbansdb.delete_one({"user_id": user_id})

    time_taken = get_readable_time(datetime.utcnow() - start_time)
    
    report = (
        f"🚀 sᴜᴘᴇʀʙᴀɴ {action.upper()} ᴄᴏᴍᴘʟᴇᴛᴇ\n\n"
        f"👤 ᴛᴀʀɢᴇᴛ: `{user_id}`\n"
        f"🛡️ ᴀᴅᴍɪɴ: {approver}\n"
        f"📝 ʀᴇᴀsᴏɴ: {reason}\n"
        f"🏘️ ᴄʜᴀᴛs ᴀꜰꜰᴇᴄᴛᴇᴅ: {r_bridge}\n"
        f"🎵 ᴍᴜsɪᴄ ʙᴏᴛs sʏɴᴄ: {m_gbans}\n"
        f"🕒 ᴛɪᴍᴇ ᴛᴀᴋᴇɴ: {time_taken}\n"
        f"📊 sᴛᴀᴛᴜs: sᴜᴄᴄᴇssꜰᴜʟ"
    )
    return report

# Updated logging logic to include Video
async def send_super_logs(report_text):
    formatted_report = format_text(report_text)
    destinations = [LOGGER_ID, STORAGE_CHANNEL_ID]
    
    for log_id in destinations:
        try:
            # Agar video URL available hai toh video bhejega
            if SUPERBAN_VIDEO_URL:
                await app.send_video(
                    log_id, 
                    video=SUPERBAN_VIDEO_URL, 
                    caption=formatted_report,
                    parse_mode=ParseMode.HTML
                )
            else:
                await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
        except:
            # Fallback agar send_video block ho ya crash ho
            try: await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
            except: pass
                

# --- 3. SUPERSTATS COMMAND ---

@app.on_message(filters.command("superstats") & ~BANNED_USERS)
async def superstats_handler(_, message: Message):
    user_id = await extract_user(message)
    if not user_id: return await message.reply_text(format_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ ɢɪᴠᴇ ɪᴅ."), parse_mode=ParseMode.HTML)
    
    ban_info = await fedbansdb.find_one({"user_id": user_id})
    try: user = await app.get_users(user_id); name = user.first_name
    except: name = "ᴜɴᴋɴᴏᴡɴ"
    
    if not ban_info:
        return await message.reply_text(format_text(f"✅ ᴜsᴇʀ `{user_id}` ɪs ᴄʟᴇᴀɴ ɪɴ ᴏᴜʀ ᴅᴀᴛᴀʙᴀsᴇ."), parse_mode=ParseMode.HTML)
    
    # Date formatting fix
    ban_time = ban_info.get('time')
    date_str = ban_time.strftime('%Y-%m-%d') if isinstance(ban_time, datetime) else "Unknown"

    stats = (
        f"📊 sᴜᴘᴇʀʙᴀɴ ɪɴᴛᴇʟ\n\n"
        f"👤 ɴᴀᴍᴇ: {name}\n"
        f"🆔 ɪᴅ: `{user_id}`\n"
        f"📝 ʀᴇᴀsᴏɴ: {ban_info.get('reason')}\n"
        f"🛡️ ʙᴀɴɴᴇᴅ ʙʏ: {ban_info.get('by')}\n"
        f"📅 ᴅᴀᴛᴇ: {date_str}\n"
        f"🌐 ᴛʏᴘᴇ: ɢʟᴏʙᴀʟ ᴇɴꜰᴏʀᴄᴇᴍᴇɴᴛ"
    )
    await message.reply_text(format_text(stats), parse_mode=ParseMode.HTML)

# --- 4. MAIN COMMAND HANDLER ---

@app.on_message(filters.command(["superban", "unsuperban"]) & ~BANNED_USERS)
async def main_cmd_handler(_, message: Message):
    cmd = message.command[0].lower()
    user_id, reason = await extract_user_and_reason(message)
    if not user_id: return await message.reply_text(format_text("ᴘʀᴏᴠɪᴅᴇ ᴀ ᴛᴀʀɢᴇᴛ ᴜsᴇʀ."), parse_mode=ParseMode.HTML)

    is_sudo = message.from_user.id in SUDOERS or message.from_user.id in AUTHORS
    
    if is_sudo:
        m = await message.reply_text(format_text("⚙️ ɪɴɪᴛɪᴀʟɪᴢɪɴɢ..."), parse_mode=ParseMode.HTML)
        await run_animation(m)
        report = await execute_super_action(user_id, reason or "ɴᴏ ʀᴇᴀsᴏɴ", message.from_user.first_name, message.from_user.id, action="ban" if cmd == "superban" else "unban")
        
        formatted_report = format_text(report)
        await m.edit_text(formatted_report, parse_mode=ParseMode.HTML)
        for log_id in [LOGGER_ID, STORAGE_CHANNEL_ID]:
            try: await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
            except: pass
    else:
        global next_reason_id
        rid = next_reason_id
        reason_storage[rid] = reason or "ɴᴏ ʀᴇᴀsᴏɴ"
        next_reason_id += 1
        encoded_rid = base64.b64encode(str(rid).encode()).decode()

        req_text = format_text(f"🚨 {cmd.upper()} ʀᴇǫᴜᴇsᴛ\n\nᴜsᴇʀ: `{user_id}`\nʙʏ: {message.from_user.first_name}\nʀᴇᴀsᴏɴ: {reason_storage[rid]}")
        
        await app.send_message(
            SUPERBAN_CHAT_ID, req_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"sb_{cmd}_{user_id}_{encoded_rid}")]]),
            parse_mode=ParseMode.HTML
        )
        try: await app.send_message(LOGGER_ID, req_text, parse_mode=ParseMode.HTML)
        except: pass
        await message.reply_text(format_text("ʀᴇǫᴜᴇsᴛ sᴇɴᴛ ᴛᴏ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴀɴᴅ ʟᴏɢɢᴇᴅ."), parse_mode=ParseMode.HTML)

# --- 5. CALLBACK HANDLER ---

@app.on_callback_query(filters.regex(r'^sb_(superban|unsuperban)_(\d+)_(.+)$'))
async def on_approve_cb(_, query: CallbackQuery):
    if query.from_user.id not in SUDOERS and query.from_user.id not in AUTHORS:
        return await query.answer("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
    
    action, user_id, encoded_rid = query.matches[0].groups()
    rid = int(base64.b64decode(encoded_rid).decode())
    reason = reason_storage.get(rid, "ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ sᴜᴅᴏ")

    await query.message.edit_text(format_text("⚡ ᴀᴘᴘʀᴏᴠᴇᴅ. ᴇxᴇᴄᴜᴛɪɴɢ ᴘʀᴏᴛᴏᴄᴏʟ..."), parse_mode=ParseMode.HTML)
    report = await execute_super_action(int(user_id), reason, query.from_user.first_name, query.from_user.id, action="ban" if action == "superban" else "unban")
    
    formatted_report = format_text(report)
    await query.message.edit_text(formatted_report, parse_mode=ParseMode.HTML)
    
    for log_id in [LOGGER_ID, STORAGE_CHANNEL_ID]:
        try: await app.send_message(log_id, formatted_report, parse_mode=ParseMode.HTML)
        except: pass
        
