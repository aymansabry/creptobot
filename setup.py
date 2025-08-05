from setuptools import setup, find_packages

setup(
    name="arbitrage_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pydantic-settings>=2.0.3',
        'pydantic>=2.5.2',
        # باقي المتطلبات من requirements.txt
    ],
    python_requires=">=3.9",
)
