from Oneforall import app
from pyrogram import filters
import asyncio
import random
import os

# ======================
# WORD LIST LOADING
# ======================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")

with open(FILE_PATH, "r") as f:
    WORDS = set(w.strip().lower() for w in f)

# ======================
# GLOBAL DATA
# ======================

games = {}
start_timers = {}

# -------------------------------------------------------
# /join
# -------------------------------------------------------
@app.on_message(filters.command("join"))
async def join_game(_, message):
    chat_id = message.chat.id

    if chat_id not in games:
        games[chat_id] = {
            "players": [],
            "turn_index": 0,
            "mode": 3,
            "repeat": 0,
            "last_letter": random.choice("abcdefghijklmnopqrstuvwxyz"),
            "timeout_task": None,
            "active": False,
            "total_words": 0,
            "start_time": None,
            "longest_word": "",
            "initial_players": 0,
            "countdown": 60
        }

    game = games[chat_id]

    if game["active"]:
        return await message.reply("❌ Game already started, you cannot join now!")

    if message.from_user.id in game["players"]:
        return await message.reply("Already joined!")

    game["players"].append(message.from_user.id)
    await message.reply(f"✔ {message.from_user.mention} joined the game!")

    if chat_id not in start_timers:
        start_timers[chat_id] = asyncio.create_task(start_countdown(chat_id, message))

# ============================
# AUTO START + REMINDER SYSTEM
# ============================

async def start_countdown(chat_id, message):
    game = games[chat_id]
    game["max_time"] = 150

    while game["countdown"] > 0:
        if game["countdown"] in (30, 15):
            await message.reply(f"⏳ {game['countdown']} seconds left to join!")

        if game["countdown"] % 20 == 0:
            await message.reply(f"⌛ Game starting in {game['countdown']} seconds...")

        await asyncio.sleep(1)
        game["countdown"] -= 1

    if len(game["players"]) < 2:
        games.pop(chat_id, None)
        return await message.reply("❌ Not enough players. Game cancelled.")

    await message.reply("🎮 Auto-starting game...")
    await auto_start_game(message)

async def auto_start_game(message):
    chat_id = message.chat.id
    game = games[chat_id]

    game.update({
        "active": True,
        "turn_index": 0,
        "mode": 3,
        "repeat": 0,
        "total_words": 0,
        "last_letter": random.choice("abcdefghijklmnopqrstuvwxyz"),
        "initial_players": len(game["players"]),
        "start_time": asyncio.get_event_loop().time()
    })

    await message.reply(
        f"🎮 Word Game Started!\n"
        f"➡ First letter: **{game['last_letter']}**\n"
        f"➡ Minimum letters: **{game['mode']}**"
    )

    await next_turn(message)

# -------------------------------------------------------
# /stopgame
# -------------------------------------------------------
@app.on_message(filters.command("stopgame"))
async def stop_game(_, message):
    chat_id = message.chat.id

    if chat_id in games:
        if games[chat_id].get("timeout_task"):
            games[chat_id]["timeout_task"].cancel()
        games.pop(chat_id)

    await message.reply("🛑 Game stopped.")

# -------------------------------------------------------
# NEXT TURN
# -------------------------------------------------------
async def next_turn(message):
    chat_id = message.chat.id
    game = games[chat_id]

    current_id = game["players"][game["turn_index"]]
    current = (await app.get_chat_member(chat_id, current_id)).user.mention

    next_id = game["players"][(game["turn_index"] + 1) % len(game["players"])]
    next_user = (await app.get_chat_member(chat_id, next_id)).user.mention

    time_map = {3: 40, 4: 35, 5: 30, 6: 30, 7: 25, 8: 25, 9: 20, 10: 20}
    game["turn_time"] = time_map.get(game["mode"], 20)

    await message.reply(
        f"Turn: {current} ⭐\n"
        f"(Next: {next_user})\n"
        f"Start with **{game['last_letter'].upper()}**, "
        f"min **{game['mode']} letters**\n"
        f"⏱ {game['turn_time']} seconds"
    )

    if game.get("timeout_task"):
        game["timeout_task"].cancel()

    game["timeout_task"] = asyncio.create_task(timeout(message))

# -------------------------------------------------------
# WORD HANDLING
# -------------------------------------------------------
@app.on_message(filters.text & ~filters.command([]))
async def game_turn(_, message):
    chat_id = message.chat.id
    if chat_id not in games:
        return

    game = games[chat_id]
    if not game["active"]:
        return

    if message.from_user.id != game["players"][game["turn_index"]]:
        return

    word = message.text.lower()

    if not word.startswith(game["last_letter"]):
        return await message.reply("❌ Wrong starting letter!")

    if len(word) < game["mode"]:
        return await message.reply("❗ Word too short!")

    if word not in WORDS:
        return await message.reply("❗ Invalid word!")

    game["last_letter"] = word[-1]
    game["total_words"] += 1

    if len(word) > len(game["longest_word"]):
        game["longest_word"] = word

    await message.reply(f"✔ `{word}` accepted!")

    game["repeat"] += 1
    if game["repeat"] == 3 and game["mode"] < 10:
        game["repeat"] = 0
        game["mode"] += 1

    game["timeout_task"].cancel()
    game["turn_index"] = (game["turn_index"] + 1) % len(game["players"])
    await next_turn(message)