from pyrogram import filters
from Oneforall import userbot

VC_LOGGER = set()

# Invite / join service based logger (no raw updates)
@userbot.one.on_message(filters.video_chat_members_invited & filters.group)
async def vc_invited_handler(client, message):
    chat_id = message.chat.id
    if chat_id not in VC_LOGGER:
        return

    invited_users = message.video_chat_members_invited.users
    for user in invited_users:
        await message.reply_text(
            f"""🤖 **ROOHI VC LOGGER**

#JoinVideoChat
👤 NAME : {user.first_name}
🆔 ID : `{user.id}`
🔗 USER : @{user.username if user.username else 'None'}
ACTION : IGNORED
"""
        )

# Optional: show when VC started
@userbot.one.on_message(filters.video_chat_started & filters.group)
async def vc_started_handler(client, message):
    chat_id = message.chat.id
    if chat_id not in VC_LOGGER:
        return

    await message.reply_text("🎧 **Video Chat Started**")