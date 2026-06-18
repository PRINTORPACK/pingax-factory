from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def dashboard():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    selected_month = request.args.get('month_filter', datetime.now().strftime("%Y-%m"))
    display_month = datetime.strptime(selected_month, "%Y-%m").strftime("%B %Y")
    
    conn = get_db()
    cursor = conn.cursor()
    
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
    
    orders = []
    for row in raw_orders:
        o = dict(row)
        for key in ["client", "product", "qty", "order_by", "status", "priority", "contact", "size", "gsm", "colour_type", "printing_side", "process", "order_date", "required_date", "remarks", "month_record"]:
            if key not in o or o[key] is None: o[key] = ""
        if not o["status"]: o["status"] = "Design"
        if not o["priority"]: o["priority"] = "Normal"
        orders.append(o)
        
    cursor.execute("""
        SELECT order_by, COUNT(*) 
        FROM orders 
        WHERE order_by IS NOT NULL AND order_by != '' AND month_record = ? 
        GROUP BY order_by
    """, (selected_month,))
    report = cursor.fetchall()
    staff_report = [{"name": r[0], "count": r[1]} for r in report]
    
    cursor.execute("SELECT DISTINCT month_record FROM orders WHERE month_record IS NOT NULL AND month_record != '' ORDER BY month_record DESC")
    available_months = [r[0] for r in cursor.fetchall()]
    if selected_month not in available_months:
        available_months.append(selected_month)
    available_months = sorted(list(set(available_months)), reverse=True)
    
    conn.close()
    return render_template('dashboard.html', orders=orders, staff_report=staff_report, current_month=display_month, selected_month=selected_month, available_months=available_months, search_query=search_query, status_filter=status_filter)

@app.route('/create-order', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        current_m = datetime.now().strftime("%Y-%m")
        cursor.execute("""
            INSERT INTO orders (
                client, contact, product, size, qty, gsm, 
                colour_type, printing_side, process, order_date, 
                required_date, remarks, order_by, status, priority, month_record
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Design', 'Normal', ?)
        """, (
            request.form.get('client', ''), request.form.get('contact', ''), request.form.get('product', ''), 
            request.form.get('size', ''), request.form.get('qty', ''), request.form.get('gsm', ''), 
            request.form.get('colour_type', ''), request.form.get('printing_side', ''), request.form.get('process', ''), 
            request.form.get('order_date', ''), request.form.get('required_date', ''), request.form.get('remarks', ''), 
            request.form.get('staff', ''), current_m
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('create_order.html')

@app.route('/edit-order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute("""
            UPDATE orders SET 
                client=?, contact=?, product=?, size=?, qty=?, gsm=?, 
                colour_type=?, printing_side=?, process=?, order_date=?, 
                required_date=?, remarks=?, order_by=?
            WHERE id=?
        """, (
            request.form.get('client', ''), request.form.get('contact', ''), request.form.get('product', ''), 
            request.form.get('size', ''), request.form.get('qty', ''), request.form.get('gsm', ''), 
            request.form.get('colour_type', ''), request.form.get('printing_side', ''), request.form.get('process', ''), 
            request.form.get('order_date', ''), request.form.get('required_date', ''), request.form.get('remarks', ''), 
            request.form.get('staff', ''), order_id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return render_template('edit_order.html', o=order)

@app.route('/delete-order/<int:order_id>')
def delete_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/update', methods=['POST'])
def update():
    conn = get_db()
    cursor = conn.cursor()
    order_id = request.form.get('id')
    
    if 'status' in request.form:
        status_val = request.form.get('status')
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status_val, order_id))
    if 'priority' in request.form:
        priority_val = request.form.get('priority')
        cursor.execute("UPDATE orders SET priority = ? WHERE id = ?", (priority_val, order_id))
        
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)