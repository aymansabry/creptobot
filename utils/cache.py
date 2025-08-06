import redis
from core.config import Config

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD')
)

def cache_market_data(data: dict):
    redis_client.set('market_data', str(data), ex=60)  # تنتهي بعد 60 ثانية

def get_cached_data():
    return eval(redis_client.get('market_data')) if redis_client.exists('market_data') else None
