from flask import Flask, render_template, request, redirect, session
from db import get_db, init_db
import os
from datetime import date, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecret')

USERNAME = 'trainer'
PASSWORD = '1234'

@app.route('/appointments/calendar')
def calendar():
    return render_template('appointments/calendar.html')


@app.route('/appointments/create')
def choose_date():
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(30)]  # 30 дней вперёд
    return render_template('appointments/choose_date.html', dates=dates)

@app.before_request
def require_login():
    if request.endpoint not in ('login', 'static') and 'user' not in session:
        return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['user'] = USERNAME
            return redirect('/menu')
        return 'Неверный логин или пароль'
    return render_template('login.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

# Clients
@app.route('/clients')
def clients():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM clients')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('clients/list.html', clients=clients)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        sessions = int(request.form['sessions'])
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO clients (name, sessions) VALUES (%s, %s)', (name, sessions))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/clients')
    return render_template('clients/add.html')

@app.route('/clients/delete/<int:client_id>')
def delete_client(client_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM clients WHERE id = %s', (client_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/clients')

@app.route('/clients/add_sessions/<int:client_id>', methods=['POST'])
def add_sessions(client_id):
    count = int(request.form['count'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE clients SET sessions = sessions + %s WHERE id = %s', (count, client_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/clients')

# Appointments
@app.route('/appointments/create', methods=['GET', 'POST'])
def create_appointment():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        client_id = request.form['client_id']
        date = request.form['date']
        time = request.form['time']

        # Проверка на пересечение
        cur.execute('SELECT 1 FROM appointments WHERE date = %s AND time = %s', (date, time))
        exists = cur.fetchone()
        if exists:
            cur.close()
            conn.close()
            return '''
                    <h2>Время занято</h2>
                    <a href="/appointments/create">Назад</a>
                '''

        # Уменьшить количество занятий
        cur.execute('UPDATE clients SET sessions = sessions - 1 WHERE id = %s AND sessions > 0', (client_id,))
        cur.execute('INSERT INTO appointments (client_id, date, time) VALUES (%s, %s, %s)', (client_id, date, time))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/menu')

    cur.execute('SELECT * FROM clients WHERE sessions > 0')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('appointments/create.html', clients=clients)

@app.route('/appointments/delete', methods=['GET', 'POST'])
def delete_appointment():
    if request.method == 'POST':
        date = request.form['date']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            SELECT a.id, a.time, c.name FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.date = %s
            ORDER BY a.time
        ''', (date,))
        appointments = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('appointments/delete.html', appointments=appointments, date=date)

    return render_template('appointments/delete.html', appointments=None, date=None)

@app.route('/appointments/delete/<int:appt_id>')
def delete_appt(appt_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT client_id FROM appointments WHERE id = %s', (appt_id,))
    client_id = cur.fetchone()[0]
    cur.execute('DELETE FROM appointments WHERE id = %s', (appt_id,))
    cur.execute('UPDATE clients SET sessions = sessions + 1 WHERE id = %s', (client_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/menu')

@app.route('/appointments/list', methods=['GET', 'POST'])
def list_appointments():
    if request.method == 'POST':
        date = request.form['date']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            SELECT a.id, a.time, c.name FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.date = %s
            ORDER BY a.time
        ''', (date,))
        appointments = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('appointments/list.html', appointments=appointments, date=date)
    return render_template('appointments/list.html', appointments=None, date=None)

@app.route('/appointments/form')
def appointment_form():
    date = request.args.get('date')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM clients WHERE sessions > 0')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('appointments/form.html', clients=clients, date=date)


@app.route('/init')
def init_db_route():
    from db import init_db
    init_db()
    return '✅ Таблицы созданы на Railway'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
