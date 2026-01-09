# ───────── IMPORTS ─────────
import asyncio
import random
import os
from typing import Dict, List

from pyrogram import filters
from pyrogram.types import Message

from Oneforall import app
from Oneforall.core.mongo import mongodb

# ───────── DATABASE ─────────
wordgame_db = mongodb.wordgame

# ───────── STATE ─────────
wordgame_status: Dict[int, bool] = {}
wordgame_data: Dict[int, dict] = {}
wordgame_tasks: Dict[int, asyncio.Task] = {}

# ───────── WORD LIST ─────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")

with open(FILE_PATH, "r") as f:
    WORDS = set(w.strip().lower() for w in f)

# ───────── DATABASE HELPERS ─────────
async def load_wordgame_status():
    async for doc in wordgame_db.find({}):
        wordgame_status[doc["chat_id"]] = doc["status"]

async def save_wordgame_status(chat_id: int, status: bool):
    await wordgame_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "status": status}},
        upsert=True
    )

async def get_wordgame_status(chat_id: int) -> bool:
    return wordgame_status.get(chat_id, False)

# ───────── /wordgame ─────────
@app.on_message(filters.command("wordgame") & filters.group)
async def wordgame_cmd(_, message: Message):
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) == 1:
        status = await get_wordgame_status(chat_id)
        return await message.reply(
            f"🎮 <b>Word Game:</b> <b>{status}</b>\n\n"
            "➤ <code>/wordgame on</code>\n"
            "➤ <code>/wordgame off</code>\n"
            "➤ <code>/wordmode 3-10</code>"
        )

    if args[1].lower() == "on":
        wordgame_status[chat_id] = True
        await save_wordgame_status(chat_id, True)
        await message.reply("✅ <b>Word Game Enabled</b>")

    elif args[1].lower() == "off":
        wordgame_status[chat_id] = False
        wordgame_data.pop(chat_id, None)
        if chat_id in wordgame_tasks:
            wordgame_tasks[chat_id].cancel()
        await save_wordgame_status(chat_id, False)
        await message.reply("🚫 <b>Word Game Disabled</b>")

# ───────── /wordmode ─────────
@app.on_message(filters.command("wordmode") & filters.group)
async def set_wordmode(_, message: Message):
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit():
        return await message.reply("Usage: <code>/wordmode 3-10</code>")

    mode = int(args[1])
    if not 3 <= mode <= 10:
        return await message.reply("Mode must be between 3 and 10")

    game = wordgame_data.setdefault(chat_id, {})
    game["mode"] = mode
    await message.reply(f"🔧 Word mode set to <b>{mode}</b>")

# ───────── /join ─────────
@app.on_message(filters.command("join") & filters.group)
async def join_game(_, message: Message):
    chat_id = message.chat.id
    if not await get_wordgame_status(chat_id):
        return

    game = wordgame_data.setdefault(chat_id, {
        "players": [],
        "turn": 0,
        "mode": 3,
        "last_letter": random.choice("abcdefghijklmnopqrstuvwxyz"),
        "active": False
    })

    if game["active"]:
        return await message.reply("❌ Game already started")

    if message.from_user.id in game["players"]:
        return await message.reply("Already joined")

    game["players"].append(message.from_user.id)
    await message.reply(f"✔ {message.from_user.mention} joined the game")

# ───────── /startgame ─────────
@app.on_message(filters.command("startgame") & filters.group)
async def start_game(_, message: Message):
    chat_id = message.chat.id
    game = wordgame_data.get(chat_id)

    if not game or len(game["players"]) < 2:
        return await message.reply("❌ Need at least 2 players")

    game["active"] = True
    game["turn"] = 0
    await announce_turn(message, chat_id)

# ───────── /stopgame ─────────
@app.on_message(filters.command("stopgame") & filters.group)
async def stop_game(_, message: Message):
    chat_id = message.chat.id
    wordgame_data.pop(chat_id, None)

    if chat_id in wordgame_tasks:
        wordgame_tasks[chat_id].cancel()

    await message.reply("🛑 Game stopped")

# ───────── TURN SYSTEM ─────────
async def announce_turn(message: Message, chat_id: int):
    game = wordgame_data[chat_id]
    uid = game["players"][game["turn"]]
    user = (await app.get_users(uid)).mention

    await message.reply(
        f"🎯 Turn: {user}\n"
        f"🔠 Start with: <b>{game['last_letter'].upper()}</b>\n"
        f"📏 Min letters: <b>{game['mode']}</b>\n"
        f"⏱ Time: 30s"
    )

    if chat_id in wordgame_tasks:
        wordgame_tasks[chat_id].cancel()

    wordgame_tasks[chat_id] = asyncio.create_task(turn_timeout(message, chat_id))

async def turn_timeout(message: Message, chat_id: int):
    await asyncio.sleep(30)
    game = wordgame_data.get(chat_id)
    if not game or not game["active"]:
        return

    kicked = game["players"].pop(game["turn"])
    user = (await app.get_users(kicked)).mention
    await message.reply(f"⌛ {user} ran out of time!")

    if len(game["players"]) == 1:
        winner = (await app.get_users(game["players"][0])).mention
        wordgame_data.pop(chat_id, None)
        return await message.reply(f"🏆 {winner} won the game!")

    game["turn"] %= len(game["players"])
    await announce_turn(message, chat_id)

# ───────── WORD INPUT ─────────
@app.on_message(filters.text & ~filters.command([]))
async def handle_word(_, message: Message):
    chat_id = message.chat.id
    game = wordgame_data.get(chat_id)

    if not game or not game["active"]:
        return

    if message.from_user.id != game["players"][game["turn"]]:
        return

    word = message.text.lower()

    if not word.startswith(game["last_letter"]):
        return await message.reply("❌ Wrong starting letter")

    if len(word) < game["mode"]:
        return await message.reply("❌ Word too short")

    if word not in WORDS:
        return await message.reply("❌ Invalid word")

    game["last_letter"] = word[-1]
    game["turn"] = (game["turn"] + 1) % len(game["players"])

    if chat_id in wordgame_tasks:
        wordgame_tasks[chat_id].cancel()

    await message.reply(f"✔ `{word}` accepted")
    await announce_turn(message, chat_id)

# ───────── INIT ─────────
async def initialize_wordgame():
    await load_wordgame_status()