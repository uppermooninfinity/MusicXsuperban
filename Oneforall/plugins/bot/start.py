import time
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from config import BANNED_USERS
from Oneforall import app
from Oneforall.misc import _boot_, SUDOERS
from Oneforall.plugins.sudo.sudoers import sudoers_list
from Oneforall.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from Oneforall.utils.decorators.language import LanguageStart
from Oneforall.utils.formatters import get_readable_time
from Oneforall.utils.inline import help_pannel, private_panel, start_panel
from strings import get_string


# ================= PRIVATE START ================= #

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    await message.react("❤")

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = help_pannel(_)
            await message.reply_sticker(
                "CAACAgUAAxkBAAEQCTBpRKJI2Ne-52UqZaInTPq2H8X7sQACvRYAAqlp8VXvMdDN80vQvDYE"
            )
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            return

        if name.startswith("inf"):
            m = await message.reply_text("🔎")
            query = name.replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)

            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channel = result["channel"]["name"]
                channellink = result["channel"]["link"]
                link = result["link"]
                published = result["publishedTime"]

            text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )

            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ]
                ]
            )

            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=text,
                reply_markup=key,
            )
            return

    out = private_panel(_)
    await message.reply_sticker(
        "CAACAgUAAxkBAAEQCTBpRKJI2Ne-52UqZaInTPq2H8X7sQACvRYAAqlp8VXvMdDN80vQvDYE"
    )
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_2"].format(message.from_user.mention, app.mention),
        reply_markup=InlineKeyboardMarkup(out),
    )


# ================= GROUP START ================= #

@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    uptime = int(time.time() - _boot_)
    out = start_panel(_)
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
    )
    await add_served_chat(message.chat.id)


# ================= WELCOME HANDLER (FIXED) ================= #

welcome_group = 2

@app.on_message(filters.new_chat_members, group=welcome_group)
async def welcome(client, message: Message):
    try:
        for member in message.new_chat_members:

            # ✅ SAFE BUTTON (NO user_id)
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=member.first_name,
                            url=f"https://t.me/{member.username}"
                            if member.username else config.SUPPORT_CHAT
                        )
                    ]
                ]
            )

            if isinstance(config.OWNER_ID, int) and member.id == config.OWNER_ID:
                text = f"👑 **BOT OWNER JOINED**\n\n{member.mention}\nGroup: `{message.chat.title}`"
                msg = await message.reply_text(text, reply_markup=buttons)
                await asyncio.sleep(20)
                await msg.delete()
                return

            if isinstance(SUDOERS, (int, list, set)) and member.id in (SUDOERS if isinstance(SUDOERS, (list, set)) else [SUDOERS]):
                text = f"⚡ **SUDO USER JOINED**\n\n{member.mention}\nGroup: `{message.chat.title}`"
                msg = await message.reply_text(text, reply_markup=buttons)
                await asyncio.sleep(20)
                await msg.delete()
                return

    except Exception as e:
        print(f"Welcome error: {e}")


# ================= BOT ADDED HANDLER ================= #

@app.on_message(filters.new_chat_members, group=-1)
async def bot_added(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await message.reply_photo(
                    photo=config.START_IMG_URL,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)