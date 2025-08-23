botbot_final
============

Production-ready draft for an arbitrage bot with:
- MySQL (via SQLAlchemy + aiomysql)
- Telegram Arabic UI (reply keyboard)
- FastAPI backend for registration, settings, start/stop trading, reports
- Binance integration using ccxt (live/paper toggle)
- OpenAI integration hooks for market summaries

IMPORTANT SAFETY NOTES:
- Test with LIVE_MODE=false and testnet keys first.
- Ensure DATABASE_URL and TELEGRAM_BOT_TOKEN are set in environment.
- Review code and run in staging before using real funds.
