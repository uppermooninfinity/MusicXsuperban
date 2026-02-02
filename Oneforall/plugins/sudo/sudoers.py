from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import BANNED_USERS, OWNER_ID
from Oneforall import app
from Oneforall.misc import SUDOERS
from Oneforall.utils.database import add_sudo, remove_sudo
from Oneforall.utils.decorators.language import language
from Oneforall.utils.extraction import extract_user


@app.on_message(
    filters.command(["addsudo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"])
    & filters.user(OWNER_ID)
)
@language
async def useradd(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)
    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention))

    if await add_sudo(user.id):
        SUDOERS.add(user.id)
        await message.reply_text(_["sudo_2"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@app.on_message(
    filters.command(["delsudo", "rmsudo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"])
    & filters.user(OWNER_ID)
)
@language
async def userdel(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)
    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"].format(user.mention))

    if await remove_sudo(user.id):
        SUDOERS.remove(user.id)
        await message.reply_text(_["sudo_4"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@app.on_message(
    filters.command(["sudolist", "listsudo", "sudoers"])
    & ~BANNED_USERS
)
async def sudoers_list(client, message: Message):
    keyboard = [
        [InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="check_sudo_list")]
    ]
    await message.reply_video(
        video="https://files.catbox.moe/8qigce.mp4",
        caption="**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**\n\n**» ɴᴏᴛᴇ:**  ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀs ᴄᴀɴ ᴠɪᴇᴡ. ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex("^check_sudo_list$"))
async def check_sudo_list(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer(
            "Sudo list dekhne ka haq nahi 😏", show_alert=True
        )

    owner = await app.get_users(OWNER_ID)
    owner_name = owner.mention if owner else str(OWNER_ID)

    caption = f"**˹ʟɪsᴛ ᴏғ ʙᴏᴛ ᴍᴏᴅᴇʀᴀᴛᴏʀs˼**\n\n"
    caption += f"**🌹 Owner ➥** {owner_name}\n\n"

    count = 1
    for uid in SUDOERS:
        if uid != OWNER_ID:
            try:
                user = await app.get_users(uid)
                caption += f"**🎁 Sudo {count} ➥** {user.mention}\n"
                count += 1
            except:
                continue

    keyboard = [
        [InlineKeyboardButton("๏ ʙᴀᴄᴋ ๏", callback_data="back_to_main_menu")]
    ]

    await callback_query.message.edit_caption(
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex("^back_to_main_menu$"))
async def back_to_main_menu(client, callback_query: CallbackQuery):
    keyboard = [
        [InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="check_sudo_list")]
    ]
    await callback_query.message.edit_caption(
        caption="**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )