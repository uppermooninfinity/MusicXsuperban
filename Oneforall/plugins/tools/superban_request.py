from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

@app.on_callback_query(filters.regex("request_superban"))
async def request_superban(_, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "✦ ʜᴇʏ 🥀\n\n"
        "⊚ ᴛᴀɢ ᴀ ᴜsᴇʀ ᴏʀ ɴsғᴡ sᴘᴀᴍᴍᴇʀ ᴏʀ ʀᴜʟᴇ ʙʀᴇᴀᴋᴇʀ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ\n"
        "➻ ᴛʜᴇɴ sᴇɴᴅ `/superban`\n\n"
        "❖ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴡɪʟʟ ʙᴇ ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ ᴜs ✅"
    )
