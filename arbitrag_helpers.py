from database import SessionLocal
from models import APIKey
from exchanges.ccxt_clients import CCXTClientFactory

def get_clients_for_user(user_id):
    db = SessionLocal()
    keys = db.query(APIKey).filter(APIKey.user_id==user_id, APIKey.is_active==True).all()
    clients = {}
    for k in keys:
        try:
            clients[k.exchange.lower()] = CCXTClientFactory.create(k.exchange, k.api_key_encrypted, k.api_secret_encrypted, k.passphrase_encrypted)
        except Exception as e:
            print('client init error', k.exchange, e)
    return clients
