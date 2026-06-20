from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'pingax_secure_key_2026'

def get_db():
    conn = sqlite3.connect('pingax_factory.db')
    conn.row_factory = sqlite3.Row
    return conn

def check_db_integrity():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT, product TEXT, qty TEXT, order_by TEXT,
            status TEXT DEFAULT 'Design', priority TEXT DEFAULT 'Normal'
        )
    """)
    new_cols = ["contact", "size", "gsm", "colour_type", "printing_side", "process", "order_date", "required_date", "remarks", "month_record"]
    for col in new_cols:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

check_db_integrity()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '1234':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    selected_month = request.args.get('month_filter', datetime.now().strftime("%Y-%m"))
    display_month = datetime.strptime(selected_month, "%Y-%m").strftime("%B %Y")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Dispatch', 'Completed')")
    active_prod = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Dispatch'")
    ready_dispatch = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'")
    dispatched = cursor.fetchone()[0]

    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if search_query:
        query += " AND (client LIKE ? OR product LIKE ? OR id LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    raw_orders = cursor.fetchall()
    
    orders = [dict(row) for row in raw_orders]
    
    cursor.execute("""
        SELECT order_by, COUNT(*) 
        FROM orders 
        WHERE order_by IS NOT NULL AND order_by != '' AND month_record = ? 
        GROUP BY order_by
    """, (selected_month,))
    staff_report = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT month_record FROM orders ORDER BY month_record DESC")
    available_months = [r[0] for r in cursor.fetchall() if r[0]]
    if selected_month not in available_months: available_months.append(selected_month)
    
    conn.close()
    return render_template('dashboard.html', orders=orders, staff_report=staff_report, 
                           current_month=display_month, selected_month=selected_month, 
                           available_months=sorted(available_months, reverse=True),
                           search_query=search_query, status_filter=status_filter,
                           total_orders=total_orders, active_prod=active_prod, 
                           ready_dispatch=ready_dispatch, dispatched=dispatched)

@app.route('/create-order', methods=['GET', 'POST'])
def create():
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (client, contact, product, size, qty, gsm, colour_type, printing_side, process, order_date, required_date, remarks, order_by, status, month_record) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (request.form.get('client'), request.form.get('contact'), request.form.get('product'), request.form.get('size'), request.form.get('qty'), request.form.get('gsm'), request.form.get('colour_type'), request.form.get('printing_side'), request.form.get('process'), request.form.get('order_date'), request.form.get('required_date'), request.form.get('remarks'), request.form.get('staff'), 'Design', datetime.now().strftime("%Y-%m")))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('create_order.html')

@app.route('/delete-order/<int:order_id>')
def delete_order(order_id):
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))
@app.route('/update', methods=['POST'])
def update():
    if 'user' not in session:
        return redirect(url_for('login'))

    order_id = request.form.get('id')
    new_status = request.form.get('status')
    new_priority = request.form.get('priority')

    conn = get_db()
    cursor = conn.cursor()

    if new_status:
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (new_status, order_id)
        )
    elif new_priority:
        cursor.execute(
            "UPDATE orders SET priority = ? WHERE id = ?",
            (new_priority, order_id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
    