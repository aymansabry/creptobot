#!/bin/bash

# تنصيب المتطلبات
pip install -r requirements.txt

# تنفيذ الهجرة
python -m db.migrations.v1_initial

# تشغيل البوت
python main.py
