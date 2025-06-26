from flask import Flask, render_template, request, redirect, session
from db import get_db, init_db
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecret')

USERNAME = 'trainer'
PASSWORD = '1234'

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
    db = get_db()
    clients = db.execute('SELECT * FROM clients').fetchall()
    return render_template('clients/list.html', clients=clients)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        sessions = int(request.form['sessions'])
        db = get_db()
        db.execute('INSERT INTO clients (name, sessions) VALUES (?, ?)', (name, sessions))
        db.commit()
        return redirect('/clients')
    return render_template('clients/add.html')

@app.route('/clients/delete/<int:client_id>')
def delete_client(client_id):
    db = get_db()
    db.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    db.commit()
    return redirect('/clients')

@app.route('/clients/add_sessions/<int:client_id>', methods=['POST'])
def add_sessions(client_id):
    count = int(request.form['count'])
    db = get_db()
    db.execute('UPDATE clients SET sessions = sessions + ? WHERE id = ?', (count, client_id))
    db.commit()
    return redirect('/clients')

# Appointments
@app.route('/appointments/create', methods=['GET', 'POST'])
def create_appointment():
    db = get_db()
    if request.method == 'POST':
        client_id = request.form['client_id']
        date = request.form['date']
        time = request.form['time']

        # Проверка на пересечение
        exists = db.execute('SELECT 1 FROM appointments WHERE date = ? AND time = ?', (date, time)).fetchone()
        if exists:
            return '''
                    <h2>Время занято</h2>
                    <a href="/appointments/create">Назад</a>
                '''


        # Уменьшить количество занятий
        db.execute('UPDATE clients SET sessions = sessions - 1 WHERE id = ? AND sessions > 0', (client_id,))
        db.execute('INSERT INTO appointments (client_id, date, time) VALUES (?, ?, ?)', (client_id, date, time))
        db.commit()
        return redirect('/menu')

    clients = db.execute('SELECT * FROM clients WHERE sessions > 0').fetchall()
    return render_template('appointments/create.html', clients=clients)

@app.route('/appointments/delete', methods=['GET', 'POST'])
def delete_appointment():
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']
        appointments = db.execute('''
            SELECT a.id, a.time, c.name FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.date = ?
            ORDER BY a.time
        ''', (date,)).fetchall()
        return render_template('appointments/delete.html', appointments=appointments, date=date)

    return render_template('appointments/delete.html', appointments=None, date=None)

@app.route('/appointments/delete/<int:appt_id>')
def delete_appt(appt_id):
    db = get_db()
    client_id = db.execute('SELECT client_id FROM appointments WHERE id = ?', (appt_id,)).fetchone()['client_id']
    db.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
    db.execute('UPDATE clients SET sessions = sessions + 1 WHERE id = ?', (client_id,))
    db.commit()
    return redirect('/menu')

@app.route('/appointments/list', methods=['GET', 'POST'])
def list_appointments():
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']
        appointments = db.execute('''
            SELECT a.id, a.time, c.name FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.date = ?
            ORDER BY a.time
        ''', (date,)).fetchall()
        return render_template('appointments/list.html', appointments=appointments, date=date)
    return render_template('appointments/list.html', appointments=None, date=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


@app.route('/init')
def init_db_route():
    from db import init_db
    init_db()
    return '✅ Таблицы созданы на Railway'


