# 🚀 Deploy to Replit - Complete Guide

## Step 1: Create Replit Account
1. Go to https://replit.com
2. Sign up (free account works!)
3. Verify your email

## Step 2: Upload Your Project to Replit

### Option A: Import from GitHub (Recommended)
1. Push your code to GitHub first:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/pythonBot.git
   git push -u origin main
   ```

2. In Replit:
   - Click **"Create Repl"**
   - Choose **"Import from GitHub"**
   - Paste your GitHub URL
   - Click **"Import from GitHub"**

### Option B: Upload Files Directly
1. In Replit, click **"Create Repl"**
2. Choose **"Python"** template
3. Name it: `dev2prod-bot`
4. Once created, you'll see the file explorer on the left
5. **Delete** the default `main.py` file
6. Click the **3 dots** (⋮) next to "Files"
7. Select **"Upload folder"**
8. Select your entire `pythonBot` folder
9. Wait for upload to complete

### Option C: Manual File Upload (If folder upload doesn't work)
1. Create Repl as above
2. For each file in your project:
   - Click **"+"** next to Files
   - Choose **"File"** or **"Folder"**
   - Copy-paste the content from your local files

## Step 3: Enable PostgreSQL Database
1. Look at the left sidebar in Replit
2. Click the **"Database"** icon (🗄️ cylinder shape)
3. Click **"Enable PostgreSQL"**
4. Wait ~30 seconds for it to provision
5. **IMPORTANT:** Replit automatically sets `DATABASE_URL` environment variable
6. You'll see connection details - no need to copy them, they're auto-configured!

## Step 4: Configure Environment Secrets
1. Click the **"Secrets"** icon (🔒 lock) in left sidebar (or Tools → Secrets)
2. Click **"Edit as JSON"** for easier bulk input
3. Paste this and replace with your values:

```json
{
  "SECRET_KEY": "your-random-32-character-secret-key-here",
  "TELEGRAM_BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "TELEGRAM_WEBHOOK_SECRET": "another-random-32-character-secret",
  "TELEGRAM_WEBHOOK_URL": "https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co/webhook/telegram",
  "LONGCAT_API_KEY": "your-longcat-api-key-here",
  "AGENT_GROUP_CHAT_ID": "-1001234567890"
}
```

4. Click **"Save"**

### How to Get Each Secret:

#### 🔑 SECRET_KEY & TELEGRAM_WEBHOOK_SECRET
Generate random secrets using Replit Shell:
```bash
python -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32)); print('WEBHOOK_SECRET:', secrets.token_urlsafe(32))"
```

#### 🤖 TELEGRAM_BOT_TOKEN
1. Open Telegram app
2. Search for `@BotFather`
3. Send: `/newbot`
4. Follow prompts:
   - Bot name: `Dev2Production Assistant`
   - Username: `dev2prod_bot` (must end with `_bot`)
5. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. **Optional settings:**
   ```
   /setdescription - Set description
   /setabouttext - Set about text
   /setcommands - Set commands list
   ```

#### 🌐 TELEGRAM_WEBHOOK_URL
1. In Replit, click **"Run"** button (▶️) at the top
2. Wait for it to start
3. Look at the top-right, you'll see a **"Webview"** open
4. Copy the URL from the webview (format: `https://REPL-NAME.USERNAME.repl.co`)
5. Add `/webhook/telegram` to the end
6. Example: `https://dev2prod-bot.johndoe.repl.co/webhook/telegram`

#### 🧠 LONGCAT_API_KEY
1. Go to https://longcat.chat
2. Sign up for free account
3. Navigate to **API Settings** or **Developer Console**
4. Click **"Generate API Key"**
5. Copy the key

#### 👥 AGENT_GROUP_CHAT_ID (Optional - skip for now)
This is for human escalation. To get it:
1. Create a Telegram group
2. Add your bot to the group
3. Send a message in the group
4. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Find `"chat":{"id":-1001234567890}` in the response
6. Copy the negative number

## Step 5: Install Dependencies
Replit should auto-install, but if not:

1. Open **Shell** tab (bottom of editor)
2. Run:
```bash
pip install -r requirements.txt
```

## Step 6: Run the Bot
1. Click the big green **"Run"** button (▶️) at the top
2. You should see logs like:
   ```
   INFO:     Starting application environment=production
   INFO:     Database initialized
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:3000
   ```
3. A webview will open showing your bot is running
4. Visit: `https://your-repl.repl.co/health` to verify

## Step 7: Set Telegram Webhook
### Method 1: Using the Script
In Replit Shell:
```bash
python scripts/set_webhook.py
```

You should see:
```
INFO: Setting webhook url=https://your-repl.repl.co/webhook/telegram
INFO: Webhook set successfully
```

### Method 2: Using curl (if script fails)
In Replit Shell, replace the placeholders:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-repl.your-username.repl.co/webhook/telegram",
    "secret_token": "<YOUR_WEBHOOK_SECRET>",
    "allowed_updates": ["message", "callback_query"]
  }'
```

### Verify Webhook:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Should return:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-repl.repl.co/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

## Step 8: Test Your Bot! 🎉
1. Open Telegram
2. Search for your bot username (e.g., `@dev2prod_bot`)
3. Click **"Start"** or send `/start`
4. You should see:
   ```
   👋 Welcome to Dev2Production!
   
   I'm your AI assistant for DevOps, Cloud Architecture,
   and Custom Software Development.
   
   How can I help you today?
   
   [4 buttons: 🚀 Start a Project | 💬 Ask Questions | etc.]
   ```

5. Try clicking buttons and sending messages!

## Step 9: Keep Bot Running 24/7

### Free Tier (Goes to sleep after inactivity):
- Bot sleeps after ~1 hour of no requests
- Wakes up when someone messages (2-3 second delay)
- Good for testing and low-traffic bots

### Always-On (Requires Replit Core - $7/month):
1. Click on your Repl name at the top
2. Go to **"Settings"**
3. Enable **"Always On"**
4. Your bot stays running 24/7 even with no traffic

### Free Alternative - External Ping:
Use a free service like UptimeRobot to ping your bot every 5 minutes:
1. Go to https://uptimerobot.com (free)
2. Add new monitor
3. URL: `https://your-repl.repl.co/health`
4. Interval: 5 minutes
5. This keeps your Repl awake during active hours

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Database connection failed"
1. Verify PostgreSQL is enabled (Database icon → should show connection info)
2. Check that `DATABASE_URL` appears in Secrets (Replit adds it automatically)
3. Restart the Repl

### "Webhook verification failed"
1. Ensure bot token is correct
2. Verify webhook URL matches your Repl URL exactly
3. Check webhook secret matches
4. Run `python scripts/set_webhook.py` again

### Bot not responding
1. Check Repl is running (green dot on "Run" button)
2. View Console logs for errors
3. Test health endpoint: `https://your-repl.repl.co/health`
4. Verify webhook is set: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

### "Port 3000 already in use"
- Replit automatically manages ports, ignore this
- The bot will still work on the public URL

### Logs not showing
- Click the **"Console"** tab at the bottom
- Should see real-time logs with timestamps

## 📊 Monitoring Your Bot

### View Logs
- **Console tab** (bottom): Real-time application logs
- Filter by log level (INFO, WARNING, ERROR)

### Check Database
- Click **Database** icon
- Use built-in SQL console to query tables:
  ```sql
  SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;
  SELECT * FROM messages ORDER BY created_at DESC LIMIT 20;
  ```

### Health Check
Visit: `https://your-repl.repl.co/health`
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### View API Docs (if DEBUG=true)
Visit: `https://your-repl.repl.co/docs`

## 🎯 Next Steps After Deployment

1. ✅ **Test basic functionality** - /start, /help commands
2. 🔄 **Add more features** from the task list:
   - Intent detection with FAQ responses
   - LongCat LLM integration
   - Project intake flow
3. 📊 **Monitor usage** - Check logs and database
4. 🔧 **Iterate** - Add features, fix bugs, improve responses

## 💡 Pro Tips

1. **Use Git:** Connect your Repl to GitHub for version control
   - Click "Version Control" icon in left sidebar
   - Connect GitHub account
   - Auto-sync on every save

2. **Environment-specific configs:**
   - Keep `.env.example` updated
   - Never commit actual secrets to GitHub
   - Use Replit Secrets for all sensitive data

3. **Monitor costs:**
   - LongCat API has usage limits
   - Set `LLM_DAILY_BUDGET_USD` to control spending
   - Monitor in Replit Console logs

4. **Backup database:**
   ```bash
   # In Replit Shell
   pg_dump $DATABASE_URL > backup.sql
   ```

5. **Test locally before deploying:**
   - Use `.env` file with local values
   - Run: `python src/main.py`
   - Use ngrok for local webhook testing

---

🎊 **Congratulations!** Your bot is now live on Replit!

Questions? Check:
- [Replit Docs](https://docs.replit.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- Your Console logs for debugging
