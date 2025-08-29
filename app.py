from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import sqlite3
from datetime import date, timedelta ,datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg
import math
from psycopg.rows import dict_row

# AI DISCLAIMER: I HAVE USED CHATGPT AS AN ASSISTANT DURING MY CODING PROCESS. IT HAS HELPED ME CREATE SOME OF THE SYNTAX AND LOGIC IN THIS DOCUMENT'S FUNCTIONS, WHEREAS THE STRUCTURE AND MOST OF THE CODE IS HAND-WRITTEN. PRESUMABLY 10-20% OF THIS DOCUMENT IS WRITTEN BY AI.

app = Flask(__name__)
DB_PATH = 'habits.db'
app.secret_key = os.environ.get('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=30)

# Configure session cookies for iframe embedding
app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True
)


def get_db():
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
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
    with get_db() as conn:
        with conn.cursor() as db:
            today = date.today().strftime("%Y-%m-%d")

            for habit in habits:
                row = db.execute('SELECT interval FROM habits WHERE id = %s', (habit["id"],)).fetchone()
                interval = row["interval"] if row else 1

                existing = db.execute('SELECT * FROM habit_logs WHERE habit_id = %s AND date = %s', (habit["id"], today)).fetchone()
                if not existing:
                    new_value = habit["current_value"] * (1 - (0.01 / float(interval)))
                    db.execute(
                        'INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (%s, %s, 0, %s)',
                        (habit["id"], today, new_value)
                    )
                    db.execute(
                        '''UPDATE habits 
                           SET current_value = current_value * (1 - (0.01 / %s)), 
                               change = (current_value * (100 - (1 / %s)) / initial_value) - 100 
                           WHERE id = %s''',
                        (float(interval), float(interval), habit["id"])
                    )
                    conn.commit()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        with conn.cursor() as db:
            today = date.today().strftime("%Y-%m-%d")
            # get logs (only needed for total habits)
            total_logs = db.execute('SELECT hl.date AS date, SUM(hl.value) AS total_value FROM habit_logs hl JOIN habits h ON hl.habit_id = h.id WHERE h.user_id = %s GROUP BY hl.date ORDER BY hl.date;', (session["user_id"],)).fetchall()
            habits = db.execute('SELECT h.*, hl.completed FROM habits h LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.date = %s WHERE user_id = %s', (today, session["user_id"])).fetchall()
            createMissingHabitLogs(habits)
            return render_template('index.html', habits=habits, username=session["username"], currency=session["currency"], logs = total_logs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    with get_db() as conn:
        with conn.cursor() as db:
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
                    db.execute("INSERT INTO users (username, password, currency) VALUES (%s, %s, %s)", (username, password, currency))
                    conn.commit()
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    return "Username already taken.", 400
            return render_template('register.html')

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    with get_db() as conn:
        with conn.cursor() as db:
            if 'user_id' in session:
                return redirect(url_for('start'))

            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                user = db.execute("SELECT * FROM users WHERE username = %s", (username,)).fetchone()

                if user and check_password_hash(user["password"], password):
                    session.permanent = True
                    session['user_id'] = user["id"]
                    session['username'] = user["username"]
                    session['currency'] = user["currency"]
                    return redirect("/")
                else:
                    return "Invalid credentials.", 401
            return render_template('login.html')


# adds a new habit with the corresponding habit logs
@app.route('/add', methods=['POST'])
def add_habit():
    if not request.form["name"]:
        return "Please enter a name for the habit."
    if not request.form["importance"] or int(request.form["importance"]) < 1 or int(request.form["importance"]) > 10:
        return "Please enter a level of importance from 1 to 10."
    if not request.form["difficulty"] or int(request.form["difficulty"]) < 1 or int(request.form["difficulty"]) > 10:
        return "Please enter a level of importance from 1 to 10."
    if not request.form["time"]:
        return "Please enter a time for the habit."
    if not request.form["identity"]:
        return "Please enter who you want to become."
    if not request.form["days"]:
        return "Please enter a time interval for the habit."
    name = request.form['name']
    short_name = create_short_name(name)
    time = request.form["time"]
    identity = request.form["identity"]
    interval = float(request.form["days"])
    init_value = int(request.form["importance"]) * int(request.form["difficulty"]) * (math.log(interval) + 1)
    description = f"Every {interval} day/s, I'll complete this habit when {time} to become {identity}."
    with get_db() as conn:
        with conn.cursor() as db:
            # insert the new habit into the habits table
            db.execute('INSERT INTO habits (name, initial_value, current_value, user_id, short_name, change, description, interval) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (name, init_value, init_value * (1 - (0.01 / float(interval))), session["user_id"], short_name, -(1 / float(interval)), description, interval))
            # get the habit id
            habit_id = db.execute('SELECT id FROM habits WHERE short_name=%s', (short_name,)).fetchone()
            habit_id = habit_id["id"]
            # make the first habit log for the new habit using the habit_id and an initial log for the day before
            log_value = float(init_value) * (1 - (0.01 / interval))
            today = date.today().strftime("%Y-%m-%d")
            yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (%s, %s, 0, %s)', (habit_id, today, log_value))
            db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (%s, %s, 1, %s)', (habit_id, yesterday, float(init_value)))
            # also create the habit logs for the prior days
            days_back = 2
            entry_found = True
            while entry_found:
                check_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
                days_back += 1
                entry = db.execute("SELECT id FROM habit_logs WHERE date = %s", (check_date,)).fetchone()
                if entry:
                    db.execute('INSERT INTO habit_logs (habit_id, date, completed, value) VALUES (%s, %s, 1, %s)', (habit_id, check_date, float(init_value)))
                else:
                    entry_found = False
            conn.commit()
            return redirect('/')


# deletes a habit
@app.route('/delete/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
     with get_db() as conn:
        with conn.cursor() as db:
            db.execute('DELETE FROM habit_logs WHERE habit_id = %s', (habit_id,))
            db.execute('DELETE FROM habits WHERE id = %s', (habit_id,))
            conn.commit()
            return redirect('/')

# completes a habit and thus changes the prices
@app.route('/complete/<int:habit_id>', methods=['POST'])
def complete_habit(habit_id):
    with get_db() as conn:
        with conn.cursor() as db:
            today = date.today().strftime("%Y-%m-%d")
            interval = db.execute('SELECT interval FROM habits WHERE id = %s', (habit_id,)).fetchone()
            if not interval:
                interval = 1
            else: interval = interval["interval"]
            # Checks if there is already a new entry for each day
            existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=%s AND date=%s', (habit_id, today)).fetchone()
            # if not, it adds the log
            if not existing:
                habits = db.execute('SELECT * FROM habits').fetchall()
                createMissingHabitLogs(habits)
            elif existing["completed"] != 1:
                db.execute('UPDATE habit_logs SET completed = 1, value = value / 0.99 * 1.01 WHERE habit_id = %s AND date = %s', (habit_id, today))
                db.execute('UPDATE habits SET current_value = current_value / 0.99 * 1.01, change = (current_value * 101 / 0.99 / initial_value) - 100 WHERE id = %s', (habit_id,))
                conn.commit()
            return redirect('/')


# completes a habit and thus changes the prices
@app.route('/yesterday/<int:habit_id>', methods=['POST'])
def complete_yesterday(habit_id):
    with get_db() as conn:
        with conn.cursor() as db:
            today = date.today().strftime("%Y-%m-%d")
            yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            interval = db.execute('SELECT interval FROM habits WHERE id = %s', (habit_id,)).fetchone()
            if not interval:
                interval = 1
            else: interval = interval["interval"]
            # Checks if there is already a new entry for today
            today_existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=%s AND date=%s', (habit_id, today)).fetchone()
            # Checks the same for yesterday
            yesterday_existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=%s AND date=%s', (habit_id, yesterday)).fetchone()
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
                db.execute('UPDATE habit_logs SET value = value / 0.99 * 1.01 WHERE habit_id = %s AND date = %s', (habit_id, today))
                # change the habit value
                db.execute('UPDATE habits SET current_value = current_value / 0.99 * 1.01, change = (current_value * 101 / 0.99 / initial_value) - 100 WHERE id = %s', (habit_id,))
                # change the entry for yesterday
                db.execute('UPDATE habit_logs SET value = value / 0.99 * 1.01, completed = 1 WHERE habit_id = %s AND date = %s', (habit_id, yesterday))
            conn.commit()
            return redirect('/')


# misses a habit if you accidentally set it to done
@app.route('/miss/<int:habit_id>', methods=['POST'])
def miss_habit(habit_id):
    with get_db() as conn:
        with conn.cursor() as db:
            today = date.today().strftime("%Y-%m-%d")
            interval = db.execute('SELECT interval FROM habits WHERE id = %s', (habit_id,)).fetchone()
            if not interval:
                interval = 1
            else: interval = interval["interval"]
            # Checks if there is already a new entry for each day
            existing = db.execute('SELECT * FROM habit_logs WHERE habit_id=%s AND date=%s', (habit_id, today)).fetchone()
            # if not, it adds the log
            if not existing:
                habits = db.execute('SELECT * FROM habits').fetchall()
                createMissingHabitLogs(habits)
            elif existing["completed"] != 0:
                db.execute('UPDATE habit_logs SET completed = 0, value = value * 0.99 / 1.01 WHERE habit_id = %s AND date = %s', (habit_id, today))
                db.execute('UPDATE habits SET current_value = current_value * 0.99 / 1.01, change = (current_value / 1.01 * 99 / initial_value) - 100 WHERE id = %s', (habit_id,))
                conn.commit()
            return redirect('/')


@app.route("/edit/<int:habit_id>", methods=["GET", "POST"])
def edit_habit(habit_id):
    with get_db() as conn:
        with conn.cursor() as db:
            habit = db.execute("SELECT * FROM habits WHERE id = %s", (habit_id,)).fetchone()

            if not habit or habit["user_id"] != session.get("user_id"):
                return "Habit not found or unauthorized", 403
            
            if request.method == "POST":
                if not request.form["name"]:
                    return "Please enter a name for the habit."
                if not request.form["initial_value"] or float(request.form["initial_value"]) < 0 or float(request.form["initial_value"]) > 1000:
                    return "Please enter a start value from 1 to 1000."
                if not request.form["description"]:
                    return "Please enter an actual description."
                if not request.form["short_name"]:
                    return "Please enter an actual short name."
                name = request.form['name']
                description = request.form["description"]
                new_initial_value = float(request.form["initial_value"])
                short_name = request.form["short_name"]
                # update habits
                db.execute("""
                    UPDATE habits
                    SET name = %s, description = %s, initial_value = %s, current_value = (current_value / initial_value * %s), short_name = %s
                    WHERE id = %s
                """, (name, description, new_initial_value, new_initial_value, short_name, habit_id))
                # update habit logs
                db.execute("""
                    UPDATE habit_logs
                    SET value = value / %s * %s
                    WHERE habit_id = %s
                """, (habit["initial_value"], new_initial_value, habit_id))
                conn.commit()
                return redirect('/')
    return render_template("edit.html", habit=habit)


if __name__ == '__main__':
    app.run()