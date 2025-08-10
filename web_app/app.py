from flask import Flask, request, redirect, render_template, session, url_for
from settings import SECRET_KEY, WEB_USERNAME, WEB_PASSWORD
from database import SessionLocal
from models import User, APIKey, TradeLog

app = Flask(__name__)
app.secret_key = SECRET_KEY

def auth_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login'))
    return wrapper

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == WEB_USERNAME and request.form['password'] == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return 'Bad creds', 401
    return render_template('login.html')

@app.route('/')
@auth_required
def index():
    db = SessionLocal()
    users = db.query(User).all()
    trades = db.query(TradeLog).order_by(TradeLog.created_at.desc()).limit(200).all()
    return render_template('index.html', users=users, trades=trades)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
