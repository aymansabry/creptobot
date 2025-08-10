from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_default_secret")

@app.route('/')
def index():
    # مثال صفحة رئيسية
    return "لوحة تحكم المراجحة"

@app.route('/login', methods=['GET', 'POST'])
def login():
    # مثال صفحة تسجيل دخول
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == os.getenv("WEB_USERNAME") and password == os.getenv("WEB_PASSWORD"):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "فشل الدخول", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)