"""
Screenshot → Obsidian Pipeline Bot
------------------------------------
Send screenshots to this bot via Telegram.
It extracts text using Groq vision, formats as
markdown, and sends to your private Telegram channel
which Obsidian Telegram Sync plugin pulls from.
"""

import os
import io
import base64
import asyncio
import httpx
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ── CONFIG (set these in Railway environment variables) ──
TELEGRAM_BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
GROQ_API_KEY         = os.environ["GROQ_API_KEY"]
ALLOWED_USER_ID      = int(os.environ["ALLOWED_USER_ID"])   # your Telegram user ID
OUTPUT_CHANNEL_ID    = os.environ["OUTPUT_CHANNEL_ID"]      # e.g. "-1001234567890"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "meta-llama/llama-4-scout-17b-16e-instruct"  # best free vision model on Groq


# ── SECURITY: only you can use this bot ──
def is_authorized(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER_ID


# ── GROQ VISION CALL ──
async def extract_and_format(image_bytes: bytes, caption: str = "") -> str:
    """
    Send image to Groq vision model.
    Returns formatted markdown note.
    """
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    system_prompt = """You are a personal knowledge assistant that processes screenshots into clean Obsidian notes.

Your job:
1. Extract ALL text visible in the screenshot accurately
2. Identify what type of content this is (article, tweet, recipe, code, quote, conversation, product, etc.)
3. Format it as a clean markdown note for Obsidian

Output format — always follow this structure exactly:

---
type: <content type>
source: <app or website if visible, else "unknown">
date: <today's date>
tags: [<2-4 relevant tags>]
---

# <A meaningful title you generate based on content>

## Content
<The extracted text, cleaned up and formatted nicely>

## Key Takeaways
<2-4 bullet points of the most important ideas — only if content is long enough to warrant it>

## My Notes
<leave this empty — user will fill it in>

Rules:
- Extract text faithfully, do not summarise or paraphrase the content itself
- Fix obvious OCR errors silently
- If image has no readable text, say so clearly
- Keep formatting clean for Obsidian markdown
- Do not add commentary outside the note structure"""

    user_content = [
        {
            "type":      "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_b64}"
            },
        }
    ]

    if caption:
        user_content.append({
            "type": "text",
            "text": f"Additional context from user: {caption}"
        })
    else:
        user_content.append({
            "type": "text",
            "text": "Process this screenshot into an Obsidian note following the format exactly."
        })

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":      GROQ_MODEL,
                "messages":   [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_content},
                ],
                "max_tokens":  1500,
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ── SEND TO OUTPUT CHANNEL ──
async def push_to_obsidian_channel(bot: Bot, markdown_note: str, filename: str):
    """
    Send the formatted note to your private Telegram channel.
    Obsidian Telegram Sync plugin watches this channel and
    pulls notes into your Obsidian inbox automatically.
    """
    # Telegram message limit is 4096 chars — split if needed
    max_len = 4000
    if len(markdown_note) <= max_len:
        await bot.send_message(
            chat_id    = OUTPUT_CHANNEL_ID,
            text       = markdown_note,
            parse_mode = "Markdown",
        )
    else:
        # Send in chunks
        chunks = [markdown_note[i:i+max_len] for i in range(0, len(markdown_note), max_len)]
        for i, chunk in enumerate(chunks):
            prefix = f"*[Part {i+1}/{len(chunks)}]* " if i > 0 else ""
            await bot.send_message(
                chat_id    = OUTPUT_CHANNEL_ID,
                text       = prefix + chunk,
                parse_mode = "Markdown",
            )
            await asyncio.sleep(0.5)


# ── HANDLERS ──

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 Screenshot pipeline ready!\n\n"
        "Send me screenshots and I'll:\n"
        "1. Extract all text using AI vision\n"
        "2. Format it as an Obsidian note\n"
        "3. Push it to your Obsidian inbox\n\n"
        "You can send multiple screenshots at once.\n"
        "Add a caption to give me extra context."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle single photo or photo in media group."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    # Acknowledge immediately
    processing_msg = await update.message.reply_text("⚙️ Processing screenshot...")

    try:
        # Get highest resolution version of photo
        photo    = update.message.photo[-1]
        caption  = update.message.caption or ""
        file     = await context.bot.get_file(photo.file_id)

        # Download image
        image_bytes = await file.download_as_bytearray()

        # Extract and format via Groq
        markdown_note = await extract_and_format(bytes(image_bytes), caption)

        # Push to Obsidian channel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"screenshot_{timestamp}.md"
        await push_to_obsidian_channel(context.bot, markdown_note, filename)

        # Confirm to user
        await processing_msg.edit_text(
            f"✅ Done! Note pushed to your Obsidian inbox.\n"
            f"📄 `{filename}`",
            parse_mode="Markdown"
        )

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text[:200] if e.response else str(e)
        await processing_msg.edit_text(
            f"❌ Groq API error: {e.response.status_code}\n`{error_detail}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)[:300]}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle screenshots sent as files (uncompressed)."""
    if not is_authorized(update):
        return

    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("Please send image files only.")
        return

    processing_msg = await update.message.reply_text("⚙️ Processing image file...")

    try:
        file        = await context.bot.get_file(doc.file_id)
        image_bytes = await file.download_as_bytearray()
        caption     = update.message.caption or ""

        markdown_note = await extract_and_format(bytes(image_bytes), caption)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"screenshot_{timestamp}.md"
        await push_to_obsidian_channel(context.bot, markdown_note, filename)

        await processing_msg.edit_text(
            f"✅ Done! Note pushed to Obsidian inbox.\n📄 `{filename}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)[:300]}")


async def handle_batch_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sends /done after a batch to get a summary."""
    if not is_authorized(update):
        return
    count = context.user_data.get("batch_count", 0)
    context.user_data["batch_count"] = 0
    await update.message.reply_text(
        f"📦 Batch complete. {count} notes pushed to your Obsidian inbox.\n"
        f"Open Obsidian on any device to see them."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "🟢 Bot is running\n"
        f"📡 Output channel: `{OUTPUT_CHANNEL_ID}`\n"
        f"🤖 Model: `{GROQ_MODEL}`",
        parse_mode="Markdown"
    )


# ── MAIN ──
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("done",   handle_batch_complete))
    app.add_handler(MessageHandler(filters.PHOTO,    handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    print("🚀 Screenshot pipeline bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
