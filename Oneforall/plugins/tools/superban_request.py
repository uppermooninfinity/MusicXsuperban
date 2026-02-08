from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

@app.on_callback_query(filters.regex("request_superban"))
async def request_superban(_, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "<blockquote><i><u>✦ ʜᴇʏ 🥀\n\n<u><i></blockquote>"
        "<blockquote><i><u>⊚ ᴛᴀɢ ᴀ ᴜsᴇʀ ᴏʀ ɴsғᴡ sᴘᴀᴍᴍᴇʀ ᴏʀ ʀᴜʟᴇ ʙʀᴇᴀᴋᴇʀ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ\n</u></i></blockquote>"
        "<blockquote><i><u>➻ ᴛʜᴇɴ sᴇɴᴅ `/superban`\n\n</u></i></blockquote>"
        "<blockquote><i><u>❖ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴡɪʟʟ ʙᴇ ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ ᴜs ✅</u></i></blockquote>"
        "<blockquote><i><u>❖ to view superban logs join @docker_git_bit</u></i></blockquote>"
    )
