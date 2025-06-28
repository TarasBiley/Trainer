from flask import jsonify
from datetime import datetime, timedelta

@app.route('/appointments/load_more')
def load_more():
    offset = int(request.args.get('offset', 0))
    conn = get_db()
    cur = conn.cursor()

    days = []
    today = datetime.today().date()

    for i in range(offset, offset + 7):
        date = today + timedelta(days=i)
        cur.execute('''
            SELECT a.time, c.name FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.date = %s
            ORDER BY a.time
        ''', (date,))
        appointments = [{'time': a[0].strftime('%H:%M'), 'name': a[1]} for a in cur.fetchall()]
        days.append({
            'date': date.isoformat(),
            'display': date.strftime('%d.%m.%Y'),
            'appointments': appointments
        })

    cur.close()
    conn.close()
    return jsonify({'days': days})
