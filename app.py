from flask import Flask, render_template, request, redirect, session, url_for
from db import get_db, init_db
import os
from datetime import date, timedelta

app = Flask(__name__)

@app.route('/')
def index():
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


# 🏠 Главное меню
@app.route('/menu')
def menu():
    return render_template('menu.html')

# 👥 Подопечные
@app.route('/clients')
def clients():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM clients ORDER BY id')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('clients/list.html', clients=clients)

@app.route('/clients/add_sessions/<int:client_id>', methods=['POST'])
def add_sessions(client_id):
    count = int(request.form['count'])
    conn = get_db()
    cur = conn.cursor()
    # Обновление, не позволяющее числу занятий уйти в минус
    cur.execute('''
        UPDATE clients
        SET sessions = CASE
            WHEN sessions + %s < 0 THEN 0
            ELSE sessions + %s
        END
        WHERE id = %s
    ''', (count, count, client_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/clients')

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        name = request.form['name'].strip()
        sessions = int(request.form['sessions'])

        conn = get_db()
        cur = conn.cursor()

        # Проверка: есть ли уже клиент с таким именем
        cur.execute('SELECT id FROM clients WHERE name = %s', (name,))
        exists = cur.fetchone()
        if exists:
            cur.close()
            conn.close()
            return redirect('/clients')  # или render_template с сообщением

        # Добавление нового клиента
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


@app.route('/appointments/choose')
def choose_date():
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(30)]

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.date, a.time, c.name, c.sessions, a.id
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    appointments = {}
    for row in rows:
        date_str = row[0].isoformat()
        if date_str not in appointments:
            appointments[date_str] = []
        appointments[date_str].append({
            'time': row[1].strftime('%H:%M'),
            'name': row[2],
            'sessions': row[3],
            'id': row[4],
        })

    return render_template('appointments/choose_date.html', dates=dates, appointments=appointments)

# 📝 Форма записи на дату
@app.route('/appointments/form')
def appointment_form():
    date_str = request.args.get('date')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM clients WHERE sessions > 0')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('appointments/form.html', clients=clients, date=date_str)

# ✅ Создание записи
@app.route('/appointments/create', methods=['POST'])
def create_appointment():
    client_id = request.form['client_id']
    date_str = request.form['date']
    time = request.form['time']

    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT 1 FROM appointments WHERE date = %s AND time = %s', (date_str, time))
    exists = cur.fetchone()
    if exists:
        cur.close()
        conn.close()
        return redirect(url_for('appointment_form', date=date_str, error='1'))

    cur.execute('UPDATE clients SET sessions = sessions - 1 WHERE id = %s AND sessions > 0', (client_id,))
    cur.execute('INSERT INTO appointments (client_id, date, time) VALUES (%s, %s, %s)', (client_id, date_str, time))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/appointments/choose')


# 🔁 Редирект если кто-то откроет /appointments/create через GET
@app.route('/appointments/create', methods=['GET'])
def redirect_from_create_get():
    return redirect('/appointments/choose')

# ❌ Отмена записи (минус)
@app.route('/appointments/delete/<int:appt_id>')
def delete_appt(appt_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT client_id FROM appointments WHERE id = %s', (appt_id,))
    client = cur.fetchone()
    if client:
        client_id = client[0]
        cur.execute('DELETE FROM appointments WHERE id = %s', (appt_id,))
        cur.execute('UPDATE clients SET sessions = sessions + 1 WHERE id = %s', (client_id,))
        conn.commit()
    cur.close()
    conn.close()
    return redirect('/appointments/choose')


# 🛠 Инициализация базы данных
@app.route('/init')
def init_db_route():
    init_db()
    return '✅ Таблицы созданы на Railway'

# 🚀 Запуск
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
