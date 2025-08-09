# web_app/app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database import query, execute, init_pool
from notifications import send_admin_alert

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET", "change-me")

@app.before_first_request
def setup():
    init_pool()

@app.route("/")
def index():
    users = query("SELECT id,username,role_id,is_active,invested_amount FROM users")
    trades = query("SELECT COUNT(*) as cnt FROM trades", fetchone=True)
    return render_template("index.html", users=users, trades=trades)

@app.route("/users")
def users_page():
    users = query("SELECT * FROM users")
    return render_template("users.html", users=users)

@app.route("/user/<int:user_id>/toggle")
def toggle_user(user_id):
    u = query("SELECT is_active FROM users WHERE id=%s", (user_id,), fetchone=True)
    if u:
        new = not bool(u['is_active'])
        execute("UPDATE users SET is_active=%s WHERE id=%s", (new, user_id))
    return redirect(url_for('users_page'))

@app.route("/settings", methods=['GET','POST'])
def settings():
    if request.method == 'POST':
        key = request.form['key']
        value = request.form['value']
        execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE setting_value=%s", (key, value, value))
        flash("Updated")
        return redirect(url_for('settings'))
    settings = query("SELECT setting_key,setting_value FROM settings")
    return render_template("settings.html", settings=settings)

@app.errorhandler(Exception)
def handle_error(e):
    send_admin_alert("WebApp Error", str(e))
    return "Internal error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
