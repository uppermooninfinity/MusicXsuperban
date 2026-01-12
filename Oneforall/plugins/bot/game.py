from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Oneforall import app
import re

# small caps map
SMALL_CAPS = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ",
    "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
    "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ",
    "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ",
    "z": "ᴢ"
})

def style_text(text: str) -> str:
    lines = text.split("\n")
    output = []

    for line in lines:
        # keep links and commands untouched
        if re.search(r"(https?://\S+|/\w+)", line):
            output.append("> " + line)
        else:
            output.append("> " + line.lower().translate(SMALL_CAPS))

    return "\n".join(output)

@app.on_callback_query(filters.regex("^games_menu$"))
async def games_menu(_, query):

    raw_text = (
        "🎮 Available Games\n\n"
        "✦ Word Chain – build words using last letter\n"
        "✦ use /join to start and auto-join by this command\n\n"
        "✦ every plugin developed here is minutely designed and well functioned\n"
        "✦ all credit goes to my developer 🥀 "
        "[✦ roohi ❕](https://t.me/roohi_queen_bot)"
    )

    text = style_text(raw_text)

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
            ]
        )
    )
