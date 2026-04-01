# Telegram Sticker Bot

A Telegram bot that lets users submit stickers, photos, and images for a community sticker pack. Admins review submissions through an approval queue before stickers are added to the pack.

## Features

- **User submissions** — Send a sticker, photo, PNG, WebP, or JPEG to submit it to the pack
- **Emoji selection** — Include an emoji in the caption to associate it with your sticker (defaults to 😊)
- **Admin approval queue** — Admins review, approve, or reject submissions via bot commands
- **Bulk approval** — Approve all pending submissions at once with `/approveall`
- **Duplicate detection** — Prevents the same file from being submitted twice
- **Rate limiting** — Max 3 submissions per user per hour
- **User blocking** — Admins can block abusive users
- **Notifications** — Users are notified when their submission is approved or rejected
- **Userbot integration** — Optional Telethon-based userbot for adding stickers via the Telegram API

## Prerequisites

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org) (for userbot features)

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/telegram_sticker_bot.git
   cd telegram_sticker_bot
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Copy the example file and fill in your values:

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |---|---|
   | `BOT_TOKEN` | Bot token from @BotFather |
   | `API_ID` | Telegram API ID from my.telegram.org |
   | `API_HASH` | Telegram API hash from my.telegram.org |
   | `ADMIN_IDS` | Comma-separated Telegram user IDs for admins |
   | `STICKER_PACK_NAME` | Short name of the sticker pack (from `t.me/addstickers/<name>`) |

4. **Authorize the userbot** (optional, for Telethon features)

   ```bash
   python auth_userbot.py
   ```

   This creates a session file in `storage/` so the userbot can act on your behalf.

5. **Run the bot**

   ```bash
   python main.py
   ```

## Commands

### User Commands

| Command | Description |
|---|---|
| `/start` | Show welcome message and usage instructions |
| *Send media* | Submit a sticker, photo, or image file to the queue |

### Admin Commands

| Command | Description |
|---|---|
| `/pending` | List all pending submissions |
| `/approve <id>` | Approve a submission and add it to the sticker pack |
| `/reject <id> [reason]` | Reject a submission with an optional reason |
| `/approveall` | Bulk approve all pending submissions |
| `/block <user_id>` | Block a user from submitting |
| `/stats` | Show submission statistics |
| `/packlink` | Get the sticker pack link |
| `/createpack` | Create the sticker pack (reply to an image/sticker to use as the first sticker) |

## Project Structure

```
telegram_sticker_bot/
├── main.py                 # Entry point — registers handlers and starts polling
├── auth_userbot.py         # Interactive script to authorize the Telethon userbot session
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── bot/
│   ├── handlers.py         # User-facing handlers (/start, media submissions)
│   ├── admin.py            # Admin command handlers (approve, reject, stats, etc.)
│   ├── queue_manager.py    # Submission queue with JSON-file persistence
│   └── userbot.py          # Telethon userbot client for sticker pack operations
├── config/
│   └── settings.py         # Loads .env and exposes configuration constants
└── storage/
    ├── submissions.json    # Submission queue data (auto-generated)
    └── user.session        # Telethon session file (auto-generated)
```

## Dependencies

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — Bot API framework
- [Telethon](https://github.com/LonamiWebs/Telethon) — Telegram userbot client
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Environment variable loading
- [emoji](https://github.com/carpedm20/emoji) — Emoji detection in captions
