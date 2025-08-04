from setuptools import setup, find_packages

setup(
    name="crypto_bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==20.4',
        'ccxt==4.2.19',
        'sqlalchemy==2.0.19',
        'psycopg2-binary==2.9.7',
        'python-dotenv==1.0.0'
    ],
)
