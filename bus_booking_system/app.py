from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from threading import Lock

app = Flask(__name__)
app.secret_key = 'secret-key'
lock = Lock()

# Initialize SQLite Database
DATABASE = 'bus_booking.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create bus table
    c.execute('''CREATE TABLE IF NOT EXISTS buses
                 (id INTEGER PRIMARY KEY, name TEXT, total_seats INTEGER, current_occupancy INTEGER, route TEXT)''')
    # Create booking table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, bus_id INTEGER, seat_number INTEGER, user_id TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM buses')
    buses = c.fetchall()
    conn.close()
    return render_template('index.html', buses=buses)

@app.route('/add_bus', methods=['POST'])
def add_bus():
    name = request.form['name']
    total_seats = int(request.form['total_seats'])
    route = request.form['route']
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO buses (name, total_seats, current_occupancy, route) VALUES (?, ?, ?, ?)',
              (name, total_seats, 0, route))
    conn.commit()
    conn.close()
    
    flash('Bus added successfully!')
    return redirect(url_for('index'))

@app.route('/book_seat/<int:bus_id>', methods=['POST'])
def book_seat(bus_id):
    user_id = request.form['user_id']

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('SELECT * FROM buses WHERE id = ?', (bus_id,))
    bus = c.fetchone()
    
    if bus[3] < bus[2]:  # Check if current_occupancy is less than total_seats
        with lock:
            c.execute('SELECT MAX(seat_number) FROM bookings WHERE bus_id = ?', (bus_id,))
            last_seat = c.fetchone()[0]
            seat_number = (last_seat + 1) if last_seat else 1
            
            c.execute('INSERT INTO bookings (bus_id, seat_number, user_id) VALUES (?, ?, ?)',
                      (bus_id, seat_number, user_id))
            c.execute('UPDATE buses SET current_occupancy = current_occupancy + 1 WHERE id = ?', (bus_id,))
            conn.commit()
            conn.close()
            flash(f'Seat {seat_number} booked successfully for Bus {bus[1]}!')
    else:
        conn.close()
        flash('No seats available!')
    
    return redirect(url_for('index'))

@app.route('/cancel_seat/<int:bus_id>', methods=['POST'])
def cancel_seat(bus_id):
    seat_number = int(request.form['seat_number'])
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    with lock:
        c.execute('DELETE FROM bookings WHERE bus_id = ? AND seat_number = ?', (bus_id, seat_number))
        c.execute('UPDATE buses SET current_occupancy = current_occupancy - 1 WHERE id = ?', (bus_id,))
        conn.commit()
        conn.close()
        flash(f'Seat {seat_number} canceled successfully for Bus {bus_id}!')
    
    return redirect(url_for('index'))

@app.route('/bus/<int:bus_id>')
def bus_details(bus_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM buses WHERE id = ?', (bus_id,))
    bus = c.fetchone()
    c.execute('SELECT * FROM bookings WHERE bus_id = ?', (bus_id,))
    bookings = c.fetchall()
    conn.close()
    return render_template('bus_details.html', bus=bus, bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
