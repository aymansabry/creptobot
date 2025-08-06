#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python -m db.migrations.v1_initial

# Start the bot
python main.py
