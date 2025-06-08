from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import sqlite3
from datetime import date, timedelta ,datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
DB_PATH = 'habits.db'
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=30)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_short_name(name):
    short_name = ""
    vowels = ["a","e","i","o","u"," ",",","."]
    for i in range(len(name)):
        if not name[i] in vowels and len(short_name) < 4:
            short_name = short_name + name[i].upper()
    while len(short_name) < 4:
        short_name = short_name + "X"
    return short_name


def createMissingHabitLogs(habits):
    db = get_db()
    today = date.today().strftime("%d.%m.%Y")

    for habit in habits:
        interval = db.execute('SELECT interval FROM habits WHERE id = ?', (habit["id"],)).fetchone()[0]
        if not interval:
            interval = 1
        existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=? AND date=?', (habit["id"], today)).fetchone()
        if not existing:
            db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (?, ?, 0, ?)', (habit["id"], today, habit["current_value"] * (1 - (0.01 / float(interval)))))
            db.execute('UPDATE habits SET current_value = current_value * (1 - (0.01 / ?)), change = (current_value * (100 - (1 / ?)) / initial_value) - 100 WHERE id = ?', (float(interval), float(interval), habit["id"]))
            db.commit()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    habits = db.execute('SELECT * FROM habits WHERE user_id = ?', (session["user_id"],)).fetchall()
    createMissingHabitLogs(habits)
    return render_template('index.html', habits=habits, username=session["username"], currency=session["currency"])


@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    if request.method == 'POST':
        if not request.form["username"]:
            return "Please enter a username"
        if not request.form["password"]:
            return "Please enter a password"
        if not request.form["currency"]:
            return "Please enter a currency"
        username = request.form['username']
        currency = request.form['currency']
        password = generate_password_hash(request.form['password'])
        try:
            db.execute("INSERT INTO users (username, password, currency) VALUES (?, ?, ?)", (username, password, currency))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already taken.", 400
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if 'user_id' in session:
        return redirect(url_for('start'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user[2], password):
            session.permanent = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['currency'] = user[3]
            return redirect("/")
        else:
            return "Invalid credentials.", 401
    return render_template('login.html')

# adds a new habit with the corresponding habit logs
@app.route('/add', methods=['POST'])
def add_habit():
    if not request.form["name"]:
        return "Please enter a name for the habit."
    if not request.form["initValue"] or int(request.form["initValue"]) < 0 or int(request.form["initValue"]) > 100:
        return "Please enter a number from 1 to 100."
    if not request.form["time"]:
        return "Please enter a time for the habit."
    if not request.form["identity"]:
        return "Please enter who you want to become."
    if not request.form["days"]:
        return "Please enter a time interval for the habit."
    name = request.form['name']
    init_value = int(request.form["initValue"])
    short_name = create_short_name(name)
    time = request.form["time"]
    identity = request.form["identity"]
    interval = int(request.form["days"])
    description = f"Every {interval} day/s, I'll complete this habit at {time} to become {identity}."
    db = get_db()
    # insert the new habit into the habits table
    db.execute('INSERT INTO habits (name, initial_value, current_value, user_id, short_name, change, description, interval) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (name, init_value, init_value * (1 - (0.01 / float(interval))), session["user_id"], short_name, -(1 / float(interval)), description, interval))
    # get the habit id
    habit_id = db.execute('SELECT id FROM habits WHERE short_name=?', (short_name,)).fetchone()
    habit_id = habit_id[0]
    # make the first habit log for the new habit using the habit_id and an initial log for the day before
    log_value = float(init_value) * (1 - (0.01 / interval))
    today = date.today().strftime("%d.%m.%Y")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%d.%m.%Y")
    db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (?, ?, 0, ?)', (habit_id, today, log_value))
    db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (?, ?, 1, ?)', (habit_id, yesterday, float(init_value)))
    # also create the habit logs for the prior days
    days_back = 2
    entry_found = True
    while entry_found:
        check_date = (datetime.today() - timedelta(days=days_back)).strftime("%d.%m.%Y")
        days_back += 1
        entry = db.execute("SELECT id FROM habit_logs WHERE date = ?", (check_date,)).fetchone()
        if entry:
            db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (?, ?, 1, ?)', (habit_id, check_date, float(init_value)))
        else:
            entry_found = False
    db.commit()
    return redirect('/')

# deletes a habit
@app.route('/delete/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
    db = get_db()
    db.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
    db.execute('DELETE FROM habit_logs WHERE habit_id = ?', (habit_id,))
    db.commit()
    return redirect('/')

# completes a habit and thus changes the prices
@app.route('/complete/<int:habit_id>', methods=['POST'])
def complete_habit(habit_id):
    db = get_db()
    today = date.today().strftime("%d.%m.%Y")
    interval = db.execute('SELECT interval FROM habits WHERE id = ?', (habit_id,)).fetchone()[0]
    if not interval:
        interval = 1
    # Checks if there is already a new entry for each day
    existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=? AND date=?', (habit_id, today)).fetchone()
    # if not, it adds the log
    if not existing:
        habits = db.execute('SELECT * FROM habits').fetchall()
        createMissingHabitLogs(habits)
    elif existing["completed"] != 1:
        db.execute('UPDATE habit_logs SET completed = 1, value = value / (1 - (0.01 / ?)) * 1.01 WHERE habit_id = ? AND date = ?', (float(interval), habit_id, today))
        db.execute('UPDATE habits SET current_value = current_value / (1 - (0.01 / ?)) * 1.01, change = (current_value * 101 / (1 - (0.01 / ?)) / initial_value) - 100 WHERE id = ?', (float(interval), float(interval), habit_id))
        db.commit()
    return redirect('/')

# completes a habit and thus changes the prices
@app.route('/yesterday/<int:habit_id>', methods=['POST'])
def complete_yesterday(habit_id):
    db = get_db()
    today = date.today().strftime("%d.%m.%Y")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%d.%m.%Y")
    interval = db.execute('SELECT interval FROM habits WHERE id = ?', (habit_id,)).fetchone()[0]
    if not interval:
        interval = 1
    # Checks if there is already a new entry for today
    today_existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=? AND date=?', (habit_id, today)).fetchone()
    # Checks the same for yesterday
    yesterday_existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=? AND date=?', (habit_id, yesterday)).fetchone()
    # check, whether we can add yesterday (condition: present and not done)
    if not yesterday_existing:
        return redirect("/")
    if yesterday_existing["completed"] == 1:
        return redirect("/")
    # if not today, it adds the log for today (and also yesterday)
    if not today_existing:
        habits = db.execute('SELECT * FROM habits').fetchall()
        createMissingHabitLogs(habits)
    else:
        # change for today
        db.execute('UPDATE habit_logs SET value = value / (1 - (0.01 / ?)) * 1.01 WHERE habit_id = ? AND date = ?', (float(interval), habit_id, today))
        # change the habit value
        db.execute('UPDATE habits SET current_value = current_value / (1 - (0.01 / ?)) * 1.01, change = (current_value * 101 / (1 - (0.01 / ?)) / initial_value) - 100 WHERE id = ?', (float(interval), float(interval), habit_id))
        # change the entry for yesterday
        db.execute('UPDATE habit_logs SET value = value / (1 - (0.01 / ?)) * 1.01, completed = 1 WHERE habit_id = ? AND date = ?', (float(interval), habit_id, yesterday))
        # db.execute('UPDATE habits SET current_value = current_value / (1 - (0.01 / ?)) * 1.01, change = (current_value * 101 / (1 - (0.01 / ?)) / initial_value) - 100 WHERE id = ?', (float(interval), float(interval), habit_id))
    db.commit()
    return redirect('/')

# misses a habit if you accidentally set it to done
@app.route('/miss/<int:habit_id>', methods=['POST'])
def miss_habit(habit_id):
    db = get_db()
    today = date.today().strftime("%d.%m.%Y")
    interval = db.execute('SELECT interval FROM habits WHERE id = ?', (habit_id,)).fetchone()[0]
    if not interval:
        interval = 1
    # Checks if there is already a new entry for each day
    existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=? AND date=?', (habit_id, today)).fetchone()
    # if not, it adds the log
    if not existing:
        habits = db.execute('SELECT * FROM habits').fetchall()
        createMissingHabitLogs(habits)
    elif existing["completed"] != 0:
        db.execute('UPDATE habit_logs SET completed = 0, value = value * (1 - (0.01 / ?)) / 1.01 WHERE habit_id = ? AND date = ?', (float(interval), habit_id, today))
        db.execute('UPDATE habits SET current_value = current_value * (1 - (0.01 / ?)) / 1.01, change = (current_value / 1.01 * (100 - (1 / ?)) / initial_value) - 100 WHERE id = ?', (float(interval), float(interval), habit_id,))
        db.commit()
    return redirect('/')

@app.route('/chart_data/<int:habit_id>')
def chart_data(habit_id):
    db = get_db()
    logs = db.execute('SELECT date, completed, value FROM habit_logs WHERE habit_id = ? ORDER BY date', (habit_id,)).fetchall()  
    data = []
    for log in logs:
        value = log["value"]
        data.append({'date': log['date'], 'value': round(value, 2)})

    return jsonify(data)


if __name__ == '__main__':
    app.run()