from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

STATUS_STAGES = ["Design", "Printing", "Cutting", "Packing", "Ready Dispatch"]

ORDERS = [
    {"id": "PI-1001", "client": "ABC Hospital", "product": "X-Ray Bags", "qty": 5000, "delivery": "20-Jun", "status": "Printing"},
    {"id": "PI-1002", "client": "XYZ Clinic", "product": "Letter Pad", "qty": 2000, "delivery": "22-Jun", "status": "Packing"},
    {"id": "PI-1003", "client": "City Hospital", "product": "File Folders", "qty": 1000, "delivery": "25-Jun", "status": "Ready Dispatch"},
    {"id": "PI-1004", "client": "Apex Lab", "product": "Report Covers", "qty": 3000, "delivery": "26-Jun", "status": "Printing"},
    {"id": "PI-1005", "client": "Care Pharma", "product": "Medicine Boxes", "qty": 10000, "delivery": "28-Jun", "status": "Design"},
    {"id": "PI-1006", "client": "Lifeline Scan", "product": "Envelopes", "qty": 4000, "delivery": "29-Jun", "status": "Cutting"},
    {"id": "PI-1007", "client": "Metro Dental", "product": "Appointment Cards", "qty": 1500, "delivery": "30-Jun", "status": "Packing"},
    {"id": "PI-1008", "client": "Vision Opticals", "product": "Bill Books", "qty": 2000, "delivery": "02-Jul", "status": "Printing"},
    {"id": "PI-1009", "client": "Surat Medical", "product": "Prescription Pads", "qty": 5000, "delivery": "04-Jul", "status": "Ready Dispatch"},
    {"id": "PI-1010", "client": "Health First", "product": "Stickers", "qty": 12000, "delivery": "05-Jul", "status": "Design"}
]

@app.route('/')
def dashboard():
    return render_template('dashboard.html', orders=ORDERS, stages=STATUS_STAGES)

@app.route('/create-order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        new_id = f"PI-{1001 + len(ORDERS)}"
        new_job = {
            "id": new_id,
            "client": request.form.get('client'),
            "product": request.form.get('product'),
            "qty": int(request.form.get('qty', 0)),
            "delivery": request.form.get('delivery'),
            "status": "Design"
        }
        ORDERS.insert(0, new_job)
        return redirect(url_for('dashboard'))
    return render_template('create_order.html')

@app.route('/update-status', methods=['POST'])
def update_status():
    order_id = request.form.get('order_id')
    new_status = request.form.get('status')
    for order in ORDERS:
        if order['id'] == order_id:
            order['status'] = new_status
            break
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)