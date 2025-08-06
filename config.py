from decouple import config

class Config:
    # إعدادات أساسية
    BOT_TOKEN = config("BOT_TOKEN")
    
    # وضع النشر (webhook أو polling)
    DEPLOY_MODE = config("DEPLOY_MODE", default="polling")
    
    # إعدادات أخرى...
    # ...

config = Config()
