# Screenshot → Obsidian Pipeline — Setup Guide

Complete setup takes about 20 minutes. Follow each step in order.

---

## What you'll set up

```
iPhone Photos
     ↓  (you forward screenshots to your bot)
Telegram Bot  ←── runs free on Railway
     ↓
Groq API  (free, vision AI)
     ↓
Private Telegram Channel
     ↓
Obsidian "Telegram Sync" plugin
     ↓
Obsidian Inbox folder → Obsidian Sync → all devices
```

---

## Step 1 — Create your Telegram Bot (5 min)

1. Open Telegram → search for **@BotFather**
2. Send `/newbot`
3. Give it a name: `My Screenshot Pipeline`
4. Give it a username: `myscreenshots_xyz_bot` (must be unique, end in _bot)
5. BotFather gives you a token like:
   ```
   7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. **Save this token** — this is your `TELEGRAM_BOT_TOKEN`

---

## Step 2 — Get your Telegram User ID (2 min)

You need this so only YOU can send screenshots to the bot.

1. Open Telegram → search for **@userinfobot**
2. Send `/start`
3. It replies with your ID like: `Id: 123456789`
4. **Save this number** — this is your `ALLOWED_USER_ID`

---

## Step 3 — Create a private Telegram Channel (3 min)

This channel is the relay between the bot and Obsidian.

1. In Telegram → tap the pencil icon → **New Channel**
2. Name it: `Obsidian Inbox`
3. Set it to **Private**
4. Skip adding subscribers

**Get the channel ID:**
1. Open Telegram Web (web.telegram.org)
2. Click your channel
3. Look at the URL: `https://web.telegram.org/k/#-1001234567890`
4. Your channel ID is the number including the minus sign: `-1001234567890`
5. **Save this** — this is your `OUTPUT_CHANNEL_ID`

**Add your bot to the channel:**
1. Open the channel → Settings → Administrators
2. Add administrator → search for your bot name
3. Give it permission to **Post Messages**

---

## Step 4 — Get Groq API Key (2 min)

1. Go to **console.groq.com**
2. Sign up (free, no credit card)
3. Go to API Keys → Create API Key
4. **Save the key** — this is your `GROQ_API_KEY`

---

## Step 5 — Deploy to Railway (5 min)

1. Go to **railway.app** → sign up with GitHub (free)
2. Click **New Project** → **Deploy from GitHub repo**
3. Upload this folder to a GitHub repo first:
   - Go to github.com → New repository → name it `screenshot-pipeline`
   - Upload `bot.py`, `requirements.txt`, `railway.toml`
4. Back in Railway → select your repo → Deploy

**Add environment variables in Railway:**

Click your service → Variables → Add these one by one:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | your bot token from Step 1 |
| `GROQ_API_KEY` | your Groq key from Step 4 |
| `ALLOWED_USER_ID` | your user ID from Step 2 |
| `OUTPUT_CHANNEL_ID` | your channel ID from Step 3 |

Railway redeploys automatically after you add variables.

**Verify it's running:**
- Go to your bot in Telegram
- Send `/start`
- Should reply with a welcome message

---

## Step 6 — Install Obsidian Telegram Sync plugin (5 min)

This plugin watches your private channel and pulls notes into Obsidian.

1. Open Obsidian → Settings → Community Plugins
2. Turn off Safe Mode → Browse
3. Search **"Telegram Sync"** → Install → Enable
4. Go to plugin settings:
   - **Bot Token**: paste your `TELEGRAM_BOT_TOKEN`
   - **Folder for new notes**: `Inbox` (or whatever your inbox folder is)
   - **Sync on startup**: ON
   - **Auto sync interval**: 5 minutes (or your preference)

> The plugin uses your bot token to read messages from the channel.
> Your bot must be an admin in the channel (done in Step 3).

---

## Step 7 — Test the full pipeline (2 min)

1. Open Telegram → find your bot
2. Send one screenshot from your camera roll
3. Bot replies "⚙️ Processing..."
4. Bot replies "✅ Done! Note pushed to Obsidian inbox"
5. Open Obsidian → check your Inbox folder
6. Your note should appear within 5 minutes (next sync cycle)

If it doesn't appear, open Obsidian → plugin icon → sync now.

---

## Daily usage

**Sending screenshots:**
1. Open iPhone Photos
2. Select screenshots you want to process (tap and hold to select multiple)
3. Share → Telegram → your bot
4. Done. Bot processes each one.

**Batch sending tip:**
- iOS lets you share up to 30 photos at once to Telegram
- Bot processes them sequentially, one note per screenshot
- Send `/done` when finished a batch to see count

**Creating a "To Process" album (optional but recommended):**
1. In iPhone Photos → Albums → + → New Album → "To Process"
2. Add screenshots to it as you take them
3. At end of day, select all → Share → your bot
4. Clean and habitual

---

## Processing the 3000 backlog

The bot handles this automatically but Groq free tier allows
14,400 requests/day. To process all 3000:

- Day 1: Send 500 screenshots (in batches of 30)
- Day 2: Send another 500
- Done in 6 days at zero cost

Or just process them at your own pace. No rush.

---

## What the notes look like in Obsidian

Each screenshot becomes a note like this:

```markdown
---
type: article
source: Twitter
date: 2025-04-27
tags: [machine-learning, transformers, AI]
---

# Attention Is All You Need — Key Points

## Content
The original text from the screenshot, cleanly formatted...

## Key Takeaways
- Transformers replaced RNNs for sequence modelling
- Self-attention allows parallel computation
- Positional encoding preserves sequence order

## My Notes
(you fill this in)
```

---

## Troubleshooting

**Bot not responding:**
- Check Railway logs (your project → Deployments → View Logs)
- Verify all 4 environment variables are set correctly

**Notes not appearing in Obsidian:**
- Open Obsidian → Telegram Sync plugin → tap sync manually
- Check the plugin settings — folder path must match exactly

**Groq rate limit error:**
- Free tier: 30 requests/minute
- If sending large batches, wait a minute between groups of 25

**Image too large:**
- Telegram compresses photos automatically — usually fine
- If sending as "file" (uncompressed), keep under 20MB

---

## Cost summary

| Service | Cost |
|---------|------|
| Telegram | Free |
| Railway | Free tier (500 hrs/month — plenty) |
| Groq API | Free (14,400 requests/day) |
| Obsidian Telegram Sync | Free |
| **Total** | **$0/month** |
