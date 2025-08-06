from setuptools import setup

setup(
    name="crypto_bot",
    version="1.0",
    install_requires=[
        line.strip() for line in open('requirements.txt') 
        if line.strip() and not line.startswith('#')
    ],
)
