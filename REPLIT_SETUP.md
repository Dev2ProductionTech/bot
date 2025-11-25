# Replit Deployment Guide

## 🚀 Quick Setup

### 1. Import to Replit
1. Create a new Repl: https://replit.com/new
2. Choose "Import from GitHub" or upload this folder
3. Replit will auto-detect Python project

### 2. Configure Secrets
Go to the "Secrets" tab (🔒 icon) and add these environment variables:

```bash
# Required Secrets
SECRET_KEY=<generate-32-char-random-string>
TELEGRAM_BOT_TOKEN=<from-@BotFather>
TELEGRAM_WEBHOOK_SECRET=<generate-32-char-random-string>
TELEGRAM_WEBHOOK_URL=https://<your-repl-name>.<your-username>.repl.co/webhook/telegram
LONGCAT_API_KEY=<your-longcat-api-key>

# Optional (if using agent features)
AGENT_GROUP_CHAT_ID=-1001234567890
```

**Generate random secrets:**
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("WEBHOOK_SECRET:", secrets.token_urlsafe(32))
```

### 3. Get Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Set bot name: "Dev2Production Assistant"
5. Set description: "AI-powered bot for dev2production.tech"

### 4. Get LongCat API Key
1. Sign up at https://longcat.chat
2. Go to API settings
3. Generate new API key
4. Copy and add to Replit secrets

### 5. Enable PostgreSQL
1. In Replit, click on "Database" icon in left sidebar
2. Click "Enable PostgreSQL"
3. Replit will automatically set `DATABASE_URL` environment variable
4. No additional configuration needed!

### 6. Install Dependencies
Replit will auto-install from `requirements.txt`, but you can also run:
```bash
pip install -r requirements.txt
```

### 7. Run the Bot
Click the big green "Run" button! The bot will:
- Initialize the database tables
- Start FastAPI server on port 3000
- Be accessible at `https://<your-repl-name>.<your-username>.repl.co`

### 8. Set Webhook
After the bot is running, execute:
```bash
python scripts/set_webhook.py
```

Or use the Shell:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<your-repl-name>.<your-username>.repl.co/webhook/telegram",
    "secret_token": "<YOUR_WEBHOOK_SECRET>"
  }'
```

### 9. Test Your Bot
1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. You should see the welcome message with inline buttons!

## 📊 Monitoring on Replit

### Check Logs
View real-time logs in the Replit console

### Check Health
Visit: `https://<your-repl>.<username>.repl.co/health`

### Database Access
Use Replit's built-in database viewer in the sidebar

## 🔧 Replit-Specific Adjustments

### Why No Redis?
Replit free tier doesn't include Redis. We use:
- **In-memory caching** for session state
- **PostgreSQL** for persistent data
- **Simple rate limiting** without distributed cache

### Why No Docker?
Replit manages the container environment. The `.replit` file configures:
- Python 3.11 runtime
- Port 3000 (auto-mapped to HTTPS)
- Auto-install dependencies
- Auto-restart on file changes

### Free Tier Limits
- **Always-on:** Limited uptime (goes to sleep after inactivity)
- **CPU:** Shared resources
- **Memory:** 512MB RAM
- **Database:** PostgreSQL with storage limits
- **Bandwidth:** Rate limited

💡 **Tip:** Upgrade to Replit Core ($7/month) for:
- 24/7 uptime
- More resources
- Faster performance
- Custom domains

## 🐛 Troubleshooting

### Bot not responding?
1. Check if Repl is running (green dot)
2. Verify webhook: `python scripts/set_webhook.py`
3. Check logs for errors
4. Verify all secrets are set correctly

### Database errors?
1. Ensure PostgreSQL is enabled in Replit
2. Check `DATABASE_URL` is set automatically
3. Restart the Repl

### Webhook verification failed?
1. Ensure `TELEGRAM_WEBHOOK_URL` matches your Repl URL
2. Check `TELEGRAM_WEBHOOK_SECRET` is correct
3. Verify bot token is valid

## 📈 Next Steps

Once basic bot is working:
1. ✅ Add intent detection (Phase 2)
2. ✅ Integrate LongCat LLM (Phase 3)
3. ✅ Build project intake flow (Phase 2)
4. ✅ Add human escalation (Phase 4)
5. ✅ Implement file uploads (Phase 2)

---

Need help? Check:
- [Replit Docs](https://docs.replit.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [LongCat.chat Docs](https://docs.longcat.chat)
