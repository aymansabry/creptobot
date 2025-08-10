# Telegram Arbitrage Bot (Multi-exchange)

**Important:** This project can run in DRY mode (no real trades) and LIVE mode (real trades).

## Quick start
1. Copy `.env.example` to `.env` and fill your real values (BOT_TOKEN, OWNER_ID, DATABASE_URL, FERNET_KEY, etc.).
2. Generate a Fernet key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. Create DB and run:
   ```bash
   python models_init.py
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start bot and web (or deploy to Railway with Procfile):
   ```bash
   # For local testing
   MODE=DRY python bot.py
   python web_app/app.py
   ```

## Security & Legal
- **Do NOT** paste real API keys into source code. Set them as environment variables or use Railway secrets.
- Running in LIVE will execute real orders and may lose money. Start with DRY and test thoroughly.
- Ensure compliance with local laws and exchange terms.
