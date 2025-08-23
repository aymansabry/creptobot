from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    port: int = int(os.getenv("PORT", 8080))
    timezone: str = os.getenv("TIMEZONE", "Africa/Cairo")
    live_mode: bool = os.getenv("LIVE_MODE", "false").lower() == "true"
    binance_testnet: bool = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    raw_db_url: str | None = os.getenv("DATABASE_URL")

    leg_notional_usdt: float = float(os.getenv("LEG_NOTIONAL_USDT", 10.0))
    max_concurrent_routes: int = int(os.getenv("MAX_CONCURRENT_ROUTES", 2))
    min_expected_profit_pct: float = float(os.getenv("MIN_EXPECTED_PROFIT_PCT", 0.45))
    max_slippage_pct: float = float(os.getenv("MAX_SLIPPAGE_PCT", 0.05))
    core_quotes: list[str] = os.getenv("CORE_QUOTES", "USDT,BTC,BNB,ETH").split(",")
    whitelist_alts: list[str] = [x for x in os.getenv("WHITELIST_ALTS", "").split(",") if x]
    max_invest_usd: float = float(os.getenv("MAX_INVEST_USD", 10000))

    bot_fee_pct: float = float(os.getenv("BOT_FEE_PCT", 0.0))
    bot_fee_withdraw_address: str | None = os.getenv("BOT_FEE_WITHDRAW_ADDRESS")
    bnb_min_reserve: float = float(os.getenv("BNB_MIN_RESERVE", 0.01))
    bnb_topup_usdt: float = float(os.getenv("BNB_TOPUP_USDT", 2.0))

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_ranking_enabled: bool = os.getenv("OPENAI_RANKING_ENABLED", "false").lower() == "true"

    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    def db_url(self) -> str:
        if not self.raw_db_url:
            return "mysql+aiomysql://arbuser:arbpass@127.0.0.1:3306/arbdb"
        return self.raw_db_url.replace("mysql://", "mysql+aiomysql://")

settings = Settings()
