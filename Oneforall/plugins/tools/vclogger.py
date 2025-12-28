from pyrogram import filters
from Oneforall import userbot
from Oneforall.vc_listener import VC_LOGGER

@userbot.one.on_message(filters.command("vclogger") & filters.group)
async def vclogger_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n/vclogger on\n/vclogger off"
        )

    chat_id = message.chat.id
    opt = message.command[1].lower()

    if opt == "on":
        VC_LOGGER.add(chat_id)
        await message.reply_text("✅ VC Logger Enabled")
    elif opt == "off":
        VC_LOGGER.discard(chat_id)
        await message.reply_text("❌ VC Logger Disabled")

@userbot.one.on_message(filters.command("vcstatus") & filters.group)
async def vcstatus_handler(client, message):
    status = message.chat.id in VC_LOGGER
    await message.reply_text(
        f"🎙️ VC Logger Status: {'ON' if status else 'OFF'}"
    )