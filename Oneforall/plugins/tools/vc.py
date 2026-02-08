import logging
import uuid
import asyncio

from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired
from pyrogram.raw import base
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import (
    CreateGroupCall,
    DiscardGroupCall,
    ExportGroupCallInvite,
    GetGroupParticipants,
)
from pyrogram.types import Message

logging.basicConfig(level=logging.DEBUG)

async def delete_message_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    await message.delete()

@Client.on_message(filters.command("vcstart", prefixes=["."]) & filters.me)
async def startvc(client: Client, message: Message):
    call_name = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else "VC"
    original_message = message.reply_to_message or message
    
    try:
        await original_message.edit_text("Checking Voice Chat status...")

        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=await client.resolve_peer(message.chat.id))
        )
        call_id = full_chat.full_chat.call

        if call_id:
            await original_message.edit_text("**Voice Chat is already running**")
        else:
            await client.invoke(
                CreateGroupCall(
                    peer=await client.resolve_peer(message.chat.id),
                    random_id=int(str(uuid.uuid4().int)[:8]),
                    title=call_name
                )
            )
            await original_message.edit_text("Voice Chat started!")
        await delete_message_after_delay(original_message, 5)
    except Exception as e:
        logging.error("VCStart Error: %s", str(e))
        await original_message.edit_text(
            "**Please make me admin and give me Manage VC admin power**"
        )
        await delete_message_after_delay(original_message, 5)

@Client.on_message(filters.command("vcend", prefixes=["."]) & filters.me)
async def endvc(client: Client, message: Message):
    original_message = message.reply_to_message or message

    try:
        await original_message.edit_text("Ending Voice Chat...")

        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=await client.resolve_peer(message.chat.id))
        )
        call_id = full_chat.full_chat.call
        if call_id:
            await client.invoke(DiscardGroupCall(call=call_id))
            await original_message.edit_text("Voice Chat ended!")
        else:
            await original_message.edit_text("**No active VC to end**")
        await delete_message_after_delay(original_message, 5)
    except Exception as e:
        logging.error("VCEnd Error: %s", str(e))
        await original_message.edit_text(
            "**Please make me admin and give me Manage VC admin power**"
        )
        await delete_message_after_delay(original_message, 5)

@Client.on_message(filters.command("vclink", prefixes=["."]) & filters.me)
async def vclink(client: Client, message: Message):
    original_message = message.reply_to_message or message

    try:
        await original_message.edit_text("Getting Voice Chat link...")

        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=await client.resolve_peer(message.chat.id))
        )
        call_id = full_chat.full_chat.call
        if call_id:
            invite = await client.invoke(
                ExportGroupCallInvite(call=call_id)
            )
            await original_message.edit_text(f"Voice Chat Link: {invite.link}")
        else:
            await original_message.edit_text("**No active VC found**")
        await delete_message_after_delay(original_message, 5)
    except Exception as e:
        logging.error("VCLink Error: %s", str(e))
        await original_message.edit_text(str(e))
        await delete_message_after_delay(original_message, 5)

@Client.on_message(filters.command("vcmembers", prefixes=["."]) & filters.me)
async def vcmembers(client: Client, message: Message):
    original_message = message.reply_to_message or message

    try:
        await original_message.edit_text("Getting Voice Chat members...")

        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=await client.resolve_peer(message.chat.id))
        )
        call_id = full_chat.full_chat.call
        if call_id:
            participants = await client.invoke(
                GetGroupParticipants(
                    call=call_id,
                    ids=[],
                    sources=[],
                    offset="",
                    limit=1000
                )
            )
            count = participants.count
            text = f"Total Voice Chat Members: {count}\n"
            users = [participant.peer.user_id for participant in participants.participants]
            for user_id in users:
                user = await client.get_users(user_id)
                text += f"[{user.first_name + (' ' + user.last_name if user.last_name else '')}](tg://user?id={user.id})\n"
            await original_message.edit_text(text)
        else:
            await original_message.edit_text("**No active VC found**")
        await delete_message_after_delay(original_message, 5)
    except ChatAdminRequired:
        await original_message.edit_text(
            "Give me Manage VC power to use this command"
        )
        await delete_message_after_delay(original_message, 5)
    except Exception as e:
        logging.error("VCMembers Error: %s", str(e))
        await original_message.edit_text("Error retrieving VC members.")
        await delete_message_after_delay(original_message, 5)
